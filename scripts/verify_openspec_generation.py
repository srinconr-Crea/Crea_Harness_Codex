"""Reproduce the pinned upstream kit in disposable, isolated Windows fixtures."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import uuid


def snapshot(roots):
    result = {}
    for root in roots:
        if root.exists():
            for path in root.rglob('*'):
                if path.is_file() and not path.is_symlink():
                    result[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def main():
    launcher = Path(shutil.which('openspec'))
    package = launcher.parent / 'node_modules/@fission-ai/openspec'
    assert json.loads((package / 'package.json').read_text())['version'] == '1.13.2'
    assert (package / 'LICENSE').read_text().startswith('MIT License')
    original = Path.home()
    roots = [original / '.codex/prompts', original / '.codex/skills', original / '.config/openspec',
             Path(os.environ['APPDATA']) / 'openspec',
             Path(os.environ['LOCALAPPDATA']) / 'openspec']
    for key in ('XDG_CONFIG_HOME', 'XDG_DATA_HOME'):
        if os.environ.get(key):
            roots.append(Path(os.environ[key]) / 'openspec')
    before = snapshot(roots)
    workspace = Path('.test-data') / ('openspec-generation-' + uuid.uuid4().hex)
    workspace.mkdir(parents=True)
    outputs = []
    logs = []
    for index in range(2):
        fixture = (workspace / str(index)).resolve()
        fixture.mkdir()
        isolated = fixture / 'home'
        config = fixture / 'xdg-config/openspec'
        config.mkdir(parents=True)
        config.joinpath('config.json').write_text(json.dumps(dict(
            profile='custom', delivery='skills', workflows=[
                'explore', 'propose', 'update', 'apply', 'verify', 'sync', 'archive'])))
        env = dict(os.environ)
        env.update(HOME=str(isolated), USERPROFILE=str(isolated),
                   CODEX_HOME=str(isolated / '.codex'),
                   APPDATA=str(fixture / 'appdata'), LOCALAPPDATA=str(fixture / 'localappdata'),
                   XDG_CONFIG_HOME=str(fixture / 'xdg-config'), XDG_DATA_HOME=str(fixture / 'xdg-data'),
                   OPENSPEC_TELEMETRY='0', DO_NOT_TRACK='1', OPENSPEC_NO_UPDATE_CHECK='1', CI='1')
        target = fixture / 'target'
        target.mkdir()
        command = [shutil.which('node'), str(package / 'bin/openspec.js'), 'init',
                   str(target), '--tools', 'codex', '--profile', 'custom', '--no-animation']
        completed = subprocess.run(command, env=env, capture_output=True, timeout=45)
        logs.append(dict(returncode=completed.returncode,
                         stdout=completed.stdout.decode('utf-8', errors='replace'),
                         stderr=completed.stderr.decode('utf-8', errors='replace')))
        assert completed.returncode == 0, logs[-1]
        outputs.append({str(p.relative_to(target)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in target.rglob('*') if p.is_file()})
    unchanged = before == snapshot(roots)
    evidence = dict(version='1.13.2', license='MIT', original_global_unchanged=unchanged,
                    reproducible=outputs[0] == outputs[1], files=outputs[0], runs=logs)
    (workspace / 'evidence.json').write_text(json.dumps(evidence, indent=2), encoding='utf-8')
    print(json.dumps(dict(workspace=str(workspace.resolve()), **evidence), indent=2))
    assert unchanged and evidence['reproducible']
    assert len([p for p in outputs[0] if p.endswith('/SKILL.md')]) == 7


if __name__ == '__main__':
    main()
