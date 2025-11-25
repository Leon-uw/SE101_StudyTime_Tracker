#!/usr/bin/env python3
"""
Test Phase 7: Subject Management
Verifies that subjects can be added, retrieved, and deleted independently from assignments.
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crud import (get_all_subjects, add_subject, delete_subject, get_subject_by_name,
                  add_grade, add_category, get_all_grades, get_all_categories)
from db import init_db, _connect, SUBJECTS_TABLE

def test_phase7():
    """Test Phase 7: Subject management with dedicated subjects table"""
    print("=" * 60)
    print("Phase 7 Test: Subject Management")
    print("=" * 60)

    # Ensure database is initialized
    print("\n[1/10] Initializing database...")
    init_db()
    print("✓ Database initialized")

    # Clean up any leftover test data
    print("\n[Cleanup] Removing any leftover test data...")
    conn = _connect()
    try:
        curs = conn.cursor()
        # Get test subject IDs
        curs.execute(f"SELECT id FROM {SUBJECTS_TABLE} WHERE name IN ('Phase7Test', 'Phase7Test2')")
        test_subject_ids = [row[0] for row in curs.fetchall()]

        # Delete test subjects (will cascade to assignments/categories via delete_subject function)
        for subject_id in test_subject_ids:
            delete_subject(subject_id)

        print("  ✓ Cleanup complete")
    finally:
        curs.close()
        conn.close()

    # Test 1: Add subject (standalone, no assignments)
    print("\n[2/10] Testing add subject (standalone)...")
    try:
        subject1_id = add_subject("Phase7Test")
        print(f"  ✓ Added subject to database with ID: {subject1_id}")
    except Exception as e:
        print(f"  ✗ Failed to add subject: {e}")
        return False

    # Test 2: Verify subject exists in database
    print("\n[3/10] Testing get_all_subjects...")
    all_subjects = get_all_subjects()
    phase7_subjects = [s for s in all_subjects if s['name'] == 'Phase7Test']
    if len(phase7_subjects) == 1 and phase7_subjects[0]['id'] == subject1_id:
        print(f"  ✓ Subject found in database")
    else:
        print(f"  ✗ Subject not found in database!")
        return False

    # Test 3: Get subject by name
    print("\n[4/10] Testing get_subject_by_name...")
    subject = get_subject_by_name("Phase7Test")
    if subject and subject['id'] == subject1_id and subject['name'] == 'Phase7Test':
        print(f"  ✓ Found subject by name: {subject['name']} (ID: {subject['id']})")
    else:
        print(f"  ✗ Failed to find subject by name!")
        return False

    # Test 4: Try to add duplicate subject (should fail)
    print("\n[5/10] Testing duplicate subject prevention...")
    try:
        add_subject("Phase7Test")
        print(f"  ✗ Duplicate subject was allowed (should have failed)!")
        return False
    except Exception as e:
        print(f"  ✓ Duplicate subject correctly prevented")

    # Test 5: Add subject with assignment
    print("\n[6/10] Testing subject persistence with assignment...")
    subject2_id = add_subject("Phase7Test2")
    add_category("Phase7Test2", "TestCategory", 50, "Test #")
    assign_id = add_grade("Phase7Test2", "TestCategory", 2.0, "Test Assignment", 85, 0)
    print(f"  ✓ Added subject with category and assignment")

    # Verify subject still exists
    subject2 = get_subject_by_name("Phase7Test2")
    if subject2 and subject2['id'] == subject2_id:
        print(f"  ✓ Subject persists correctly with assignments")
    else:
        print(f"  ✗ Subject not found after adding assignment!")
        return False

    # Test 6: Subject exists without assignments (original subject)
    print("\n[7/10] Testing subject without assignments still exists...")
    subject1_check = get_subject_by_name("Phase7Test")
    if subject1_check and subject1_check['id'] == subject1_id:
        print(f"  ✓ Subject without assignments persists correctly")
    else:
        print(f"  ✗ Subject without assignments disappeared!")
        return False

    # Test 7: Display page shows subject without assignments
    print("\n[8/10] Testing display page includes all subjects...")
    all_subjects = get_all_subjects()
    subject_names = [s['name'] for s in all_subjects]
    if 'Phase7Test' in subject_names and 'Phase7Test2' in subject_names:
        print(f"  ✓ Both subjects appear in subjects list")
    else:
        print(f"  ✗ Not all subjects appear in list!")
        print(f"    Found subjects: {subject_names}")
        return False

    # Test 8: Delete subject (cascade delete assignments and categories)
    print("\n[9/10] Testing delete subject (cascade)...")
    rows_deleted = delete_subject(subject2_id)
    if rows_deleted > 0:
        print(f"  ✓ Deleted subject (rows affected: {rows_deleted})")
    else:
        print(f"  ✗ Failed to delete subject!")
        return False

    # Verify assignment and category were also deleted
    all_grades = get_all_grades()
    phase7_assignments = [a for a in all_grades if a['subject'] == 'Phase7Test2']
    all_categories = get_all_categories()
    phase7_categories = [c for c in all_categories if c['subject'] == 'Phase7Test2']

    if len(phase7_assignments) == 0 and len(phase7_categories) == 0:
        print(f"  ✓ Assignments and categories cascaded delete correctly")
    else:
        print(f"  ✗ Cascade delete failed - orphaned data remains!")
        return False

    # Test 9: Delete subject without assignments
    print("\n[10/10] Testing delete subject without assignments...")
    rows_deleted = delete_subject(subject1_id)
    if rows_deleted > 0:
        print(f"  ✓ Deleted subject without assignments")
    else:
        print(f"  ✗ Failed to delete subject!")
        return False

    # Verify it's gone
    subject1_final = get_subject_by_name("Phase7Test")
    if subject1_final is None:
        print(f"  ✓ Subject deleted successfully")
    else:
        print(f"  ✗ Subject still exists after deletion!")
        return False

    print("\n" + "=" * 60)
    print("✓ Phase 7 Complete: Subject Management Working!")
    print("=" * 60)
    print("\nWhat Changed in Phase 7:")
    print("  • Created subjects table in database")
    print("  • Subjects now persist independently of assignments")
    print("  • Can add/delete subjects without assignments")
    print("  • Subjects table is source of truth for subject list")
    print("\nBenefits:")
    print("  ✓ Subjects persist even when empty")
    print("  ✓ User can pre-create subjects before adding assignments")
    print("  ✓ Cleaner data model with proper subject management")
    print("  ✓ Cascade delete ensures data integrity")
    print("\nBug Fixed:")
    print("  ✓ 'Add Subject' functionality now works correctly")
    print("  ✓ Subjects appear in dropdown immediately after creation")
    print("  ✓ No more empty pages when navigating to new subjects")
    print("\nReady for: Phase 7.2 - Recommendations algorithm!")

    return True

if __name__ == "__main__":
    success = test_phase7()
    sys.exit(0 if success else 1)
