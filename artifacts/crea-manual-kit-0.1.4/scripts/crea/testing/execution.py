"""argv local revisado, sin shell; entorno mínimo y logs acotados/redactados."""
from datetime import datetime, timezone
import os
from pathlib import Path
import re
import subprocess
import threading

LIMIT = 65536


def utc():
    return datetime.now(timezone.utc).isoformat()


def redact(value):
    value = re.sub(r'(?i)\b(token|password|secret|api[_-]?key)\s*[=:]\s*\S+', r'\1=[REDACTED]', value)
    return re.sub(r'(?i)Bearer\s+\S+', 'Bearer [REDACTED]', value)


def run_process(root, argv, python_executable, timeout):
    executable = Path(python_executable or '')
    if not executable.is_absolute() or not executable.is_file() or not argv:
        raise ValueError('REVIEWED_INTERPRETER_REQUIRED')
    if argv[0] != 'python' and Path(argv[0]).resolve() != executable.resolve():
        raise ValueError('UNREVIEWED_EXECUTABLE')
    if type(timeout) is not int or timeout < 1 or any(not isinstance(x, str) or '\n' in x or '\r' in x or '\0' in x for x in argv):
        raise ValueError('INVALID_PROCESS_ARGUMENTS')
    command = [str(executable), *argv[1:]]
    env = {k: os.environ[k] for k in ('SystemRoot', 'WINDIR', 'COMSPEC', 'PATHEXT', 'TEMP', 'TMP') if k in os.environ}
    env.update({'PATH': str(executable.parent), 'PYTHONIOENCODING': 'utf-8',
                'PYTHONDONTWRITEBYTECODE': '1', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD': '1', 'PYTHONHASHSEED': '0'})
    streams = {}
    def drain(name, stream):
        kept, total = bytearray(), 0
        while True:
            chunk = stream.read(8192)
            if not chunk:
                break
            total += len(chunk)
            if len(kept) < LIMIT:
                kept.extend(chunk[:LIMIT-len(kept)])
        stream.close()
        streams[name] = (redact(kept.decode('utf-8', errors='replace')), total > LIMIT)
    started = utc()
    p = subprocess.Popen(command, cwd=Path(root).resolve(), env=env, shell=False,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         start_new_session=(os.name != 'nt'))
    threads = [threading.Thread(target=drain, args=(name, stream), daemon=True)
               for name, stream in [('stdout', p.stdout), ('stderr', p.stderr)]]
    for t in threads:
        t.start()
    timed_out = False
    try:
        p.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        if os.name == 'nt':
            subprocess.run([str(Path(os.environ.get('SystemRoot', '')) / 'System32/taskkill.exe'),
                            '/PID', str(p.pid), '/T', '/F'], capture_output=True, timeout=10)
        else:
            import signal
            os.killpg(p.pid, signal.SIGKILL)
        p.kill()
        p.wait(timeout=10)
    for t in threads:
        t.join(timeout=10)
    if any(t.is_alive() for t in threads):
        raise ValueError('PROCESS_OUTPUT_NOT_CLOSED')
    return {'argv': argv, 'exit_code': p.returncode, 'timed_out': timed_out,
            'started_at': started, 'finished_at': utc(),
            'stdout': streams['stdout'][0], 'stderr': streams['stderr'][0],
            'stdout_truncated': streams['stdout'][1], 'stderr_truncated': streams['stderr'][1]}
