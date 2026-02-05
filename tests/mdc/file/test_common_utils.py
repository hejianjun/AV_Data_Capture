import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import os
import sys

# Add project root to sys.path
sys.path.append(str(Path(__file__).parents[3]))

from mdc.file.common_utils import windows_long_path

class TestCommonUtils(unittest.TestCase):
    def test_windows_long_path_nt_short(self):
        with patch("os.name", "nt"):
            p = Path("c:/short/path")
            res = windows_long_path(p)
            self.assertEqual(res, p)

    def test_windows_long_path_nt_already_long(self):
        with patch("os.name", "nt"):
            # Using forward slashes for Path, but check logic usually handles string conversion
            p_str = "\\\\?\\c:\\long\\path"
            p = Path(p_str)
            res = windows_long_path(p)
            # Should return as is if starts with \\?\
            self.assertEqual(str(res), p_str)

    def test_windows_long_path_nt_make_long(self):
        with patch("os.name", "nt"):
            # Mock Path.exists to return True so it returns the long path
            with patch("pathlib.Path.exists", return_value=True):
                p = Path("c:\\some\\path")
                res = windows_long_path(p)
                self.assertTrue(str(res).startswith("\\\\?\\"))
                self.assertTrue(str(res).endswith("c:\\some\\path"))

    def test_windows_long_path_nt_make_long_not_exist(self):
        with patch("os.name", "nt"):
            # If long path doesn't exist, it might fallback or still return it depending on implementation.
            # Looking at code: return Path(lp) if Path(lp).exists() else path
            with patch("pathlib.Path.exists", return_value=False):
                p = Path("c:\\nonexistent\\path")
                res = windows_long_path(p)
                self.assertEqual(res, p)

    def test_windows_long_path_posix(self):
        # Instantiate Path before patching os.name to avoid pathlib confusion
        p = Path("c:/some/path")
        with patch("os.name", "posix"):
            res = windows_long_path(p)
            self.assertEqual(res, p)

if __name__ == '__main__':
    unittest.main()
