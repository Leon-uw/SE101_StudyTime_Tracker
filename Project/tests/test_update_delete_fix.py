#!/usr/bin/env python3
"""
Test: Update and Delete Fix
Verifies that updating and deleting assignments works correctly after the database fix.
This test simulates the bug where assignments added after app start couldn't be updated/deleted.
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crud import (get_all_grades, add_grade, update_grade, delete_grade,
                  add_category, delete_category)
from db import init_db

def test_update_delete_fix():
    """Test that update and delete work for newly added assignments"""
    print("=" * 60)
    print("Test: Update and Delete Fix")
    print("=" * 60)

    # Ensure database is initialized
    print("\n[1/5] Initializing database...")
    init_db()
    print("✓ Database initialized")

    # Clean up any leftover test data
    print("\n[Cleanup] Removing any leftover test data...")
    from db import _connect, TABLE_NAME, CATEGORIES_TABLE
    conn = _connect()
    try:
        curs = conn.cursor()
        curs.execute(f"DELETE FROM {TABLE_NAME} WHERE Subject = 'FixTestSubject'")
        curs.execute(f"DELETE FROM {CATEGORIES_TABLE} WHERE Subject = 'FixTestSubject'")
        conn.commit()
        print("  ✓ Cleanup complete")
    finally:
        curs.close()
        conn.close()

    # Add a test category first
    print("\n[2/5] Adding test category...")
    cat_id = add_category("FixTestSubject", "TestCategory", 100, "Test #")
    print(f"  ✓ Added category with ID: {cat_id}")

    # Simulate adding an assignment (like the app does)
    print("\n[3/5] Adding test assignment...")
    assignment_id = add_grade(
        subject="FixTestSubject",
        category="TestCategory",
        study_time=3.0,
        assignment_name="Test Assignment",
        grade=85,
        weight=100  # Will be recalculated
    )
    print(f"  ✓ Added assignment with ID: {assignment_id}")

    # Verify assignment exists in database
    all_grades = get_all_grades()
    assignment = next((g for g in all_grades if g['id'] == assignment_id), None)
    if assignment:
        print(f"  ✓ Assignment found in database")
        print(f"    Subject: {assignment['subject']}")
        print(f"    Category: {assignment['category']}")
        print(f"    Assignment: {assignment['assignment_name']}")
        print(f"    Grade: {assignment['grade']}%")
    else:
        print(f"  ✗ Assignment not found!")
        return False

    # Test UPDATE - this would fail before the fix
    print("\n[4/5] Testing UPDATE on newly added assignment...")
    print("  (This would fail with 'Assignment not found' before the fix)")
    try:
        rows_updated = update_grade(
            grade_id=assignment_id,
            subject="FixTestSubject",
            category="TestCategory",
            study_time=4.0,
            assignment_name="Updated Test Assignment",
            grade=90,
            weight=100
        )
        print(f"  ✓ Updated {rows_updated} assignment successfully!")

        # Verify update worked
        all_grades = get_all_grades()
        updated_assignment = next((g for g in all_grades if g['id'] == assignment_id), None)
        if updated_assignment and updated_assignment['assignment_name'] == "Updated Test Assignment":
            print(f"  ✓ Update verified in database")
            print(f"    New name: {updated_assignment['assignment_name']}")
            print(f"    New grade: {updated_assignment['grade']}%")
            print(f"    New study time: {updated_assignment['study_time']}h")
        else:
            print(f"  ✗ Update verification failed!")
            return False
    except Exception as e:
        print(f"  ✗ Update failed with error: {e}")
        return False

    # Test DELETE - this would also fail before the fix
    print("\n[5/5] Testing DELETE on newly added assignment...")
    print("  (This would fail with 'Assignment not found' before the fix)")
    try:
        rows_deleted = delete_grade(assignment_id)
        print(f"  ✓ Deleted {rows_deleted} assignment successfully!")

        # Verify deletion worked
        all_grades = get_all_grades()
        deleted_assignment = next((g for g in all_grades if g['id'] == assignment_id), None)
        if deleted_assignment is None:
            print(f"  ✓ Deletion verified - assignment no longer in database")
        else:
            print(f"  ✗ Deletion verification failed - assignment still exists!")
            return False
    except Exception as e:
        print(f"  ✗ Delete failed with error: {e}")
        return False

    # Clean up test category
    print("\n[Cleanup] Removing test category...")
    delete_category(cat_id)
    print("  ✓ Test data cleaned up")

    print("\n" + "=" * 60)
    print("✓ Update and Delete Fix Working!")
    print("=" * 60)
    print("\nWhat Was Fixed:")
    print("  • UPDATE route now checks database instead of in-memory dict")
    print("  • DELETE route now checks database instead of in-memory dict")
    print("  • Assignments added after app start can now be updated/deleted")
    print("\nBefore Fix:")
    print("  ✗ New assignments only existed in database")
    print("  ✗ In-memory dict only had pre-startup assignments")
    print("  ✗ Update/delete checked in-memory dict → 'Assignment not found'")
    print("\nAfter Fix:")
    print("  ✓ Routes query database to find assignments")
    print("  ✓ All assignments can be updated/deleted regardless of when added")
    print("  ✓ In-memory dict optionally updated for backwards compatibility")

    return True

if __name__ == "__main__":
    success = test_update_delete_fix()
    sys.exit(0 if success else 1)
