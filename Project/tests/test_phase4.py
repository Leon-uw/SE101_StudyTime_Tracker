#!/usr/bin/env python3
"""
Test Phase 4: Weight Recalculation and Category Management
Verifies that weights are recalculated in the database and category CRUD works.
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crud import (get_all_grades, get_all_categories, add_grade, add_category,
                  recalculate_and_update_weights, update_category, delete_category,
                  get_total_weight_for_subject)
from db import init_db

def test_phase4():
    """Test Phase 4: Weight recalculation and category management"""
    print("=" * 60)
    print("Phase 4 Test: Weight Recalculation & Category Management")
    print("=" * 60)

    # Ensure database is initialized
    print("\n[1/7] Initializing database...")
    init_db()
    print("✓ Database initialized")

    # Clean up any leftover test data from previous runs
    print("\n[Cleanup] Removing any leftover test data...")
    from crud import delete_grade
    from db import _connect, TABLE_NAME, CATEGORIES_TABLE
    conn = _connect()
    try:
        curs = conn.cursor()
        # Delete test assignments
        curs.execute(f"DELETE FROM {TABLE_NAME} WHERE Subject = 'TestSubject'")
        # Delete test categories
        curs.execute(f"DELETE FROM {CATEGORIES_TABLE} WHERE Subject = 'TestSubject'")
        conn.commit()
        print("  ✓ Cleanup complete")
    finally:
        curs.close()
        conn.close()

    # Test adding a category
    print("\n[2/7] Testing add_category()...")
    test_cat_id = add_category(
        subject="TestSubject",
        category_name="TestCategory",
        total_weight=50,
        default_name="Test #"
    )
    print(f"  ✓ Added category with ID: {test_cat_id}")

    # Verify category was added
    categories = get_all_categories(subject="TestSubject")
    test_cat = next((c for c in categories if c['id'] == test_cat_id), None)
    if test_cat and test_cat['name'] == 'TestCategory':
        print(f"  ✓ Category found in database")
        print(f"    Subject: {test_cat['subject']}")
        print(f"    Name: {test_cat['name']}")
        print(f"    Total Weight: {test_cat['total_weight']}%")
    else:
        print(f"  ✗ Category not found or incorrect!")
        print(f"  Found categories: {categories}")
        return False

    # Test weight recalculation with 1 assignment
    print("\n[3/7] Testing weight recalculation with 1 assignment...")
    assign1_id = add_grade(
        subject="TestSubject",
        category="TestCategory",
        study_time=2.0,
        assignment_name="Test Assignment 1",
        grade=85,
        weight=0  # Will be recalculated
    )
    print(f"  ✓ Added assignment with ID: {assign1_id}")

    # Recalculate weights
    rows_updated = recalculate_and_update_weights("TestSubject", "TestCategory")
    print(f"  ✓ Updated {rows_updated} assignment(s)")

    # Check weight (should be 50% since total_weight is 50 and there's 1 assignment)
    grades = get_all_grades()
    assign1 = next((g for g in grades if g['id'] == assign1_id), None)
    if assign1 and assign1['weight'] == 50.0:
        print(f"  ✓ Weight correctly calculated: {assign1['weight']}% (expected 50%)")
    else:
        print(f"  ✗ Weight incorrect! Got {assign1['weight']}, expected 50")
        return False

    # Test weight recalculation with 2 assignments
    print("\n[4/7] Testing weight recalculation with 2 assignments...")
    assign2_id = add_grade(
        subject="TestSubject",
        category="TestCategory",
        study_time=3.0,
        assignment_name="Test Assignment 2",
        grade=90,
        weight=0  # Will be recalculated
    )
    print(f"  ✓ Added second assignment with ID: {assign2_id}")

    # Recalculate weights
    rows_updated = recalculate_and_update_weights("TestSubject", "TestCategory")
    print(f"  ✓ Updated {rows_updated} assignment(s)")

    # Check weights (should be 25% each since total_weight is 50 and there are 2 assignments)
    grades = get_all_grades()
    assign1 = next((g for g in grades if g['id'] == assign1_id), None)
    assign2 = next((g for g in grades if g['id'] == assign2_id), None)

    if assign1 and assign1['weight'] == 25.0 and assign2 and assign2['weight'] == 25.0:
        print(f"  ✓ Weights correctly calculated:")
        print(f"    Assignment 1: {assign1['weight']}% (expected 25%)")
        print(f"    Assignment 2: {assign2['weight']}% (expected 25%)")
    else:
        print(f"  ✗ Weights incorrect!")
        return False

    # Test update_category
    print("\n[5/7] Testing update_category()...")
    rows_affected = update_category(
        category_id=test_cat_id,
        subject="TestSubject",
        category_name="UpdatedCategory",
        total_weight=40,
        default_name="Updated #"
    )
    print(f"  ✓ Updated {rows_affected} category")

    # Verify update
    categories = get_all_categories(subject="TestSubject")
    updated_cat = next((c for c in categories if c['id'] == test_cat_id), None)
    if updated_cat and updated_cat['name'] == 'UpdatedCategory' and updated_cat['total_weight'] == 40:
        print(f"  ✓ Category updated correctly:")
        print(f"    Name: {updated_cat['name']}")
        print(f"    Total Weight: {updated_cat['total_weight']}%")
    else:
        print(f"  ✗ Category update failed!")
        return False

    # Test get_total_weight_for_subject
    print("\n[6/7] Testing get_total_weight_for_subject()...")
    total_weight = get_total_weight_for_subject("TestSubject")
    if total_weight == 40:
        print(f"  ✓ Total weight for TestSubject: {total_weight}%")
    else:
        print(f"  ✗ Total weight incorrect! Got {total_weight}, expected 40")
        return False

    # Add another category to test total weight calculation
    test_cat2_id = add_category("TestSubject", "TestCategory2", 30, "Test2 #")
    total_weight = get_total_weight_for_subject("TestSubject")
    if total_weight == 70:
        print(f"  ✓ Total weight after adding second category: {total_weight}%")
    else:
        print(f"  ✗ Total weight incorrect! Got {total_weight}, expected 70")
        return False

    # Test excluding a category from total
    total_weight_excluding = get_total_weight_for_subject("TestSubject", exclude_category_id=test_cat2_id)
    if total_weight_excluding == 40:
        print(f"  ✓ Total weight excluding second category: {total_weight_excluding}%")
    else:
        print(f"  ✗ Excluded total weight incorrect! Got {total_weight_excluding}, expected 40")
        return False

    # Test delete_category
    print("\n[7/7] Testing delete_category()...")
    rows_deleted = delete_category(test_cat2_id)
    print(f"  ✓ Deleted {rows_deleted} category")

    # Verify deletion
    categories = get_all_categories(subject="TestSubject")
    remaining_test_cat2 = next((c for c in categories if c['id'] == test_cat2_id), None)
    if remaining_test_cat2 is None:
        print(f"  ✓ Category deleted successfully")
    else:
        print(f"  ✗ Category deletion failed! Category still exists")
        return False

    # Clean up test data
    print("\n[Cleanup] Removing test data...")
    from crud import delete_grade
    delete_grade(assign1_id)
    delete_grade(assign2_id)
    delete_category(test_cat_id)
    print("  ✓ Test data cleaned up")

    print("\n" + "=" * 60)
    print("✓ Phase 4 Complete: Weight Recalculation & Category CRUD Working!")
    print("=" * 60)
    print("\nStatus:")
    print("  • Weight recalculation updates database correctly")
    print("  • Weights distributed evenly across assignments in category")
    print("  • Category CRUD operations work (add, update, delete)")
    print("  • Total weight calculation works with exclusions")
    print("  • All changes persist in database")
    print("\nNext: Start Flask app and verify:")
    print("      1. Add an assignment - weight should persist after restart")
    print("      2. Add a category - should be saved to database")
    print("      3. Update/delete categories - changes should persist")
    print("\n      Run: python3 app.py")

    return True

if __name__ == "__main__":
    success = test_phase4()
    sys.exit(0 if success else 1)
