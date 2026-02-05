import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from mdc.file.movie_list import movie_lists
from mdc.config import config

class TestMovieList(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.source = Path(self.test_dir)
        
        # Create dummy structure
        # source/
        #   movie1.mp4
        #   movie2.avi
        #   ignored.txt
        #   movie-trailer.mp4
        #   subdir/
        #     movie3.mkv
        #   escaped/
        #     movie4.mp4
        
        (self.source / "movie1.mp4").touch()
        (self.source / "movie2.avi").touch()
        (self.source / "ignored.txt").touch()
        (self.source / "movie-trailer.mp4").touch()
        
        (self.source / "subdir").mkdir()
        (self.source / "subdir" / "movie3.mkv").touch()
        
        (self.source / "escaped").mkdir()
        (self.source / "escaped" / "movie4.mp4").touch()
        
        # Mock config
        self.config_mock = MagicMock()
        self.config_mock.main_mode.return_value = 1
        self.config_mock.debug.return_value = False
        self.config_mock.link_mode.return_value = False
        self.config_mock.media_type.return_value = ".mp4,.avi,.mkv"
        self.config_mock.failed_folder.return_value = self.test_dir
        self.config_mock.ignore_failed_list.return_value = True # Default to ignore failed list check
        self.config_mock.escape_folder.return_value = "escaped,hidden"
        
        # Patch config.getInstance
        self.patcher = patch('mdc.config.config.getInstance', return_value=self.config_mock)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        shutil.rmtree(self.test_dir)

    def test_movie_lists_basic(self):
        files = list(movie_lists(str(self.source), ""))
        filenames = [Path(f).name for f in files]
        
        self.assertIn("movie1.mp4", filenames)
        self.assertIn("movie2.avi", filenames)
        self.assertIn("movie3.mkv", filenames)
        self.assertNotIn("ignored.txt", filenames)
        self.assertNotIn("movie4.mp4", filenames) # Escaped
        self.assertNotIn("movie-trailer.mp4", filenames) # Trailer skipped

    def test_movie_lists_regex(self):
        files = list(movie_lists(str(self.source), "movie1"))
        filenames = [Path(f).name for f in files]
        self.assertIn("movie1.mp4", filenames)
        self.assertNotIn("movie2.avi", filenames)

    def test_movie_lists_failed_list(self):
        # Enable failed list check
        self.config_mock.ignore_failed_list.return_value = False
        self.config_mock.main_mode.return_value = 3 # Only checks failed list in mode 3 or link_mode
        
        failed_file = self.source / "failed_list.txt"
        failed_path = str((self.source / "movie1.mp4").resolve())
        failed_file.write_text(failed_path, encoding="utf-8")
        
        files = list(movie_lists(str(self.source), ""))
        filenames = [Path(f).name for f in files]
        
        self.assertNotIn("movie1.mp4", filenames)
        self.assertIn("movie2.avi", filenames)

if __name__ == '__main__':
    unittest.main()
