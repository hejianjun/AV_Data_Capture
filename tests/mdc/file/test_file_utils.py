import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Add project root to sys.path
sys.path.append(str(Path(__file__).parents[3]))

from mdc.file.file_utils import is_windows_path_too_long, iter_movie_dirs_with_nfo, pick_main_nfo


class TestFileUtils(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.root = Path(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_is_windows_path_too_long(self):
        with patch("os.name", "nt"):
            short_path = "c:\\short\\path"
            self.assertFalse(is_windows_path_too_long(Path(short_path)))

            long_path = "c:\\" + "a" * 260
            self.assertTrue(is_windows_path_too_long(Path(long_path)))

    def test_pick_main_nfo(self):
        # Create NFOs
        (self.root / "movie.nfo").touch()
        (self.root / "extra.nfo").touch()

        # Should return one of them. Since order is not guaranteed by FS usually,
        # but pick_main_nfo uses os.listdir or iterdir which is arbitrary but stable-ish.
        # Actually pick_main_nfo implementation:
        # for file in os.listdir(movie_dir): if file.endswith(".nfo"): return file
        # So it returns the first one found.

        nfo = pick_main_nfo(self.root)
        self.assertIsNotNone(nfo)
        self.assertTrue(nfo.name.endswith(".nfo"))

    def test_pick_main_nfo_none(self):
        nfo = pick_main_nfo(self.root)
        self.assertIsNone(nfo)

    def test_iter_movie_dirs_with_nfo(self):
        # Structure:
        # root/
        #   valid_movie/
        #     movie.nfo
        #     movie.mp4
        #   invalid_no_nfo/
        #     movie.mp4
        #   invalid_with_subdir/
        #     movie.nfo
        #     subdir/
        #   translated/ (ignored)
        #     some.nfo
        #   failed/ (ignored)
        #     some.nfo

        (self.root / "valid_movie").mkdir()
        (self.root / "valid_movie" / "movie.nfo").touch()

        (self.root / "invalid_no_nfo").mkdir()
        (self.root / "invalid_no_nfo" / "movie.mp4").touch()

        (self.root / "invalid_with_subdir").mkdir()
        (self.root / "invalid_with_subdir" / "movie.nfo").touch()
        (self.root / "invalid_with_subdir" / "subdir").mkdir()

        (self.root / "translated").mkdir()
        (self.root / "translated" / "some.nfo").touch()

        dirs = list(iter_movie_dirs_with_nfo(self.root))
        dir_names = [d.name for d in dirs]

        self.assertIn("valid_movie", dir_names)
        self.assertNotIn("invalid_no_nfo", dir_names)
        self.assertNotIn("invalid_with_subdir", dir_names)
        self.assertNotIn("translated", dir_names)


if __name__ == "__main__":
    unittest.main()
