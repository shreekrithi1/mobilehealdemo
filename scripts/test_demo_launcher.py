"""Check isolation and the separate Android application flag without starting a server."""
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch, Mock

spec = importlib.util.spec_from_file_location('demo_launcher', Path(__file__).with_name('demo.py'))
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


class LauncherTest(unittest.TestCase):
    def test_isolation_android_flag_and_credential_free_process(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'backend').mkdir()
            (root / 'backend/requirements.txt').write_text('name: required\n')
            (root / 'android').mkdir()
            (root / 'android/gradle.properties').write_text('android.useAndroidX=true\n')
            (root / '.env').write_text('SAMPLE_SECRET=not-a-real-credential\n')
            (root / 'backend/private.db').write_text('runtime data')
            workspace = root / '.mobileheal/demo-workspace'
            invoked = []
            real_run = subprocess.run
            real_popen = subprocess.Popen
            def run(args, **kwargs):
                if 'uvicorn' in args:
                    invoked.append((args, kwargs))
                    return subprocess.CompletedProcess(args, 0)
                return real_run(args, **kwargs)
            with patch.object(launcher, 'ROOT', root), patch.object(launcher, 'WORKSPACE', workspace), \
                 patch.object(launcher.subprocess, 'run', side_effect=run), \
                 patch.object(launcher.subprocess, 'Popen', side_effect=lambda args, **kwargs: (invoked.append((args, kwargs)) or Mock(wait=Mock(return_value=0), poll=Mock(return_value=0))) if 'uvicorn' in args else real_popen(args, **kwargs)), \
                 patch.object(launcher.signal, 'signal'), \
                 patch.dict(os.environ, {'OPENAI_API_KEY':'fake-test-key','GITHUB_TOKEN':'fake-token','MOBILEHEAL_PORT':'8010'}):
                launcher.main()
            self.assertTrue((workspace / '.git').is_dir())
            self.assertFalse((workspace / '.env').exists())
            self.assertFalse((workspace / 'backend/private.db').exists())
            self.assertIn('mobileheal.demo=true', (workspace / 'android/gradle.properties').read_text())
            self.assertNotIn('mobileheal.demo', (root / 'android/gradle.properties').read_text())
            args, call = invoked[0]
            self.assertEqual(args[-1], '8010')
            self.assertEqual(call['env']['MOBILEHEAL_ROOT'], str(workspace))
            self.assertEqual(call['env']['MOBILEHEAL_DEMO'], '1')
            self.assertNotIn('OPENAI_API_KEY', call['env'])
            self.assertNotIn('GITHUB_TOKEN', call['env'])


if __name__ == '__main__':
    unittest.main()
