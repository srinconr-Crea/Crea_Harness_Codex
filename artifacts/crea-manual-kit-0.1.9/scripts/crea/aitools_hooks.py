"""Windows launcher and pure configuration proposals for advisory upstream hooks."""
import copy
import base64
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys
import tomllib

EVENTS = {'SessionStart': 'databricks-context.py', 'UserPromptSubmit': 'databricks-router.py', 'PostToolUse': 'databricks-auth-helper.py'}
REQUIRED = [*EVENTS.values(), '_routing_data.json', 'codex-hooks.json']


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def proposal(kit_root, interpreter=None):
    """Return JSON only; never writes native config or persists hook trust."""
    interpreter = str(interpreter or sys.executable)
    launcher = str(Path(kit_root) / 'scripts/crea/aitools.py')
    hooks = {}
    for event in EVENTS:
        windows = "& '" + interpreter.replace("'", "''") + "' '" + launcher.replace("'", "''") + "' hook --event " + event
        windows = 'powershell.exe -NoProfile -NonInteractive -EncodedCommand ' + base64.b64encode(windows.encode('utf-16le')).decode('ascii')
        command = shlex.quote(interpreter) + ' ' + shlex.quote(launcher) + ' hook --event ' + event
        group = {'hooks': [{'type': 'command', 'command': command, 'commandWindows': windows, 'timeout': 8}]}
        if event == 'SessionStart':
            group['matcher'] = 'startup|clear|compact'
        elif event == 'PostToolUse':
            group['matcher'] = '^Bash$'
        hooks[event] = [group]
    return {'hooks': hooks}


def merge_owned(previous, addition):
    """Pure merge for human-reviewed future activation; receipt owns exact groups."""
    merged = copy.deepcopy(previous)
    target = merged.setdefault('hooks', {})
    receipt = {'schema_version': 1, 'original_had_hooks': 'hooks' in previous, 'original_events': list(previous.get('hooks', {})), 'groups': []}
    for event, groups in addition['hooks'].items():
        existing = target.setdefault(event, [])
        for group in groups:
            if group in existing:
                raise ValueError('OWNED_HOOK_ALREADY_PRESENT')
            existing.append(copy.deepcopy(group))
            receipt['groups'].append({'event': event, 'sha256': fingerprint(group)})
    return merged, receipt


def restore_owned(current, receipt):
    """Remove only unchanged owned groups; any changed/missing owned group conflicts."""
    restored = copy.deepcopy(current)
    target = restored.get('hooks', {})
    for entry in receipt['groups']:
        groups = target.get(entry['event'], [])
        matches = [i for i, group in enumerate(groups) if fingerprint(group) == entry['sha256']]
        if len(matches) != 1:
            raise ValueError('HOOK_RESTORE_CONFLICT_PRESERVE_CLIENT_CHANGES')
        del groups[matches[0]]
        if not groups and entry['event'] not in receipt.get('original_events', []):
            del target[entry['event']]
    if not target and not receipt['original_had_hooks']:
        restored.pop('hooks', None)
    return restored


def inspect_hooks(kit_root, project_root):
    directory = Path(kit_root) / 'resources/databricks-aitools/hooks'
    missing = [name for name in REQUIRED if not (directory / name).is_file()]
    configured = False
    available = []
    for filename in ('hooks.json', 'config.toml'):
        try:
            content = (Path(project_root) / '.codex' / filename).read_text(encoding='utf-8-sig')
            config = json.loads(content) if filename.endswith('.json') else tomllib.loads(content)
            available.append(config.get('hooks', {}))
        except FileNotFoundError:
            continue
        except (OSError, ValueError, TypeError):
            configured = 'unknown'
    expected = proposal(kit_root)['hooks']
    def normalized(group):
        group = copy.deepcopy(group)
        for handler in group.get('hooks', []):
            if 'command_windows' in handler:
                handler['commandWindows'] = handler.pop('command_windows')
        return group
    try:
        if all(all(any(normalized(group) in [normalized(g) for g in config.get(event, [])] for config in available) for group in groups) for event, groups in expected.items()):
            configured = True
    except (AttributeError, TypeError):
        configured = 'unknown'
    return {'included': not missing, 'missing_resources': missing, 'configured': configured,
            'authorized': 'unknown', 'observed': 'not_run',
            'events': {event: {'included': name not in missing, 'observed': 'not_run'} for event, name in EVENTS.items()},
            'compatibility': {'codex_cli_reference': '0.167.0-alpha.3.2', 'project_hooks_documented': True,
                              'host_policy_and_trust': 'unknown', 'native_smoke': 'not_run'}}


def run_advisory(event, payload, kit_root, interpreter=None):
    """Forward stdin JSON via argv without shell; emit only advisory context fields."""
    try:
        if event not in EVENTS:
            return {}, 'unsupported_event'
        data = json.loads(payload)
        if not isinstance(data, dict) or data.get('hook_event_name', event) != event:
            return {}, 'invalid_payload'
        script = Path(kit_root) / 'resources/databricks-aitools/hooks' / EVENTS[event]
        # No login or CLI remote operation is dispatched by this launcher.
        result = subprocess.run([str(interpreter or sys.executable), str(script)], input=json.dumps(data),
                                capture_output=True, text=True, encoding='utf-8', timeout=6, shell=False)
        if result.returncode != 0:
            return {}, 'failed_open'
        raw = json.loads(result.stdout or '{}')
        specific = raw.get('hookSpecificOutput', {})
        context = specific.get('additionalContext')
        if not isinstance(context, str) or specific.get('hookEventName') != event:
            return {}, 'fixture_or_invocation_only'
        # Drop continue/decision/permission/tool rewrites. Upstream advice never grants scope.
        note = '\n[CREA] Advisory only. Preserve workflow gates, explicit skill selection and profile choice. Authentication/login requires separate authorization; plugin slash commands may be unavailable in this portable kit.'
        return {'hookSpecificOutput': {'hookEventName': event, 'additionalContext': context + note}}, 'fixture_or_invocation_only'
    except Exception:
        return {}, 'failed_open'


def windows_launcher_scripts(config):
    """Decoded bodies alongside proposal for review, outside the native config."""
    return {event: base64.b64decode(groups[0]['hooks'][0]['commandWindows'].rsplit(' ', 1)[-1]).decode('utf-16le')
            for event, groups in config['hooks'].items()}
