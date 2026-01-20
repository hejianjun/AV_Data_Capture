#!/usr/bin/env python3
"""
Test script to verify refactored module structure
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.abspath('.'))

def test_imports():
    """Test that all functions can be imported correctly"""
    print("Testing imports...")
    
    # Test imports from new modular structure
    try:
        from mdc.utils.http import get_html, get_html_session, post_html
        print("✓ Imported HTTP functions from mdc.utils.http")
    except ImportError as e:
        print(f"✗ Failed to import HTTP functions: {e}")
        return False
    
    try:
        from mdc.utils.download import parallel_download_files, download_file_with_filename
        print("✓ Imported download functions from mdc.utils.download")
    except ImportError as e:
        print(f"✗ Failed to import download functions: {e}")
        return False
    
    try:
        from mdc.utils.cookie import load_cookies
        print("✓ Imported cookie functions from mdc.utils.cookie")
    except ImportError as e:
        print(f"✗ Failed to import cookie functions: {e}")
        return False
    
    try:
        from mdc.utils.string import cn_space
        print("✓ Imported string functions from mdc.utils.string")
    except ImportError as e:
        print(f"✗ Failed to import string functions: {e}")
        return False
    
    try:
        from mdc.utils.html import get_xpath_single
        print("✓ Imported HTML functions from mdc.utils.html")
    except ImportError as e:
        print(f"✗ Failed to import HTML functions: {e}")
        return False
    
    # Test backward compatibility imports
    try:
        from mdc.utils import (
            get_html, get_html_session, post_html,
            parallel_download_files, load_cookies,
            cn_space, get_xpath_single
        )
        print("✓ Imported all functions via backward compatibility interface")
    except ImportError as e:
        print(f"✗ Failed to import via backward compatibility interface: {e}")
        return False
    
    return True

def test_basic_functionality():
    """Test basic functionality of some functions"""
    print("\nTesting basic functionality...")
    
    try:
        from mdc.utils.string import cn_space
        result = cn_space("测试字符串", 10)
        print(f"✓ cn_space function works: cn_space('测试字符串', 10) = {result}")
    except Exception as e:
        print(f"✗ cn_space function failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Testing refactored module structure...")
    print("=" * 50)
    
    imports_ok = test_imports()
    functionality_ok = test_basic_functionality()
    
    print("=" * 50)
    if imports_ok and functionality_ok:
        print("✓ All tests passed! The refactoring was successful.")
        sys.exit(0)
    else:
        print("✗ Some tests failed! Please check the refactored code.")
        sys.exit(1)