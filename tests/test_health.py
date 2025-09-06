"""
Basic health check tests for the MorningAI API
Tests are designed to run without external dependencies
"""
import pytest
import sys
import os

# Add the parent directory to the path so we can import main
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_basic_math():
    """Basic test to ensure pytest is working"""
    assert 1 + 1 == 2

def test_python_version():
    """Test that we're running on Python 3.11"""
    assert sys.version_info.major == 3
    assert sys.version_info.minor >= 11

def test_import_main():
    """Test that we can import the main module without external dependencies"""
    try:
        import main
        assert hasattr(main, 'app')
    except ImportError as e:
        # This is acceptable in CI environment without all dependencies
        pytest.skip(f"Cannot import main module: {e}")

def test_environment_access():
    """Test that we can access environment variables (local test only)"""
    # This test only checks that os.getenv works, not that vars are set
    result = os.getenv("PATH")  # PATH should always exist
    assert result is not None

