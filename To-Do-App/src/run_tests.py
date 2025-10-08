#!/usr/bin/env python3
"""
Test runner that loads environment variables from .env file
Usage: python3 run_tests.py [pytest arguments]
"""

import os
import sys
import subprocess

def load_env_file(filepath='.env'):
    """Load environment variables from .env file"""
    if not os.path.exists(filepath):
        print(f"❌ {filepath} file not found!")
        print("📝 Create one with your database credentials:")
        print("   TODO_DB_USER=your_username")
        print("   TODO_DB_PASSWORD=your_password")
        print("   TODO_DB_NAME=your_database")
        return False
    
    print(f"📂 Loading environment from {filepath}")
    
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value
                if 'PASSWORD' in key:
                    print(f"   {key}=***")
                else:
                    print(f"   {key}={value}")
    
    return True

def main():
    """Main function to load env and run tests"""
    print("🧪 To-Do App Test Runner")
    print("=" * 40)
    
    # Load environment variables
    if not load_env_file():
        sys.exit(1)
    
    # Verify required variables are set
    required_vars = ['TODO_DB_USER', 'TODO_DB_PASSWORD', 'TODO_DB_NAME']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        sys.exit(1)
    
    print("\n✅ Environment configured successfully!")
    print("\n🚀 Running tests...")
    print("-" * 40)
    
    # Run pytest with any additional arguments
    pytest_args = ['pytest'] + sys.argv[1:]  # Pass through any command line args
    
    try:
        result = subprocess.run(pytest_args, cwd=os.getcwd())
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()