#!/usr/bin/env python3
"""
Test Assessments - Comprehensive tests for assessment/grade management.
Based on comprehensive test plan covering assessment CRUD, weight preview, and bulk operations.
"""

import sys
import os
import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

from crud import (
    create_user, add_subject, add_category, add_grade, update_grade,
    delete_grade, delete_grades_bulk, get_all_grades, recalculate_and_update_weights
)
from db import _connect, init_db, USERS_TABLE, SUBJECTS_TABLE, TABLE_NAME, CATEGORIES_TABLE


class TestAssessmentCreation:
    """Tests for assessment/grade creation functionality (ASMNT-001 to ASMNT-005)"""
    
    @classmethod
    def setup_class(cls):
        """Initialize database and create test user with subject and category."""
        init_db()
        cls.test_username = "TEST_ASMNT_user"
        cls.password = "testpassword123"
        cls.test_subject = "AssessmentTestSubject"
        cls.test_category = "TestCategory"
        
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
        add_category(cls.test_username, cls.test_subject, cls.test_category, 100)
    
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
        """Clean up grades after each test."""
        conn = _connect()
        try:
            curs = conn.cursor()
            curs.execute(f"DELETE FROM {TABLE_NAME} WHERE username = %s", (self.test_username,))
            conn.commit()
        finally:
            curs.close()
            conn.close()
    
    def test_asmnt_001_create_valid_assessment(self):
        """ASMNT-001: Create assessment with all valid fields"""
        assignment_name = "Test Assignment 1"
        study_time = 2.5
        grade = 85
        weight = 25
        
        grade_id = add_grade(
            self.test_username, self.test_subject, self.test_category,
            study_time, assignment_name, grade, weight
        )
        
        assert grade_id is not None, "Should return a grade ID"
        
        # Verify in database
        grades = get_all_grades(self.test_username)
        assert len(grades) == 1, "Should have one grade"
        assert grades[0]['assignment_name'] == assignment_name
        assert grades[0]['study_time'] == study_time
        assert grades[0]['grade'] == grade
        assert grades[0]['weight'] == weight
    
    def test_asmnt_002_create_assessment_without_grade(self):
        """ASMNT-002: Create assessment with NULL grade (ungraded)"""
        grade_id = add_grade(
            self.test_username, self.test_subject, self.test_category,
            2.0, "Ungraded Assignment", None, 20
        )
        
        assert grade_id is not None, "Should return a grade ID"
        
        grades = get_all_grades(self.test_username)
        assert grades[0]['grade'] is None, "Grade should be NULL"
    
    def test_asmnt_003_create_prediction_assessment(self):
        """ASMNT-003: Create prediction assessment (is_prediction=True)"""
        predicted_grade = 75
        
        grade_id = add_grade(
            self.test_username, self.test_subject, self.test_category,
            3.0, "Predicted Assignment", None, 20,
            is_prediction=True, predicted_grade=predicted_grade
        )
        
        assert grade_id is not None, "Should return a grade ID"
        
        grades = get_all_grades(self.test_username)
        assert grades[0]['is_prediction'] is True, "Should be a prediction"
        assert grades[0]['predicted_grade'] == predicted_grade, "Should have predicted grade"
    
    def test_asmnt_004_create_with_zero_study_time(self):
        """ASMNT-004: Create assessment with 0 study time"""
        grade_id = add_grade(
            self.test_username, self.test_subject, self.test_category,
            0.0, "No Study Assignment", 70, 15
        )
        
        assert grade_id is not None, "Should allow 0 study time"
        
        grades = get_all_grades(self.test_username)
        assert grades[0]['study_time'] == 0.0, "Study time should be 0"
    
    def test_asmnt_005_create_with_100_percent_grade(self):
        """ASMNT-005: Create assessment with 100% grade"""
        grade_id = add_grade(
            self.test_username, self.test_subject, self.test_category,
            5.0, "Perfect Score", 100, 25
        )
        
        assert grade_id is not None, "Should allow 100% grade"
        
        grades = get_all_grades(self.test_username)
        assert grades[0]['grade'] == 100, "Grade should be 100"


class TestAssessmentUpdate:
    """Tests for assessment update functionality (ASMNT-006 to ASMNT-010)"""
    
    @classmethod
    def setup_class(cls):
        """Initialize database and create test user with subject and category."""
        init_db()
        cls.test_username = "TEST_ASMNT_update_user"
        cls.password = "testpassword123"
        cls.test_subject = "UpdateTestSubject"
        cls.test_category = "TestCategory"
        
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
        add_category(cls.test_username, cls.test_subject, cls.test_category, 100)
    
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
        """Clean up grades after each test."""
        conn = _connect()
        try:
            curs = conn.cursor()
            curs.execute(f"DELETE FROM {TABLE_NAME} WHERE username = %s", (self.test_username,))
            conn.commit()
        finally:
            curs.close()
            conn.close()
    
    def test_asmnt_006_update_grade_value(self):
        """ASMNT-006: Update an existing assessment's grade"""
        # Create initial grade
        grade_id = add_grade(
            self.test_username, self.test_subject, self.test_category,
            2.0, "Update Test", 75, 20
        )
        
        # Update grade
        rows = update_grade(
            self.test_username, grade_id, self.test_subject, self.test_category,
            2.0, "Update Test", 85, 20
        )
        
        assert rows == 1, "Should update exactly one row"
        
        grades = get_all_grades(self.test_username)
        assert grades[0]['grade'] == 85, "Grade should be updated to 85"
    
    def test_asmnt_007_update_study_time(self):
        """ASMNT-007: Update an assessment's study time"""
        grade_id = add_grade(
            self.test_username, self.test_subject, self.test_category,
            2.0, "Study Time Test", 80, 20
        )
        
        rows = update_grade(
            self.test_username, grade_id, self.test_subject, self.test_category,
            4.5, "Study Time Test", 80, 20
        )
        
        assert rows == 1, "Should update exactly one row"
        
        grades = get_all_grades(self.test_username)
        assert grades[0]['study_time'] == 4.5, "Study time should be updated to 4.5"
    
    def test_asmnt_008_update_assignment_name(self):
        """ASMNT-008: Update an assessment's name"""
        grade_id = add_grade(
            self.test_username, self.test_subject, self.test_category,
            2.0, "Original Name", 80, 20
        )
        
        rows = update_grade(
            self.test_username, grade_id, self.test_subject, self.test_category,
            2.0, "Updated Name", 80, 20
        )
        
        assert rows == 1, "Should update exactly one row"
        
        grades = get_all_grades(self.test_username)
        assert grades[0]['assignment_name'] == "Updated Name", "Name should be updated"
    
    def test_asmnt_009_update_nonexistent_assessment(self):
        """ASMNT-009: Attempt to update non-existent assessment"""
        rows = update_grade(
            self.test_username, 999999, self.test_subject, self.test_category,
            2.0, "Nonexistent", 80, 20
        )
        
        assert rows == 0, "Should return 0 for non-existent ID"
    
    def test_asmnt_010_convert_prediction_to_actual(self):
        """ASMNT-010: Convert prediction to actual grade"""
        # Create prediction
        grade_id = add_grade(
            self.test_username, self.test_subject, self.test_category,
            3.0, "Prediction Convert", None, 25,
            is_prediction=True, predicted_grade=80
        )
        
        # Convert to actual grade
        rows = update_grade(
            self.test_username, grade_id, self.test_subject, self.test_category,
            3.0, "Prediction Convert", 82, 25,
            is_prediction=False, predicted_grade=80  # Keep predicted for comparison
        )
        
        assert rows == 1, "Should update exactly one row"
        
        grades = get_all_grades(self.test_username)
        assert grades[0]['is_prediction'] is False, "Should no longer be a prediction"
        assert grades[0]['grade'] == 82, "Should have actual grade"


class TestAssessmentDeletion:
    """Tests for assessment deletion functionality (ASMNT-011 to ASMNT-015)"""
    
    @classmethod
    def setup_class(cls):
        """Initialize database and create test user with subject and category."""
        init_db()
        cls.test_username = "TEST_ASMNT_delete_user"
        cls.password = "testpassword123"
        cls.test_subject = "DeleteTestSubject"
        cls.test_category = "TestCategory"
        
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
        add_category(cls.test_username, cls.test_subject, cls.test_category, 100)
    
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
        """Clean up grades after each test."""
        conn = _connect()
        try:
            curs = conn.cursor()
            curs.execute(f"DELETE FROM {TABLE_NAME} WHERE username = %s", (self.test_username,))
            conn.commit()
        finally:
            curs.close()
            conn.close()
    
    def test_asmnt_011_delete_single_assessment(self):
        """ASMNT-011: Delete a single assessment"""
        grade_id = add_grade(
            self.test_username, self.test_subject, self.test_category,
            2.0, "Delete Me", 80, 20
        )
        
        # Verify exists
        grades_before = get_all_grades(self.test_username)
        assert len(grades_before) == 1, "Should have one grade"
        
        # Delete
        rows = delete_grade(self.test_username, grade_id)
        
        assert rows == 1, "Should delete exactly one row"
        
        # Verify deleted
        grades_after = get_all_grades(self.test_username)
        assert len(grades_after) == 0, "Should have no grades"
    
    def test_asmnt_012_delete_nonexistent_assessment(self):
        """ASMNT-012: Attempt to delete non-existent assessment"""
        rows = delete_grade(self.test_username, 999999)
        
        assert rows == 0, "Should return 0 for non-existent ID"
    
    def test_asmnt_013_bulk_delete_assessments(self):
        """ASMNT-013: Delete multiple assessments at once"""
        # Create multiple grades
        id1 = add_grade(self.test_username, self.test_subject, self.test_category, 1.0, "Delete1", 70, 10)
        id2 = add_grade(self.test_username, self.test_subject, self.test_category, 2.0, "Delete2", 80, 10)
        id3 = add_grade(self.test_username, self.test_subject, self.test_category, 3.0, "Delete3", 90, 10)
        
        # Verify all exist
        grades_before = get_all_grades(self.test_username)
        assert len(grades_before) == 3, "Should have 3 grades"
        
        # Bulk delete
        rows = delete_grades_bulk(self.test_username, [id1, id2, id3])
        
        assert rows == 3, "Should delete 3 rows"
        
        # Verify all deleted
        grades_after = get_all_grades(self.test_username)
        assert len(grades_after) == 0, "Should have no grades"
    
    def test_asmnt_014_bulk_delete_partial(self):
        """ASMNT-014: Bulk delete with some valid and some invalid IDs"""
        id1 = add_grade(self.test_username, self.test_subject, self.test_category, 1.0, "Keep1", 70, 10)
        id2 = add_grade(self.test_username, self.test_subject, self.test_category, 2.0, "Delete", 80, 10)
        
        # Delete id2 and a non-existent ID
        rows = delete_grades_bulk(self.test_username, [id2, 999999])
        
        assert rows == 1, "Should delete only 1 valid row"
        
        # Verify id1 still exists
        grades_after = get_all_grades(self.test_username)
        assert len(grades_after) == 1, "Should have 1 grade remaining"
        assert grades_after[0]['id'] == id1, "Should be the kept grade"
    
    def test_asmnt_015_bulk_delete_empty_list(self):
        """ASMNT-015: Bulk delete with empty list"""
        rows = delete_grades_bulk(self.test_username, [])
        
        assert rows == 0, "Should return 0 for empty list"


class TestWeightPreview:
    """Tests for weight preview functionality"""
    
    @classmethod
    def setup_class(cls):
        """Initialize database and create test user with subject and category."""
        init_db()
        cls.test_username = "TEST_ASMNT_preview_user"
        cls.password = "testpassword123"
        cls.test_subject = "PreviewTestSubject"
        cls.test_category = "TestCategory"
        
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
        add_category(cls.test_username, cls.test_subject, cls.test_category, 60)  # 60% total weight
    
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
        """Clean up grades after each test."""
        conn = _connect()
        try:
            curs = conn.cursor()
            curs.execute(f"DELETE FROM {TABLE_NAME} WHERE username = %s", (self.test_username,))
            conn.commit()
        finally:
            curs.close()
            conn.close()
    
    def test_weight_preview_new_assignment(self):
        """Weight preview shows correct weight when adding new assignment"""
        # With 60% category weight and 0 existing assignments, new assignment gets 60%
        # After recalculation, one assignment should have weight 60
        add_grade(self.test_username, self.test_subject, self.test_category, 2.0, "First", 80, 0)
        recalculate_and_update_weights(self.test_username, self.test_subject, self.test_category)
        
        grades = get_all_grades(self.test_username)
        assert grades[0]['weight'] == 60, "Single assignment should have full category weight"
    
    def test_weight_preview_second_assignment(self):
        """Weight preview shows correct split when adding second assignment"""
        # Two assignments in 60% category = 30% each
        add_grade(self.test_username, self.test_subject, self.test_category, 2.0, "First", 80, 0)
        add_grade(self.test_username, self.test_subject, self.test_category, 2.0, "Second", 85, 0)
        recalculate_and_update_weights(self.test_username, self.test_subject, self.test_category)
        
        grades = get_all_grades(self.test_username)
        for g in grades:
            assert g['weight'] == 30, f"Each assignment should have 30% weight, got {g['weight']}"
    
    def test_weight_preview_after_delete(self):
        """Weight preview shows correct rebalance after deleting assignment"""
        # Add 3 assignments
        id1 = add_grade(self.test_username, self.test_subject, self.test_category, 2.0, "First", 80, 0)
        id2 = add_grade(self.test_username, self.test_subject, self.test_category, 2.0, "Second", 85, 0)
        id3 = add_grade(self.test_username, self.test_subject, self.test_category, 2.0, "Third", 90, 0)
        recalculate_and_update_weights(self.test_username, self.test_subject, self.test_category)
        
        # Each should have 60/3 = 20
        grades_before = get_all_grades(self.test_username)
        for g in grades_before:
            assert g['weight'] == 20, "Each of 3 assignments should have 20%"
        
        # Delete one
        delete_grade(self.test_username, id2)
        recalculate_and_update_weights(self.test_username, self.test_subject, self.test_category)
        
        # Remaining 2 should have 60/2 = 30
        grades_after = get_all_grades(self.test_username)
        assert len(grades_after) == 2, "Should have 2 grades"
        for g in grades_after:
            assert g['weight'] == 30, "Each of 2 assignments should have 30%"


class TestAssessmentPosition:
    """Tests for assessment ordering/position functionality"""
    
    @classmethod
    def setup_class(cls):
        """Initialize database and create test user with subject and category."""
        init_db()
        cls.test_username = "TEST_ASMNT_pos_user"
        cls.password = "testpassword123"
        cls.test_subject = "PositionTestSubject"
        cls.test_category = "TestCategory"
        
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
        add_category(cls.test_username, cls.test_subject, cls.test_category, 100)
    
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
        """Clean up grades after each test."""
        conn = _connect()
        try:
            curs = conn.cursor()
            curs.execute(f"DELETE FROM {TABLE_NAME} WHERE username = %s", (self.test_username,))
            conn.commit()
        finally:
            curs.close()
            conn.close()
    
    def test_position_increments(self):
        """Positions increment for each new assignment"""
        add_grade(self.test_username, self.test_subject, self.test_category, 1.0, "First", 80, 20)
        add_grade(self.test_username, self.test_subject, self.test_category, 2.0, "Second", 85, 20)
        add_grade(self.test_username, self.test_subject, self.test_category, 3.0, "Third", 90, 20)
        
        grades = get_all_grades(self.test_username)
        
        # Should be ordered by position
        positions = [g['position'] for g in grades]
        assert positions == sorted(positions), "Positions should be in order"
        
        # Names should be in order of creation
        names = [g['assignment_name'] for g in grades]
        assert names == ["First", "Second", "Third"], "Assignments should be in creation order"
    
    def test_order_preserved_after_delete(self):
        """Order preserved when middle item is deleted"""
        add_grade(self.test_username, self.test_subject, self.test_category, 1.0, "First", 80, 20)
        id2 = add_grade(self.test_username, self.test_subject, self.test_category, 2.0, "Middle", 85, 20)
        add_grade(self.test_username, self.test_subject, self.test_category, 3.0, "Last", 90, 20)
        
        # Delete middle
        delete_grade(self.test_username, id2)
        
        grades = get_all_grades(self.test_username)
        names = [g['assignment_name'] for g in grades]
        
        assert names == ["First", "Last"], "Order should be preserved after deletion"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
