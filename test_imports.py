#!/usr/bin/env python3
"""
Comprehensive test script to verify all imports are working properly
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.abspath('.'))

def test_all_imports():
    """Test all imports from different modules"""
    print("Testing comprehensive imports...")
    
    # Test imports from different modules
    modules_to_test = [
        # Core modules
        "from mdc.core import core",
        "from mdc.core import scraper",
        "from mdc.core import metadata",
        
        # File modules
        "from mdc.file import file_utils",
        "from mdc.file import movie_list",
        
        # Download modules
        "from mdc.download import downloader",
        "from mdc.download.subtitles import download_subtitles",
        
        # Image modules
        "from mdc.image import imgproc",
        
        # Scraping modules
        "from mdc.scraping import api",
        "from mdc.scraping import javbus",
        
        # Utils modules
        "from mdc.utils import actor_mapping",
        "from mdc.utils import number_parser",
        "from mdc.utils import translation",
        "from mdc.utils.http import get_html",
        "from mdc.utils.download import parallel_download_files",
        "from mdc.utils.cookie import load_cookies",
        "from mdc.utils.string import cn_space",
        "from mdc.utils.html import get_xpath_single",
    ]
    
    for import_statement in modules_to_test:
        try:
            exec(import_statement)
            print(f"✓ {import_statement}")
        except ImportError as e:
            print(f"✗ {import_statement}: {e}")
            return False
    
    return True

if __name__ == "__main__":
    print("Running comprehensive import tests...")
    print("=" * 60)
    
    all_ok = test_all_imports()
    
    print("=" * 60)
    if all_ok:
        print("✓ All imports passed! The refactoring is complete.")
        sys.exit(0)
    else:
        print("✗ Some imports failed! Please check the errors above.")
        sys.exit(1)