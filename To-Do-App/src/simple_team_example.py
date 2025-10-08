"""
Simple example showing how team members can use the shared setup
"""
import pytest
from shared_setup import setup_test_environment, cleanup_after_test

# Call setup at the start of your test file
if not setup_test_environment():
    pytest.skip("Missing database credentials in .env file")

def test_example():
    """Example test using shared setup"""
    import logging
    logging.info("This test has automatic setup and logging!")
    # Your test code here
    assert True

# Add more test functions here...

def teardown_module():
    """This runs after all tests in this file"""
    cleanup_after_test()