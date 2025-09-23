"""
Test runner for the Email Event Parser v2.0.

Run this to execute all tests for the new configurable system.
"""
import sys
import os
import pytest

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_tests():
    """Run all tests."""
    test_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Run pytest on the test directory
    pytest.main([
        test_dir,
        "-v",  # Verbose output
        "--tb=short",  # Short traceback format
        "--color=yes"  # Colored output
    ])

if __name__ == "__main__":
    run_tests()

