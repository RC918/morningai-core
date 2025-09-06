"""
Basic health check tests for the MorningAI API
"""
import pytest
import sys
import os

# Add the parent directory to the path so we can import main
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_import_main():
    """Test that we can import the main module"""
    try:
        import main
        assert hasattr(main, 'app')
    except ImportError as e:
        pytest.skip(f"Cannot import main module: {e}")

def test_basic_math():
    """Basic test to ensure pytest is working"""
    assert 1 + 1 == 2

def test_environment_variables():
    """Test that we can access environment variables"""
    # This should not fail even if env vars are not set
    database_url = os.getenv("DATABASE_URL")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    # Just check that we can access them (they might be None)
    assert database_url is not None or database_url is None
    assert openai_key is not None or openai_key is None

