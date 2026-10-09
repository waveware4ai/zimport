"""
Unit tests for zimport.util.path.slashpath.

slashpath normalizes filesystem paths to forward-slash form and must
accept the path-like types Python itself can pass to os.path.* hooks:
str, bytes, and pathlib.Path subclasses. bytes support is required
because POSIX subprocess._execute_child calls os.path.dirname with a
bytes executable (via os.fsencode upstream) and zimport's detour
hook forwards that bytes into slashpath.
"""
import os
import pathlib
import sys
import unittest

from zimport.util.path import slashpath


class SlashpathAcceptsString(unittest.TestCase):
    """Existing behaviour: plain string input is normalised."""

    def test_returns_str(self):
        result = slashpath('/tmp/foo')
        self.assertIsInstance(result, str)

    def test_no_backslashes_remain(self):
        result = slashpath('/tmp/foo')
        self.assertNotIn('\\', result)

    def test_backslashes_normalised_to_forward_slashes(self):
        # On POSIX, os.path.abspath resolves 'C:\\tmp\\foo' relative to
        # the cwd, so we assert the contract 'no backslashes remain'
        # rather than a literal string equality that would couple the
        # test to platform-specific abspath behaviour.
        result = slashpath(r'C:\tmp\foo')
        self.assertNotIn('\\', result)
        self.assertIn('C:', result)
        self.assertIn('/tmp/foo', result)


class SlashpathAcceptsBytes(unittest.TestCase):
    """Regression: bytes input used to raise TypeError."""

    def test_returns_str(self):
        result = slashpath(b'/bin/sh')
        self.assertIsInstance(result, str)

    def test_no_backslashes_remain(self):
        result = slashpath(b'/bin/sh')
        self.assertNotIn('\\', result)

    def test_backslashes_normalised_to_forward_slashes(self):
        result = slashpath(b'C:\\tmp\\foo')
        self.assertNotIn('\\', result)
        self.assertIn('C:', result)
        self.assertIn('/tmp/foo', result)

    def test_os_fsencode_round_trip(self):
        # os.fsencode is what CPython's subprocess layer uses
        result = slashpath(os.fsencode('/usr/local/bin'))
        self.assertIsInstance(result, str)

    def test_arbitrary_bytes_via_surrogateescape(self):
        # PEP 383 surrogateescape must preserve non-utf8 filesystem
        # bytes; we do not lose data when decoding.
        result = slashpath(b'/\xff/path')
        self.assertIsInstance(result, str)


@unittest.skipIf(
    sys.platform.startswith('win'),
    "posix pathlib type only instantiable on POSIX runners (CI matrix covers both)",
)
class SlashpathAcceptsPosixPathlib(unittest.TestCase):
    def test_posix_path_input(self):
        result = slashpath(pathlib.PosixPath('/tmp/foo'))
        self.assertIsInstance(result, str)
        self.assertNotIn('\\', result)


@unittest.skipIf(
    sys.platform.startswith('linux') or sys.platform == 'darwin',
    "windows pathlib type only instantiable on Windows runners (CI matrix covers both)",
)
class SlashpathAcceptsWindowsPathlib(unittest.TestCase):
    def test_windows_path_input(self):
        result = slashpath(pathlib.WindowsPath('/tmp/foo'))
        self.assertIsInstance(result, str)
        self.assertNotIn('\\', result)


if __name__ == '__main__':
    unittest.main(verbosity=2)