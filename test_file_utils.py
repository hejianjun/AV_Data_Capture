#!/usr/bin/env python3
"""
Test script to verify file utility functions work correctly
"""

import sys
import os
import tempfile

# Add the project root to Python path
sys.path.insert(0, os.path.abspath("."))


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
        with open(tmp_path, "w") as f:
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
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Running file utility tests...")
    print("=" * 50)

    if test_file_utils():
        print("✓ All file utility tests passed!")
        sys.exit(0)
    else:
        print("✗ File utility tests failed!")
        sys.exit(1)
