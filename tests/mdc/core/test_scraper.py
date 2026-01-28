import unittest
from unittest.mock import patch, MagicMock
from mdc.core.scraper import Scraping, get_data_from_json
import json

class TestScraper(unittest.TestCase):

    def tearDown(self):
        Scraping.searchGeneral.cache_clear()
        Scraping.searchAdult.cache_clear()

    @patch("mdc.core.scraper.load_cookies")
    @patch("mdc.core.scraper.file_modification_days")
    def test_load_cookies_for_source_valid(self, mock_days, mock_load):
        scraper = Scraping()
        
        # Mock valid cookie load
        mock_load.return_value = ({"cookie": "value"}, "path/to/cookie")
        # Mock valid modification days (< 7)
        mock_days.return_value = 5
        
        cookies = scraper.load_cookies_for_source("javdb", "javdb_site")
        
        self.assertEqual(cookies, {"cookie": "value"})
        mock_load.assert_called_with("javdb_site.json")
        
        # Check other source logic
        cookies = scraper.load_cookies_for_source("javlibrary", "javlibrary_site")
        mock_load.assert_called_with("javlibrary.json")

    @patch("mdc.core.scraper.load_cookies")
    @patch("mdc.core.scraper.file_modification_days")
    def test_load_cookies_for_source_expired(self, mock_days, mock_load):
        scraper = Scraping()
        
        mock_load.return_value = ({"cookie": "value"}, "path/to/cookie")
        # Mock expired modification days (>= 7)
        mock_days.return_value = 8
        
        cookies = scraper.load_cookies_for_source("javdb", "javdb_site")
        self.assertIsNone(cookies)

    @patch("mdc.core.scraper.load_cookies")
    def test_load_cookies_for_source_invalid_format(self, mock_load):
        scraper = Scraping()
        
        # Mock invalid cookie format (not a dict)
        mock_load.return_value = (None, "path/to/cookie")
        
        cookies = scraper.load_cookies_for_source("javdb", "javdb_site")
        self.assertIsNone(cookies)

    @patch.object(Scraping, "searchAdult")
    @patch.object(Scraping, "searchGeneral")
    @patch.object(Scraping, "load_cookies_for_source")
    def test_search_dispatch(self, mock_load_cookies, mock_general, mock_adult):
        scraper = Scraping()
        mock_load_cookies.return_value = {"key": "value"}
        
        # Test adult search dispatch
        scraper.search("ABC-123", sources=["javdb"], type="adult", dbsite="javdb_site")
        mock_adult.assert_called_once()
        mock_general.assert_not_called()
        self.assertEqual(scraper.dbcookies, {"javdb": {"key": "value"}})
        
        # Reset mocks
        mock_adult.reset_mock()
        mock_general.reset_mock()
        
        # Test general search dispatch
        scraper.search("Movie Title", sources=["tmdb"], type="general")
        mock_general.assert_called_once()
        mock_adult.assert_not_called()

    @patch("importlib.import_module")
    @patch("mdc.core.scraper.config")
    def test_searchGeneral_success(self, mock_config, mock_import):
        scraper = Scraping()
        
        # Mock config
        mock_config.getInstance.return_value.anonymous_fill.return_value = False
        
        # Setup mock parser
        mock_module = MagicMock()
        mock_parser_class = MagicMock()
        mock_parser_instance = MagicMock()
        
        mock_import.return_value = mock_module
        setattr(mock_module, "Tmdb", mock_parser_class)
        mock_parser_class.return_value = mock_parser_instance
        
        # Mock scrape return value
        expected_data = {"title": "Test Movie", "number": "123", "cover": "http://cover.jpg"}
        mock_parser_instance.scrape.return_value = json.dumps(expected_data)
        
        result = scraper.searchGeneral("Test Movie", ("tmdb",))
        
        self.assertEqual(result, expected_data)
        mock_import.assert_called_with(".tmdb", "mdc.scraping")

    @patch("importlib.import_module")
    def test_searchGeneral_404(self, mock_import):
        scraper = Scraping()
        
        mock_module = MagicMock()
        mock_parser_class = MagicMock()
        mock_parser_instance = MagicMock()
        
        mock_import.return_value = mock_module
        setattr(mock_module, "Tmdb", mock_parser_class)
        mock_parser_class.return_value = mock_parser_instance
        
        mock_parser_instance.scrape.return_value = 404
        
        result = scraper.searchGeneral("Test Movie", ("tmdb",))
        
        self.assertIsNone(result)

    def test_get_data_state(self):
        scraper = Scraping()
        
        # Valid data
        valid_data = {"title": "T", "number": "N", "cover": "C"}
        self.assertTrue(scraper.get_data_state(valid_data))
        
        # Missing title
        self.assertFalse(scraper.get_data_state({"number": "N", "cover": "C"}))
        self.assertFalse(scraper.get_data_state({"title": "", "number": "N", "cover": "C"}))
        
        # Missing number
        self.assertFalse(scraper.get_data_state({"title": "T", "cover": "C"}))
        self.assertFalse(scraper.get_data_state({"title": "T", "number": "", "cover": "C"}))
        
        # Missing cover (both cover and cover_small)
        self.assertFalse(scraper.get_data_state({"title": "T", "number": "N"}))
        
        # Has cover_small but no cover -> Valid
        self.assertTrue(scraper.get_data_state({"title": "T", "number": "N", "cover_small": "CS"}))

    @patch("mdc.core.scraper.config")
    @patch("mdc.core.scraper.search")
    @patch("mdc.core.scraper.get_actor_mapping")
    @patch("mdc.core.scraper.get_info_mapping")
    @patch("mdc.core.scraper.is_number_equivalent")
    @patch("mdc.core.scraper.process_text_mappings")
    @patch("mdc.core.scraper.process_special_actor_name")
    def test_get_data_from_json(self, mock_process_special, mock_process_text, mock_is_equiv, mock_info_map, mock_actor_map, mock_search, mock_config):
        # Setup config mock
        conf_instance = mock_config.getInstance.return_value
        conf_instance.cc_convert_mode.return_value = "s2t"
        conf_instance.sources.return_value = "javdb"
        conf_instance.proxy.return_value.enable = False
        conf_instance.javdb_sites.return_value = "77"
        conf_instance.cacert_file.return_value = None
        conf_instance.is_storyline.return_value = False
        conf_instance.debug.return_value = False
        conf_instance.naming_rule.return_value = "number+title"
        conf_instance.number_uppercase.return_value = True
        conf_instance.is_translate.return_value = False
        
        # Setup mapping mocks
        mock_process_text.side_effect = lambda text, mapping: text
        mock_process_special.side_effect = lambda name, mapping: name
        
        # Setup search mock
        mock_data = {
            "title": "Title",
            "number": "ABC-123",
            "actor": ["Actor1"],
            "director": "Director",
            "release": "2023-01-01",
            "studio": "Studio",
            "source": "javdb",
            "cover": "cover.jpg",
            "tag": ["tag1"]
        }
        mock_search.return_value = mock_data
        
        # Setup number equivalence
        mock_is_equiv.return_value = True
        
        result = get_data_from_json("ABC-123", None, None, None)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["title"], "Title")
        self.assertEqual(result["number"], "ABC-123")

if __name__ == '__main__':
    unittest.main()
