#!/usr/bin/env python3
"""Launch an isolated, no-key MobileHeal demo without opening native IDEs."""
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT / '.mobileheal' / 'demo-workspace'


def main():
    if sys.version_info < (3, 10):
        raise SystemExit('Use Python 3.10 or newer (Python 3.12 recommended).')
    if not shutil.which('git'):
        raise SystemExit('Install Git before starting the demo.')
    if not (WORKSPACE / '.git').exists():
        WORKSPACE.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(ROOT, WORKSPACE, dirs_exist_ok=True, ignore=shutil.ignore_patterns(
            '.git', '.mobileheal', '.venv', '__pycache__', '.pytest_cache', '*.db*',
            '*.log', '.env', '.env.*', '.DS_Store', '.gradle', 'build',
            'local.properties', 'google-services.json', '.superpowers'))
        gradle = WORKSPACE / 'android' / 'gradle.properties'
        if gradle.exists():
            content = gradle.read_text()
            if 'mobileheal.demo=true' not in content.splitlines():
                gradle.write_text(content.rstrip() + '\nmobileheal.demo=true\n')
        subprocess.run(['git', 'init', '-q', '-b', 'main'], cwd=WORKSPACE, check=True)
        subprocess.run(['git', 'add', '-A'], cwd=WORKSPACE, check=True)
        subprocess.run(['git', '-c', 'user.name=MobileHeal Demo', '-c',
                        'user.email=demo@mobileheal.local', 'commit', '-qm',
                        'Initialize isolated demo workspace'], cwd=WORKSPACE, check=True)
    env = dict(os.environ)
    # This launcher intentionally uses simulated integrations and no model credentials.
    for key in list(env):
        if key.endswith(('_API_KEY', '_TOKEN')) or key in ('GITHUB_REPO', 'GITLAB_REPO'):
            env.pop(key, None)
    env.update(MOBILEHEAL_DEMO='1', MOBILEHEAL_ROOT=str(WORKSPACE),
               MOBILEHEAL_SPEC=str(WORKSPACE / 'backend/requirements.txt'),
               MOBILEHEAL_DB=str(ROOT / 'backend/mobileheal-demo.db'),
               MOBILEHEAL_CRASHFEED='0')
    port = int(env.get('MOBILEHEAL_PORT', '8000'))
    print(f'MobileHeal demo: http://localhost:{port}/#new', flush=True)
    print(f'Isolated workspace: {WORKSPACE}', flush=True)
    try:
        subprocess.run([sys.executable, '-m', 'uvicorn', 'app.main:app', '--host',
                        '127.0.0.1', '--port', str(port)], cwd=ROOT / 'backend', env=env, check=True)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
