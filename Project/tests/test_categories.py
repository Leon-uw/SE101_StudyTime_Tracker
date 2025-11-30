#!/usr/bin/env python3
"""
Test Categories - Comprehensive tests for category management.
Based on comprehensive test plan covering category CRUD and weight calculations.
"""

import sys
import os
import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

from crud import (
    create_user, add_subject, add_category, get_all_categories, get_categories_as_dict,
    get_category_by_id, update_category, delete_category, get_total_weight_for_subject,
    add_grade, get_all_grades, recalculate_and_update_weights, update_assignment_names_for_category
)
from db import _connect, init_db, USERS_TABLE, SUBJECTS_TABLE, TABLE_NAME, CATEGORIES_TABLE


class TestCategoryCreation:
    """Tests for category creation functionality (CAT-001 to CAT-004)"""
    
    @classmethod
    def setup_class(cls):
        """Initialize database and create test user with subject."""
        init_db()
        cls.test_username = "TEST_CAT_user"
        cls.password = "testpassword123"
        cls.test_subject = "CategoryTestSubject"
        
        # Clean up and create test user
        conn = _connect()
        try:
            curs = conn.cursor()
            curs.execute(f"DELETE FROM {TABLE_NAME} WHERE username = %s", (cls.test_username,))
            curs.execute(f"DELETE FROM {CATEGORIES_TABLE} WHERE username = %s", (cls.test_username,))
            curs.execute(f"DELETE FROM {SUBJECTS_TABLE} WHERE username = %s", (cls.test_username,))
            curs.execute(f"DELETE FROM {USERS_TABLE} WHERE username = %s", (cls.test_username,))
            conn.commit()
        finally:
            curs.close()
            conn.close()
        
        create_user(cls.test_username, cls.password)
        add_subject(cls.test_username, cls.test_subject)
    
    @classmethod
    def teardown_class(cls):
        """Clean up test user and data."""
        conn = _connect()
        try:
            curs = conn.cursor()
            curs.execute(f"DELETE FROM {TABLE_NAME} WHERE username = %s", (cls.test_username,))
            curs.execute(f"DELETE FROM {CATEGORIES_TABLE} WHERE username = %s", (cls.test_username,))
            curs.execute(f"DELETE FROM {SUBJECTS_TABLE} WHERE username = %s", (cls.test_username,))
            curs.execute(f"DELETE FROM {USERS_TABLE} WHERE username = %s", (cls.test_username,))
            conn.commit()
        finally:
            curs.close()
            conn.close()
    
    def teardown_method(self):
        """Clean up categories after each test."""
        conn = _connect()
        try:
            curs = conn.cursor()
            curs.execute(f"DELETE FROM {TABLE_NAME} WHERE username = %s", (self.test_username,))
            curs.execute(f"DELETE FROM {CATEGORIES_TABLE} WHERE username = %s", (self.test_username,))
            conn.commit()
        finally:
            curs.close()
            conn.close()
    
    def test_cat_001_create_valid_category(self):
        """CAT-001: Create category with valid name and weight"""
        category_name = "Homework"
        total_weight = 25
        
        category_id = add_category(self.test_username, self.test_subject, category_name, total_weight)
        
        assert category_id is not None, "Category creation should return an ID"
        
        # Verify category exists
        categories = get_all_categories(self.test_username, self.test_subject)
        category_names = [c['name'] for c in categories]
        assert category_name in category_names, "Category should appear in list"
    
    def test_cat_002_create_category_with_default_name(self):
        """CAT-002: Create category with default assignment naming pattern"""
        category_name = "Quizzes"
        total_weight = 20
        default_name = "Quiz #"
        
        category_id = add_category(self.test_username, self.test_subject, category_name, total_weight, default_name)
        
        # Verify default name is stored
        category = get_category_by_id(self.test_username, category_id)
        assert category is not None, "Category should exist"
        assert category['default_name'] == default_name, "Default name should be stored"
    
    def test_cat_003_create_duplicate_category(self):
        """CAT-003: Attempt to create category with duplicate name in same subject"""
        category_name = "DuplicateCategory"
        
        add_category(self.test_username, self.test_subject, category_name, 30)
        
        # Attempt to create duplicate - should raise exception
        with pytest.raises(Exception):
            add_category(self.test_username, self.test_subject, category_name, 40)
    
    def test_cat_004_same_category_name_different_subjects(self):
        """CAT-004: Same category name can exist in different subjects"""
        category_name = "Exams"
        other_subject = "OtherSubject"
        
        # Create second subject
        add_subject(self.test_username, other_subject)
        
        # Create category in first subject
        cat1_id = add_category(self.test_username, self.test_subject, category_name, 40)
        
        # Create same category name in second subject - should succeed
        cat2_id = add_category(self.test_username, other_subject, category_name, 50)
        
        assert cat1_id != cat2_id, "Different subjects should have different category IDs"


class TestCategoryWeights:
    """Tests for category weight management (CAT-005 to CAT-008)"""
    
    @classmethod
    def setup_class(cls):
        """Initialize database and create test user with subject."""
        init_db()
        cls.test_username = "TEST_CAT_weight_user"
        cls.password = "testpassword123"
        cls.test_subject = "WeightTestSubject"
        
        # Clean up and create test user
        conn = _connect()
        try:
            curs = conn.cursor()
            curs.execute(f"DELETE FROM {TABLE_NAME} WHERE username = %s", (cls.test_username,))
            curs.execute(f"DELETE FROM {CATEGORIES_TABLE} WHERE username = %s", (cls.test_username,))
            curs.execute(f"DELETE FROM {SUBJECTS_TABLE} WHERE username = %s", (cls.test_username,))
            curs.execute(f"DELETE FROM {USERS_TABLE} WHERE username = %s", (cls.test_username,))
            conn.commit()
        finally:
            curs.close()
            conn.close()
        
        create_user(cls.test_username, cls.password)
        add_subject(cls.test_username, cls.test_subject)
    
    @classmethod
    def teardown_class(cls):
        """Clean up test user and data."""
        conn = _connect()
        try:
            curs = conn.cursor()
            curs.execute(f"DELETE FROM {TABLE_NAME} WHERE username = %s", (cls.test_username,))
            curs.execute(f"DELETE FROM {CATEGORIES_TABLE} WHERE username = %s", (cls.test_username,))
            curs.execute(f"DELETE FROM {SUBJECTS_TABLE} WHERE username = %s", (cls.test_username,))
            curs.execute(f"DELETE FROM {USERS_TABLE} WHERE username = %s", (cls.test_username,))
            conn.commit()
        finally:
            curs.close()
            conn.close()
    
    def teardown_method(self):
        """Clean up categories after each test."""
        conn = _connect()
        try:
            curs = conn.cursor()
            curs.execute(f"DELETE FROM {TABLE_NAME} WHERE username = %s", (self.test_username,))
            curs.execute(f"DELETE FROM {CATEGORIES_TABLE} WHERE username = %s", (self.test_username,))
            conn.commit()
        finally:
            curs.close()
            conn.close()
    
    def test_cat_005_total_weight_calculation(self):
        """CAT-005: Total weight for subject calculates correctly"""
        # Add multiple categories
        add_category(self.test_username, self.test_subject, "Cat1", 30)
        add_category(self.test_username, self.test_subject, "Cat2", 40)
        add_category(self.test_username, self.test_subject, "Cat3", 20)
        
        total = get_total_weight_for_subject(self.test_username, self.test_subject)
        
        assert total == 90, f"Total weight should be 90, got {total}"
    
    def test_cat_006_weight_excluding_category(self):
        """CAT-006: Total weight calculation excludes specified category"""
        cat1_id = add_category(self.test_username, self.test_subject, "Cat1", 30)
        add_category(self.test_username, self.test_subject, "Cat2", 40)
        add_category(self.test_username, self.test_subject, "Cat3", 20)
        
        # Exclude Cat1 (30)
        total = get_total_weight_for_subject(self.test_username, self.test_subject, exclude_category_id=cat1_id)
        
        assert total == 60, f"Total weight excluding Cat1 should be 60, got {total}"
    
    def test_cat_007_weight_recalculation_single_assignment(self):
        """CAT-007: Single assignment gets full category weight"""
        add_category(self.test_username, self.test_subject, "TestCat", 40)
        add_grade(self.test_username, self.test_subject, "TestCat", 2.0, "Assignment 1", 85, 0)
        
        recalculate_and_update_weights(self.test_username, self.test_subject, "TestCat")
        
        grades = get_all_grades(self.test_username)
        assignment = [g for g in grades if g['assignment_name'] == "Assignment 1"][0]
        
        assert assignment['weight'] == 40, f"Single assignment should have weight 40, got {assignment['weight']}"
    
    def test_cat_008_weight_recalculation_multiple_assignments(self):
        """CAT-008: Multiple assignments split category weight equally"""
        add_category(self.test_username, self.test_subject, "TestCat", 60)
        
        # Add 3 assignments
        add_grade(self.test_username, self.test_subject, "TestCat", 1.0, "A1", 80, 0)
        add_grade(self.test_username, self.test_subject, "TestCat", 2.0, "A2", 85, 0)
        add_grade(self.test_username, self.test_subject, "TestCat", 1.5, "A3", 90, 0)
        
        recalculate_and_update_weights(self.test_username, self.test_subject, "TestCat")
        
        grades = get_all_grades(self.test_username)
        category_assignments = [g for g in grades if g['category'] == "TestCat"]
        
        # Each should have weight = 60 / 3 = 20
        for assignment in category_assignments:
            assert assignment['weight'] == 20, f"Each assignment should have weight 20, got {assignment['weight']}"
    
    def test_weight_recalculation_with_predictions(self):
        """Weight recalculation includes prediction rows"""
        add_category(self.test_username, self.test_subject, "PredCat", 80)
        
        # Add actual and prediction assignments
        add_grade(self.test_username, self.test_subject, "PredCat", 2.0, "Actual1", 85, 0, is_prediction=False)
        add_grade(self.test_username, self.test_subject, "PredCat", 3.0, "Prediction1", None, 0, is_prediction=True)
        
        recalculate_and_update_weights(self.test_username, self.test_subject, "PredCat")
        
        grades = get_all_grades(self.test_username)
        category_assignments = [g for g in grades if g['category'] == "PredCat"]
        
        # Both assignments should have weight = 80 / 2 = 40
        for assignment in category_assignments:
            assert assignment['weight'] == 40, f"Each assignment should have weight 40, got {assignment['weight']}"


class TestCategoryUpdate:
    """Tests for category update functionality (CAT-009 to CAT-010)"""
    
    @classmethod
    def setup_class(cls):
        """Initialize database and create test user with subject."""
        init_db()
        cls.test_username = "TEST_CAT_update_user"
        cls.password = "testpassword123"
        cls.test_subject = "UpdateTestSubject"
        
        # Clean up and create test user
        conn = _connect()
        try:
            curs = conn.cursor()
            curs.execute(f"DELETE FROM {TABLE_NAME} WHERE username = %s", (cls.test_username,))
            curs.execute(f"DELETE FROM {CATEGORIES_TABLE} WHERE username = %s", (cls.test_username,))
            curs.execute(f"DELETE FROM {SUBJECTS_TABLE} WHERE username = %s", (cls.test_username,))
            curs.execute(f"DELETE FROM {USERS_TABLE} WHERE username = %s", (cls.test_username,))
            conn.commit()
        finally:
            curs.close()
            conn.close()
        
        create_user(cls.test_username, cls.password)
        add_subject(cls.test_username, cls.test_subject)
    
    @classmethod
    def teardown_class(cls):
        """Clean up test user and data."""
        conn = _connect()
        try:
            curs = conn.cursor()
            curs.execute(f"DELETE FROM {TABLE_NAME} WHERE username = %s", (cls.test_username,))
            curs.execute(f"DELETE FROM {CATEGORIES_TABLE} WHERE username = %s", (cls.test_username,))
            curs.execute(f"DELETE FROM {SUBJECTS_TABLE} WHERE username = %s", (cls.test_username,))
            curs.execute(f"DELETE FROM {USERS_TABLE} WHERE username = %s", (cls.test_username,))
            conn.commit()
        finally:
            curs.close()
            conn.close()
    
    def teardown_method(self):
        """Clean up after each test."""
        conn = _connect()
        try:
            curs = conn.cursor()
            curs.execute(f"DELETE FROM {TABLE_NAME} WHERE username = %s", (self.test_username,))
            curs.execute(f"DELETE FROM {CATEGORIES_TABLE} WHERE username = %s", (self.test_username,))
            conn.commit()
        finally:
            curs.close()
            conn.close()
    
    def test_cat_009_update_category_weight(self):
        """CAT-009: Update category weight"""
        category_id = add_category(self.test_username, self.test_subject, "OriginalCat", 30, "Test #")
        
        # Update to new weight
        rows = update_category(self.test_username, category_id, self.test_subject, "OriginalCat", 50, "Test #")
        
        assert rows == 1, "Should update exactly one row"
        
        # Verify updated
        category = get_category_by_id(self.test_username, category_id)
        assert category['total_weight'] == 50, f"Weight should be 50, got {category['total_weight']}"
    
    def test_cat_010_update_category_name(self):
        """CAT-010: Update category name"""
        category_id = add_category(self.test_username, self.test_subject, "OldName", 30)
        
        rows = update_category(self.test_username, category_id, self.test_subject, "NewName", 30)
        
        assert rows == 1, "Should update exactly one row"
        
        # Verify updated
        category = get_category_by_id(self.test_username, category_id)
        assert category['name'] == "NewName", f"Name should be NewName, got {category['name']}"
    
    def test_update_assignment_names_pattern(self):
        """Updating default name pattern updates existing assignments"""
        category_id = add_category(self.test_username, self.test_subject, "PatternCat", 40, "Quiz #")
        
        # Add assignments with old pattern
        add_grade(self.test_username, self.test_subject, "PatternCat", 1.0, "Quiz 1", 80, 10)
        add_grade(self.test_username, self.test_subject, "PatternCat", 1.5, "Quiz 2", 85, 10)
        add_grade(self.test_username, self.test_subject, "PatternCat", 2.0, "Quiz 3", 90, 10)
        
        # Update assignments to new pattern
        updated = update_assignment_names_for_category(
            self.test_username, self.test_subject, "PatternCat", "Quiz #", "Test #"
        )
        
        assert updated == 3, f"Should update 3 assignments, got {updated}"
        
        # Verify new names
        grades = get_all_grades(self.test_username)
        pattern_assignments = [g for g in grades if g['category'] == "PatternCat"]
        names = [g['assignment_name'] for g in pattern_assignments]
        
        assert "Test 1" in names, "Quiz 1 should become Test 1"
        assert "Test 2" in names, "Quiz 2 should become Test 2"
        assert "Test 3" in names, "Quiz 3 should become Test 3"


class TestCategoryDeletion:
    """Tests for category deletion functionality"""
    
    @classmethod
    def setup_class(cls):
        """Initialize database and create test user with subject."""
        init_db()
        cls.test_username = "TEST_CAT_delete_user"
        cls.password = "testpassword123"
        cls.test_subject = "DeleteTestSubject"
        
        # Clean up and create test user
        conn = _connect()
        try:
            curs = conn.cursor()
            curs.execute(f"DELETE FROM {TABLE_NAME} WHERE username = %s", (cls.test_username,))
            curs.execute(f"DELETE FROM {CATEGORIES_TABLE} WHERE username = %s", (cls.test_username,))
            curs.execute(f"DELETE FROM {SUBJECTS_TABLE} WHERE username = %s", (cls.test_username,))
            curs.execute(f"DELETE FROM {USERS_TABLE} WHERE username = %s", (cls.test_username,))
            conn.commit()
        finally:
            curs.close()
            conn.close()
        
        create_user(cls.test_username, cls.password)
        add_subject(cls.test_username, cls.test_subject)
    
    @classmethod
    def teardown_class(cls):
        """Clean up test user and data."""
        conn = _connect()
        try:
            curs = conn.cursor()
            curs.execute(f"DELETE FROM {TABLE_NAME} WHERE username = %s", (cls.test_username,))
            curs.execute(f"DELETE FROM {CATEGORIES_TABLE} WHERE username = %s", (cls.test_username,))
            curs.execute(f"DELETE FROM {SUBJECTS_TABLE} WHERE username = %s", (cls.test_username,))
            curs.execute(f"DELETE FROM {USERS_TABLE} WHERE username = %s", (cls.test_username,))
            conn.commit()
        finally:
            curs.close()
            conn.close()
    
    def teardown_method(self):
        """Clean up after each test."""
        conn = _connect()
        try:
            curs = conn.cursor()
            curs.execute(f"DELETE FROM {TABLE_NAME} WHERE username = %s", (self.test_username,))
            curs.execute(f"DELETE FROM {CATEGORIES_TABLE} WHERE username = %s", (self.test_username,))
            conn.commit()
        finally:
            curs.close()
            conn.close()
    
    def test_delete_empty_category(self):
        """Delete category with no assignments"""
        category_id = add_category(self.test_username, self.test_subject, "EmptyCat", 30)
        
        rows = delete_category(self.test_username, category_id)
        
        assert rows == 1, "Should delete exactly one row"
        
        # Verify deleted
        category = get_category_by_id(self.test_username, category_id)
        assert category is None, "Category should be deleted"
    
    def test_delete_nonexistent_category(self):
        """Attempt to delete non-existent category"""
        rows = delete_category(self.test_username, 999999)
        
        assert rows == 0, "Should return 0 for non-existent category"


class TestCategoriesAsDict:
    """Tests for category retrieval as dictionary"""
    
    @classmethod
    def setup_class(cls):
        """Initialize database and create test user with subjects and categories."""
        init_db()
        cls.test_username = "TEST_CAT_dict_user"
        cls.password = "testpassword123"
        
        # Clean up and create test user
        conn = _connect()
        try:
            curs = conn.cursor()
            curs.execute(f"DELETE FROM {TABLE_NAME} WHERE username = %s", (cls.test_username,))
            curs.execute(f"DELETE FROM {CATEGORIES_TABLE} WHERE username = %s", (cls.test_username,))
            curs.execute(f"DELETE FROM {SUBJECTS_TABLE} WHERE username = %s", (cls.test_username,))
            curs.execute(f"DELETE FROM {USERS_TABLE} WHERE username = %s", (cls.test_username,))
            conn.commit()
        finally:
            curs.close()
            conn.close()
        
        create_user(cls.test_username, cls.password)
        
        # Create subjects with categories
        add_subject(cls.test_username, "Subject1")
        add_subject(cls.test_username, "Subject2")
        
        add_category(cls.test_username, "Subject1", "Cat1A", 30)
        add_category(cls.test_username, "Subject1", "Cat1B", 40)
        add_category(cls.test_username, "Subject2", "Cat2A", 50)
    
    @classmethod
    def teardown_class(cls):
        """Clean up test user and data."""
        conn = _connect()
        try:
            curs = conn.cursor()
            curs.execute(f"DELETE FROM {TABLE_NAME} WHERE username = %s", (cls.test_username,))
            curs.execute(f"DELETE FROM {CATEGORIES_TABLE} WHERE username = %s", (cls.test_username,))
            curs.execute(f"DELETE FROM {SUBJECTS_TABLE} WHERE username = %s", (cls.test_username,))
            curs.execute(f"DELETE FROM {USERS_TABLE} WHERE username = %s", (cls.test_username,))
            conn.commit()
        finally:
            curs.close()
            conn.close()
    
    def test_categories_as_dict_structure(self):
        """Categories organized by subject in dictionary"""
        categories_dict = get_categories_as_dict(self.test_username)
        
        assert isinstance(categories_dict, dict), "Should return dictionary"
        assert "Subject1" in categories_dict, "Should have Subject1"
        assert "Subject2" in categories_dict, "Should have Subject2"
    
    def test_categories_as_dict_content(self):
        """Categories dictionary contains correct category data"""
        categories_dict = get_categories_as_dict(self.test_username)
        
        # Subject1 should have 2 categories
        assert len(categories_dict["Subject1"]) == 2, "Subject1 should have 2 categories"
        
        # Subject2 should have 1 category
        assert len(categories_dict["Subject2"]) == 1, "Subject2 should have 1 category"
        
        # Check category names
        subject1_names = [c['name'] for c in categories_dict["Subject1"]]
        assert "Cat1A" in subject1_names
        assert "Cat1B" in subject1_names


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
