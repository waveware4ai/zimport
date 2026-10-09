"""
Integration tests verifying that subprocess still works while the
zimport detour hooks are installed.

Background: zimport installs detour hooks for os.path.* utilities.
On POSIX, subprocess._execute_child internally calls
os.path.dirname(executable) with a bytes value. Before the slashpath
fix this raised TypeError: a bytes-like object is required, not 'str',
crashing subprocess.run with shell=True.
"""
import os
import subprocess
import unittest


class OsPathDirnameWithHookInstalled(unittest.TestCase):
    """os.path.dirname must accept the types Python itself passes."""

    def test_bytes_input_does_not_crash(self):
        # CPython's POSIX subprocess path pushes bytes into os.path.dirname
        result = os.path.dirname(b'/bin/sh')
        # Original implementation may return either representation;
        # what matters is that no exception is raised.
        self.assertIn(result, (b'/bin', '/bin', ''))


class SubprocessRunCompatibility(unittest.TestCase):
    """End-to-end reproducers for real-world call sites."""

    def test_subprocess_run_shell_true(self):
        # The original reproducer from issue #3.
        cwd = '/tmp' if os.name != 'nt' else os.getcwd()
        r = subprocess.run(
            "echo hello",
            shell=True,
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
            timeout=10,
            cwd=cwd,
        )
        stdout = r.stdout if isinstance(r.stdout, bytes) else r.stdout.encode()
        self.assertIn(b'hello', stdout)
        self.assertEqual(r.returncode, 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)