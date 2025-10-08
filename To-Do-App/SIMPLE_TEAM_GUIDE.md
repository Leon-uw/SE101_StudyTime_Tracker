# Simple Team Setup Guide

## Quick Setup (3 steps)

1. **Copy the setup file**: Your team already has `shared_setup.py`

2. **In your test file, add these lines at the top**:
```python
import pytest
from shared_setup import setup_test_environment, cleanup_after_test

if not setup_test_environment():
    pytest.skip("Missing database credentials")

# Clean database before each test
@pytest.fixture(autouse=True)
def clean_database():
    from shared_setup import cleanup_test_data
    cleanup_test_data()
```

3. **Add cleanup at the bottom**:
```python
def teardown_module():
    cleanup_after_test()
```

## That's it! 

Your tests now have:
- ✅ Database cleanup
- ✅ Logging configured  
- ✅ Environment variables loaded
- ✅ Automatic skipping if no credentials

## Example Test File

```python
import pytest
from shared_setup import setup_test_environment, cleanup_after_test

# Setup (copy these lines)
if not setup_test_environment():
    pytest.skip("Missing database credentials")

# Clean database before each test
@pytest.fixture(autouse=True)
def clean_database():
    from shared_setup import cleanup_test_data
    cleanup_test_data()

def test_my_feature():
    import logging
    logging.info("Testing my feature")
    # Your test code here
    assert True

def test_another_feature():
    # Database is clean for each test
    # Your test code here  
    assert True

# Cleanup (copy this function)
def teardown_module():
    cleanup_after_test()
```

**Total extra code per test file: ~10 lines**