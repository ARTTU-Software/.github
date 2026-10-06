import subprocess
import sys
import unittest
from unittest.mock import patch
from helpers import Fixture, HOOKS
from mcp_launcher import launch_command


class PortableHelpers(Fixture):
    def test_bounded_reader_outputs_only_requested_lines(self):
        result = subprocess.run([sys.executable,str(HOOKS/'read_context.py'),str(self.large),
                                 '--start','101','--end','103'],text=True,capture_output=True,timeout=5)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.stdout.splitlines(),['101: int item;','102: int item;','103: int item;'])

    def test_bounded_reader_rejects_bulk_read(self):
        result = subprocess.run([sys.executable,str(HOOKS/'read_context.py'),str(self.large)],
                                text=True,capture_output=True,timeout=5)
        self.assertNotEqual(result.returncode,0)
        self.assertEqual(result.stdout,'')

    def test_windows_and_posix_npx_selection(self):
        with patch('mcp_launcher.shutil.which',return_value='C:/Program Files/nodejs/npx.cmd') as which:
            command, shell = launch_command('markdown-docs-mcp@0.1.5','win32')
            which.assert_called_once_with('npx.cmd')
            self.assertTrue(shell)
            self.assertEqual(command[-1],'markdown-docs-mcp@0.1.5')
        with patch('mcp_launcher.shutil.which',return_value='/usr/bin/npx') as which:
            _, shell = launch_command('codebase-memory-mcp@0.11.0','linux')
            which.assert_called_once_with('npx')
            self.assertFalse(shell)

    def test_mcp_launcher_rejects_unknown_package_and_missing_runtime(self):
        with self.assertRaises(ValueError):
            launch_command('unreviewed-package@latest')
        with patch('mcp_launcher.shutil.which',return_value=None):
            with self.assertRaises(FileNotFoundError):
                launch_command('markdown-docs-mcp@0.1.5')


if __name__ == '__main__':
    unittest.main()
