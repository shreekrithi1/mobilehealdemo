import os
import sys
import threading
import time
from pathlib import Path
import pytest
from app.harness_tools import ToolExecutor, ToolSpec, ToolPermissionError, resolve_allowed_path


def context(root, **extra):
    return dict(root=root, revision=1, commit='abc', permissions=['read'], demo_mode=True, **extra)


@pytest.mark.parametrize('name', ['../escape', '/tmp/file', '.git/config', '.env', 'credentials.json', 'docs/GUARDRAILS.md', 'app/harness_policy.py'])
def test_denied_paths(tmp_path, name):
    with pytest.raises(ToolPermissionError):
        resolve_allowed_path(tmp_path, name, ['**'])


def test_symlink_and_allowlist(tmp_path):
    (tmp_path / 'link').symlink_to('/tmp')
    with pytest.raises(ToolPermissionError):
        resolve_allowed_path(tmp_path, 'link/file', ['**'])
    with pytest.raises(ToolPermissionError):
        resolve_allowed_path(tmp_path, 'other.py', ['src/**'])
    assert resolve_allowed_path(tmp_path, 'src/main.py', ['src/**']) == tmp_path / 'src/main.py'


def spec(script, **kw):
    return ToolSpec(executable=sys.executable, build_argv=lambda a, c: ['-c', script], requires_isolation=False, **kw)


def test_unknown_injection_and_external_mutation(tmp_path):
    executor = ToolExecutor({'external': spec('pass', mutation=True, external=True)})
    for name, args in [('sh', {}), ('git_status', {'command': 'touch /tmp/pwned'}), ('external', {})]:
        with pytest.raises(ToolPermissionError):
            executor.execute(name, args, context(tmp_path))


def test_output_cap_redaction_and_receipt(tmp_path):
    executor = ToolExecutor({'test': spec("print('alice@example.com');print('x'*10000)", output_cap=128)})
    result = executor.execute('test', {}, context(tmp_path))
    assert result.status == 'passed'
    assert 'alice@example.com' not in result.summary
    assert len(result.summary) < 256
    assert 'truncated' in result.summary
    assert result.exit_code == 0 and result.duration_seconds >= 0


@pytest.mark.parametrize('cancel', [False, True])
def test_timeout_and_cancel_kill_process_group(tmp_path, cancel):
    pidfile = tmp_path / 'pid'
    heartbeat = tmp_path / 'heartbeat'
    child = f"import time; f=open({str(heartbeat)!r},'w')\nwhile True: f.write(chr(120)); f.flush(); time.sleep(0.02)"
    script = f"import subprocess,time; p=subprocess.Popen([{sys.executable!r},'-c',{child!r}]);open({str(pidfile)!r},'w').write(str(p.pid));time.sleep(30)"
    event = threading.Event()
    executor = ToolExecutor({'test': spec(script, timeout=0.3 if not cancel else 3)})
    if cancel:
        threading.Timer(0.2, event.set).start()
    result = executor.execute('test', {}, context(tmp_path, cancel_event=event))
    assert result.status == 'failed'
    assert ('cancelled' if cancel else 'timeout') in result.summary
    assert result.duration_seconds < 2
    assert int(pidfile.read_text()) > 0
    size = heartbeat.stat().st_size
    time.sleep(0.15)
    assert heartbeat.stat().st_size == size



def test_missing_executable_unavailable(tmp_path):
    executor = ToolExecutor({'missing': ToolSpec('/nonexistent/mobileheal', lambda a,c: [], requires_isolation=False)})
    assert executor.execute('missing', {}, context(tmp_path)).status == 'unavailable'


def test_shell_metacharacters_remain_literal(tmp_path):
    payload = '; touch marker; $(touch marker)'
    tool = ToolSpec(sys.executable, lambda a,c: ['-c', 'import sys;print(sys.argv[1])', a['text']], argument_names=frozenset({'text'}), requires_isolation=False)
    result = ToolExecutor({'echo': tool}).execute('echo', {'text': payload}, context(tmp_path))
    assert result.status == 'passed' and payload in result.summary
    assert not (tmp_path / 'marker').exists()


def test_missing_permission_and_mutation_authorization(tmp_path):
    tool = spec('pass', permission='write', mutation=True)
    executor = ToolExecutor({'write': tool})
    with pytest.raises(ToolPermissionError):
        executor.execute('write', {}, context(tmp_path))
    ctx = context(tmp_path)
    ctx['permissions'] = ['write']
    with pytest.raises(ToolPermissionError):
        executor.execute('write', {}, ctx)


def test_required_isolation_fails_closed_before_detached_child_launch(tmp_path):
    heartbeat = tmp_path / 'detached'
    script = f"import subprocess;subprocess.Popen([{sys.executable!r},'-c',\"open({str(heartbeat)!r},'w').write('started')\"],start_new_session=True)"
    tool = ToolSpec(sys.executable, lambda a,c: ['-c', script])
    result = ToolExecutor({'untrusted': tool}).execute('untrusted', {}, context(tmp_path))
    assert result.status == 'unavailable'
    assert 'isolation' in result.summary.lower()
    assert not heartbeat.exists()
