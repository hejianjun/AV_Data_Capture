#!/usr/bin/env python3
"""
Functional test script to verify that core functionality works after removing ADC_function.py
"""

import sys
import os
import tempfile
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, os.path.abspath('.'))

def test_http_request():
    """Test HTTP request functionality"""
    print("Testing HTTP request functionality...")
    
    from mdc.utils.http import get_html
    
    try:
        # Test with a simple URL
        url = "https://www.example.com"
        response = get_html(url)
        if response and "Example Domain" in response:
            print("✓ HTTP GET request successful")
            return True
        else:
            print("✗ HTTP GET request failed: No expected content")
            return False
    except Exception as e:
        print(f"✗ HTTP GET request failed with exception: {e}")
        return False

def test_file_download():
    """Test file download functionality"""
    print("Testing file download functionality...")
    
    from mdc.utils.download import download_file_with_filename
    
    try:
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as tmpdir:
            # Test with a small image file
            url = "https://via.placeholder.com/100x100"
            filename = "test_image.jpg"
            path = tmpdir
            
            download_file_with_filename(url, filename, path)
            
            # Check if the file was downloaded successfully
            file_path = os.path.join(path, filename)
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                print("✓ File download successful")
                return True
            else:
                print("✗ File download failed: File not found or empty")
                return False
    except Exception as e:
        print(f"✗ File download failed with exception: {e}")
        return False

def test_file_utils():
    """Test file utility functions"""
    print("Testing file utility functions...")
    
    from mdc.file.file_utils import file_not_exist_or_empty, file_modification_days
    
    try:
        # Test file_not_exist_or_empty
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        # Empty file should return True
        if file_not_exist_or_empty(tmp_path):
            print("✓ file_not_exist_or_empty correctly identifies empty file")
        else:
            print("✗ file_not_exist_or_empty failed for empty file")
            return False
        
        # Write something to the file
        with open(tmp_path, 'w') as f:
            f.write("test content")
        
        # Non-empty file should return False
        if not file_not_exist_or_empty(tmp_path):
            print("✓ file_not_exist_or_empty correctly identifies non-empty file")
        else:
            print("✗ file_not_exist_or_empty failed for non-empty file")
            return False
        
        # Test file_modification_days
        days = file_modification_days(tmp_path)
        if days >= 0:
            print("✓ file_modification_days works correctly")
        else:
            print("✗ file_modification_days failed")
            return False
        
        # Clean up
        os.unlink(tmp_path)
        return True
    except Exception as e:
        print(f"✗ File utility functions failed with exception: {e}")
        return False

if __name__ == "__main__":
    print("Running functional tests after removing ADC_function.py...")
    print("=" * 70)
    
    # Run tests
    tests = [
        ("HTTP Request", test_http_request),
        ("File Download", test_file_download),
        ("File Utilities", test_file_utils),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        if test_func():
            passed += 1
    
    print("\n" + "=" * 70)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All functional tests passed! The code is working correctly.")
        sys.exit(0)
    else:
        print("✗ Some functional tests failed! Please check the errors above.")
        sys.exit(1)