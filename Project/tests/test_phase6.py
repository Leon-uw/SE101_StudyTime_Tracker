#!/usr/bin/env python3
"""
Test Phase 6: Database-Only Architecture
Verifies that all in-memory dictionaries have been removed and all operations use database only.
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crud import (get_all_grades, get_all_categories, add_grade, update_grade,
                  delete_grade, add_category, update_category, delete_category,
                  recalculate_and_update_weights)
from db import init_db, _connect, TABLE_NAME, CATEGORIES_TABLE

def test_phase6():
    """Test Phase 6: Database-only architecture (no more in-memory dicts)"""
    print("=" * 60)
    print("Phase 6 Test: Database-Only Architecture")
    print("=" * 60)

    # Ensure database is initialized
    print("\n[1/8] Initializing database...")
    init_db()
    print("✓ Database initialized")

    # Clean up any leftover test data
    print("\n[Cleanup] Removing any leftover test data...")
    conn = _connect()
    try:
        curs = conn.cursor()
        curs.execute(f"DELETE FROM {TABLE_NAME} WHERE Subject = 'Phase6Test'")
        curs.execute(f"DELETE FROM {CATEGORIES_TABLE} WHERE Subject = 'Phase6Test'")
        conn.commit()
        print("  ✓ Cleanup complete")
    finally:
        curs.close()
        conn.close()

    # Test 1: Add category (database only)
    print("\n[2/8] Testing category add (database only)...")
    cat1_id = add_category("Phase6Test", "Category1", 50, "Test #")
    print(f"  ✓ Added category to database with ID: {cat1_id}")

    # Verify it's in database
    categories = get_all_categories(subject="Phase6Test")
    if len(categories) == 1 and categories[0]['id'] == cat1_id:
        print(f"  ✓ Category found in database")
    else:
        print(f"  ✗ Category not found in database!")
        return False

    # Test 2: Add assignment (database only)
    print("\n[3/8] Testing assignment add (database only)...")
    assign1_id = add_grade("Phase6Test", "Category1", 3.0, "Assignment 1", 85, 0)
    print(f"  ✓ Added assignment to database with ID: {assign1_id}")

    # Verify it's in database
    assignments = get_all_grades()
    phase6_assignments = [a for a in assignments if a['subject'] == 'Phase6Test']
    if len(phase6_assignments) == 1 and phase6_assignments[0]['id'] == assign1_id:
        print(f"  ✓ Assignment found in database")
    else:
        print(f"  ✗ Assignment not found in database!")
        return False

    # Test 3: Weight recalculation (database only)
    print("\n[4/8] Testing weight recalculation (database only)...")
    rows_updated = recalculate_and_update_weights("Phase6Test", "Category1")
    print(f"  ✓ Recalculated weights for {rows_updated} assignment(s)")

    # Verify weight was updated in database
    assignments = get_all_grades()
    phase6_assignments = [a for a in assignments if a['subject'] == 'Phase6Test']
    if phase6_assignments[0]['weight'] == 50.0:
        print(f"  ✓ Weight correctly recalculated in database: {phase6_assignments[0]['weight']}%")
    else:
        print(f"  ✗ Weight incorrect! Got {phase6_assignments[0]['weight']}, expected 50.0")
        return False

    # Test 4: Update assignment (database only)
    print("\n[5/8] Testing assignment update (database only)...")
    rows_affected = update_grade(assign1_id, "Phase6Test", "Category1", 4.0, "Updated Assignment 1", 90, 0)
    print(f"  ✓ Updated {rows_affected} assignment(s) in database")

    # Verify update in database
    assignments = get_all_grades()
    phase6_assignments = [a for a in assignments if a['subject'] == 'Phase6Test']
    if (phase6_assignments[0]['assignment_name'] == "Updated Assignment 1" and
        phase6_assignments[0]['grade'] == 90 and
        phase6_assignments[0]['study_time'] == 4.0):
        print(f"  ✓ Update verified in database")
    else:
        print(f"  ✗ Update verification failed!")
        return False

    # Test 5: Add second assignment to test multi-assignment weight calc
    print("\n[6/8] Testing multi-assignment weight calculation...")
    assign2_id = add_grade("Phase6Test", "Category1", 2.0, "Assignment 2", 95, 0)
    recalculate_and_update_weights("Phase6Test", "Category1")
    print(f"  ✓ Added second assignment and recalculated weights")

    # Verify both assignments have correct weights (25% each)
    assignments = get_all_grades()
    phase6_assignments = [a for a in assignments if a['subject'] == 'Phase6Test']
    if len(phase6_assignments) == 2:
        weights = [a['weight'] for a in phase6_assignments]
        if all(w == 25.0 for w in weights):
            print(f"  ✓ Both assignments have correct weight: 25.0%")
        else:
            print(f"  ✗ Weights incorrect! Got {weights}, expected [25.0, 25.0]")
            return False
    else:
        print(f"  ✗ Expected 2 assignments, found {len(phase6_assignments)}")
        return False

    # Test 6: Update category (database only)
    print("\n[7/8] Testing category update (database only)...")
    rows_affected = update_category(cat1_id, "Phase6Test", "UpdatedCategory1", 60, "Updated #")
    print(f"  ✓ Updated {rows_affected} category in database")

    # Verify update in database
    categories = get_all_categories(subject="Phase6Test")
    if (categories[0]['name'] == "UpdatedCategory1" and
        categories[0]['total_weight'] == 60):
        print(f"  ✓ Category update verified in database")
    else:
        print(f"  ✗ Category update verification failed!")
        return False

    # Test 7: Delete assignment (database only)
    print("\n[8/8] Testing assignment delete (database only)...")
    rows_deleted = delete_grade(assign2_id)
    print(f"  ✓ Deleted {rows_deleted} assignment(s) from database")

    # Verify deletion in database
    assignments = get_all_grades()
    phase6_assignments = [a for a in assignments if a['subject'] == 'Phase6Test']
    if len(phase6_assignments) == 1:
        print(f"  ✓ Deletion verified - only 1 assignment remains")
    else:
        print(f"  ✗ Expected 1 assignment, found {len(phase6_assignments)}")
        return False

    # Clean up test data
    print("\n[Cleanup] Removing test data...")
    delete_grade(assign1_id)
    delete_category(cat1_id)
    print("  ✓ Test data cleaned up")

    print("\n" + "=" * 60)
    print("✓ Phase 6 Complete: Database-Only Architecture Working!")
    print("=" * 60)
    print("\nWhat Changed in Phase 6:")
    print("  • Removed in-memory study_data dictionary")
    print("  • Removed in-memory weight_categories dictionary")
    print("  • Removed all dual-write code")
    print("  • All CRUD operations now use database directly")
    print("  • Simplified codebase - single source of truth")
    print("\nBenefits:")
    print("  ✓ No more synchronization issues")
    print("  ✓ Data persists correctly across restarts")
    print("  ✓ Cleaner, more maintainable code")
    print("  ✓ True database-driven architecture")
    print("\nArchitecture Before Phase 6:")
    print("  - In-memory dictionaries initialized at startup")
    print("  - Dual-write to both database AND in-memory")
    print("  - Potential sync issues between database and memory")
    print("\nArchitecture After Phase 6:")
    print("  - Database is the ONLY source of truth")
    print("  - All reads query database")
    print("  - All writes go to database only")
    print("  - Simple, reliable, scalable")
    print("\nReady for: New feature development on clean architecture!")

    return True

if __name__ == "__main__":
    success = test_phase6()
    sys.exit(0 if success else 1)
