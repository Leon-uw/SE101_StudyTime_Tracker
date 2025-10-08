# To-Do App - SE101 Project Team 21

A Python-based To-Do application with comprehensive testing infrastructure.

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- MySQL database access (UWaterloo)
- VPN connection to UWaterloo network

### Setup
1. Navigate to the `src` directory
2. Copy environment template: `cp .env.example .env`  
3. Edit `.env` with your database credentials
4. Run tests: `python3 run_tests.py -v`

## 📁 Project Structure

```
To-Do-App/
├── src/
│   ├── todo.py              # Core To-Do functions
│   ├── test_todo.py         # Comprehensive test suite (28 tests)
│   ├── shared_setup.py      # Simple team setup functions  
│   ├── run_tests.py         # Test runner with environment loading
│   └── .env.example         # Environment template
├── SIMPLE_TEAM_GUIDE.md     # Team collaboration guide (1 page)
└── TESTING_STRATEGY.md      # Current testing approach
```

## 🧪 Testing

### Running Tests
```bash
cd src

# All tests
python3 run_tests.py -v

# Specific test class  
python3 run_tests.py test_todo.py::TestAddFunction -v

# HTML report
python3 run_tests.py --html=report.html --self-contained-html
```

### Current Test Coverage
- ✅ **28 comprehensive test cases**
- ✅ Add function validation (14 tests)
- ✅ Edge cases and error handling
- ✅ Database integration testing
- ✅ Logging and reporting

## 👥 Team Collaboration

### For Team Members
**See `SIMPLE_TEAM_GUIDE.md` for complete instructions**

Quick setup - add ~10 lines to your test file:
```python
import pytest
from shared_setup import setup_test_environment, cleanup_after_test

if not setup_test_environment():
    pytest.skip("Missing database credentials")

@pytest.fixture(autouse=True)  
def clean_database():
    from shared_setup import cleanup_test_data
    cleanup_test_data()

# Your tests here...

def teardown_module():
    cleanup_after_test()
```

### What You Get
- ✅ Database cleanup before/after each test
- ✅ Logging configured with timestamps
- ✅ Environment variables loaded from `.env`
- ✅ Skip tests if no credentials
- ✅ HTML test reports

## 🔒 Security
- Individual `.env` files per team member
- Database credentials not committed to git
- Automatic cleanup prevents data conflicts

## 📖 Documentation
- `SIMPLE_TEAM_GUIDE.md` - Team setup instructions
- `TESTING_STRATEGY.md` - Current testing approach
- Inline code documentation

## 🛠️ Current Status
- **14/14 tests passing** in TestAddFunction
- **Simplified architecture** - 90% less complexity
- **Team-ready** with simple setup pattern
- **Professional testing** with comprehensive coverage

---

**Team 21**: Simple, effective, professional testing infrastructure.

**Need help?** Check `SIMPLE_TEAM_GUIDE.md` for team collaboration instructions.