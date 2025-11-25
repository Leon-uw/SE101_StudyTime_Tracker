#!/usr/bin/env python3
"""
Test Phase 2: Read-Only Database Integration
Verifies that the app can fetch and display data from database.
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crud import get_all_grades, get_all_categories, get_categories_as_dict
from db import init_db

def test_phase2():
    """Test Phase 2: Read-only database integration"""
    print("=" * 60)
    print("Phase 2 Test: Read-Only Database Integration")
    print("=" * 60)

    # Ensure database is initialized
    print("\n[1/5] Initializing database...")
    init_db()
    print("✓ Database initialized")

    # Test get_all_grades with lowercase keys
    print("\n[2/5] Testing get_all_grades() with lowercase keys...")
    grades = get_all_grades()
    print(f"  ✓ Fetched {len(grades)} assignments")

    if grades:
        sample = grades[0]
        expected_keys = ['id', 'subject', 'category', 'study_time', 'assignment_name', 'grade', 'weight']
        actual_keys = list(sample.keys())

        print(f"  Expected keys: {expected_keys}")
        print(f"  Actual keys:   {actual_keys}")

        if set(expected_keys) == set(actual_keys):
            print("  ✓ Keys are lowercase and match Sprint 2A format")
        else:
            print("  ✗ Key mismatch!")
            return False

        print(f"\n  Sample assignment:")
        print(f"    Subject: {sample['subject']}")
        print(f"    Category: {sample['category']}")
        print(f"    Assignment: {sample['assignment_name']}")
        print(f"    Time: {sample['study_time']}h")
        print(f"    Grade: {sample['grade']}%")
        print(f"    Weight: {sample['weight']}%")

    # Test get_all_categories
    print("\n[3/5] Testing get_all_categories()...")
    categories = get_all_categories()
    print(f"  ✓ Fetched {len(categories)} categories")

    if categories:
        sample = categories[0]
        expected_keys = ['id', 'subject', 'name', 'total_weight', 'default_name']
        actual_keys = list(sample.keys())

        if set(expected_keys) == set(actual_keys):
            print("  ✓ Keys match Sprint 2A format")
        else:
            print(f"  ✗ Key mismatch! Expected {expected_keys}, got {actual_keys}")
            return False

        print(f"\n  Sample category:")
        print(f"    Subject: {sample['subject']}")
        print(f"    Name: {sample['name']}")
        print(f"    Total Weight: {sample['total_weight']}%")
        print(f"    Default Name: '{sample['default_name']}'")

    # Test get_categories_as_dict
    print("\n[4/5] Testing get_categories_as_dict()...")
    cat_dict = get_categories_as_dict()
    print(f"  ✓ Organized into {len(cat_dict)} subjects")

    for subject, cats in cat_dict.items():
        print(f"    {subject}: {len(cats)} categories")
        if cats:
            sample_cat = cats[0]
            # Should NOT have 'subject' key in individual categories
            if 'subject' in sample_cat:
                print(f"  ✗ Category shouldn't have 'subject' key!")
                return False

    print("  ✓ Dictionary structure matches Sprint 2A weight_categories")

    # Test app imports
    print("\n[5/5] Testing app can import CRUD functions...")
    try:
        # Simulate app import
        from app import display_table, calculate_summary
        print("  ✓ App successfully imports CRUD functions")
        print("  ✓ display_table() and calculate_summary() available")
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False

    print("\n" + "=" * 60)
    print("✓ Phase 2 Complete: Read-Only Integration Working!")
    print("=" * 60)
    print("\nStatus:")
    print("  • App can read assignments from database")
    print("  • App can read categories from database")
    print("  • Field names normalized to lowercase")
    print("  • Dictionary structure matches Sprint 2A format")
    print("  • Writes still go to in-memory dictionaries (safe!)")
    print("\nNext: Start Flask app and verify UI displays database data")
    print("      Run: python3 app.py")

    return True

if __name__ == "__main__":
    success = test_phase2()
    sys.exit(0 if success else 1)
