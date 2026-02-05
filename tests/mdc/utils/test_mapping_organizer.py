import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock, call
import sys

# Add project root to sys.path
sys.path.append(str(Path(__file__).parents[3]))

from mdc.utils.mapping_organizer import process_movie_dir, run_mode4

class TestMappingOrganizer(unittest.TestCase):
    def setUp(self):
        self.movie_dir = Path("/path/to/actor/movie_dir")
        self.nfo_path = self.movie_dir / "movie.nfo"
        
        self.mock_nfo = MagicMock(spec=Path)
        self.mock_nfo.read_text.return_value = "<movie></movie>"
        self.mock_nfo.write_text = MagicMock()
        
    @patch("mdc.utils.mapping_organizer.pick_main_nfo")
    @patch("mdc.utils.mapping_organizer.windows_long_path")
    def test_process_movie_dir_no_nfo(self, mock_wlp, mock_pick):
        mock_wlp.side_effect = lambda x: x
        mock_pick.return_value = None
        
        res = process_movie_dir(self.movie_dir)
        self.assertTrue(res["skipped"])
        self.assertEqual(res["reason"], "no_nfo")

    @patch("mdc.utils.mapping_organizer.pick_main_nfo")
    @patch("mdc.utils.mapping_organizer.windows_long_path")
    @patch("mdc.utils.mapping_organizer.get_actor_mapping")
    @patch("mdc.utils.mapping_organizer.get_info_mapping")
    @patch("mdc.utils.mapping_organizer.normalize_nfo_xml")
    def test_process_movie_dir_conflict(self, mock_norm, mock_info, mock_actor, mock_wlp, mock_pick):
        mock_wlp.side_effect = lambda x: x
        mock_pick.return_value = self.mock_nfo
        
        # Conflict
        mock_norm.return_value = (None, None, False, True)
        
        res = process_movie_dir(self.movie_dir)
        self.assertTrue(res["skipped"])
        self.assertEqual(res["reason"], "actor_mapping_conflict")

    @patch("mdc.utils.mapping_organizer.pick_main_nfo")
    @patch("mdc.utils.mapping_organizer.windows_long_path")
    @patch("mdc.utils.mapping_organizer.get_actor_mapping")
    @patch("mdc.utils.mapping_organizer.get_info_mapping")
    @patch("mdc.utils.mapping_organizer.normalize_nfo_xml")
    @patch("shutil.move")
    def test_process_movie_dir_move(self, mock_move, mock_norm, mock_info, mock_actor, mock_wlp, mock_pick):
        mock_wlp.side_effect = lambda x: x
        mock_pick.return_value = self.mock_nfo
        
        # Modified and New Actors
        mock_norm.return_value = ("<new></new>", ["NewActor"], True, False)
        
        # Mock pathlib operations
        # Since movie_dir is a real Path object in test, but we want to mock parent.name
        # It's easier to use a MagicMock for movie_dir if we rely on properties
        # But process_movie_dir calls windows_long_path(movie_dir) first.
        # Let's just use real Path objects and rely on logic.
        
        # /path/to/actor/movie_dir -> parent is 'actor'
        # new actor is 'NewActor' -> destination /path/to/NewActor/movie_dir
        
        with patch("pathlib.Path.mkdir"):
             res = process_movie_dir(self.movie_dir, dry_run=False)
        
        self.assertTrue(res["modified_nfo"])
        self.assertTrue(res["moved"])
        self.mock_nfo.write_text.assert_called_once()
        mock_move.assert_called_once()
        
    @patch("mdc.utils.mapping_organizer.iter_movie_dirs_with_nfo")
    @patch("mdc.utils.mapping_organizer.process_movie_dir")
    @patch("pathlib.Path.exists", return_value=True)
    def test_run_mode4(self, mock_exists, mock_process, mock_iter):
        mock_iter.return_value = [Path("d1"), Path("d2")]
        mock_process.side_effect = [
            {"movie_dir": "d1", "skipped": False, "modified_nfo": True, "moved": True, "dest_dir": "new_d1"},
            {"movie_dir": "d2", "skipped": True, "reason": "actor_mapping_conflict"}
        ]
        
        summary = run_mode4("root_path")
        
        self.assertEqual(summary["processed"], 2)
        self.assertEqual(summary["modified_nfo"], 1)
        self.assertEqual(summary["moved"], 1)
        self.assertEqual(summary["skipped"], 1)
        self.assertEqual(summary["conflicts"], 1)

if __name__ == '__main__':
    unittest.main()
