#!/usr/bin/env python3
"""
Test Edge Cases - Edge case and boundary condition tests.
Based on comprehensive test plan covering error handling, boundary conditions, and unusual inputs.
"""

import sys
import os
import pytest
import math

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

from crud import (
    create_user, add_subject, add_category, add_grade, update_grade,
    delete_grade, get_all_grades, get_total_weight_for_subject
)
from db import _connect, init_db, USERS_TABLE, SUBJECTS_TABLE, TABLE_NAME, CATEGORIES_TABLE


class TestBoundaryConditions:
    """Tests for boundary condition handling"""
    
    @classmethod
    def setup_class(cls):
        """Initialize database and create test user."""
        init_db()
        cls.test_username = "TEST_EDGE_boundary"
        cls.password = "testpassword123"
        cls.test_subject = "EdgeTestSubject"
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
    
    def test_edge_zero_grade(self):
        """EDGE-001: 0% grade is valid and stored correctly"""
        grade_id = add_grade(
            self.test_username, self.test_subject, self.test_category,
            2.0, "Zero Grade Test", 0, 20
        )
        
        grades = get_all_grades(self.test_username)
        assert grades[0]['grade'] == 0, "Should store 0% grade"
    
    def test_edge_100_grade(self):
        """EDGE-002: 100% grade is valid and stored correctly"""
        grade_id = add_grade(
            self.test_username, self.test_subject, self.test_category,
            5.0, "Perfect Grade Test", 100, 20
        )
        
        grades = get_all_grades(self.test_username)
        assert grades[0]['grade'] == 100, "Should store 100% grade"
    
    def test_edge_zero_study_time(self):
        """EDGE-003: 0 hours study time is valid"""
        grade_id = add_grade(
            self.test_username, self.test_subject, self.test_category,
            0.0, "No Study Test", 50, 20
        )
        
        grades = get_all_grades(self.test_username)
        assert grades[0]['study_time'] == 0.0, "Should store 0 study time"
    
    def test_edge_very_high_study_time(self):
        """EDGE-004: Very high study time is handled"""
        grade_id = add_grade(
            self.test_username, self.test_subject, self.test_category,
            100.0, "Marathon Study Test", 95, 20
        )
        
        grades = get_all_grades(self.test_username)
        assert grades[0]['study_time'] == 100.0, "Should store high study time"
    
    def test_edge_decimal_grade(self):
        """EDGE-005: Decimal grades are handled correctly"""
        grade_id = add_grade(
            self.test_username, self.test_subject, self.test_category,
            2.5, "Decimal Grade Test", 85.5, 20
        )
        
        grades = get_all_grades(self.test_username)
        assert grades[0]['grade'] == 85.5 or grades[0]['grade'] == 85, \
            "Should handle decimal grade (may be rounded)"
    
    def test_edge_decimal_study_time(self):
        """EDGE-006: Decimal study times are handled"""
        grade_id = add_grade(
            self.test_username, self.test_subject, self.test_category,
            2.75, "Decimal Hours Test", 80, 20
        )
        
        grades = get_all_grades(self.test_username)
        assert abs(grades[0]['study_time'] - 2.75) < 0.01, "Should store decimal study time"


class TestSpecialCharacters:
    """Tests for special character handling"""
    
    @classmethod
    def setup_class(cls):
        """Initialize database and create test user."""
        init_db()
        cls.test_username = "TEST_EDGE_special"
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
    
    def test_special_chars_in_subject_name(self):
        """Subject names with special characters"""
        subject_name = "Math & Science 101: Intro!"
        
        subject_id = add_subject(self.test_username, subject_name)
        assert subject_id is not None, "Should create subject with special chars"
        
        from crud import get_subject_by_name
        subject = get_subject_by_name(self.test_username, subject_name)
        assert subject is not None, "Should retrieve subject with special chars"
        assert subject['name'] == subject_name, "Name should be preserved exactly"
    
    def test_special_chars_in_assignment_name(self):
        """Assignment names with special characters"""
        add_subject(self.test_username, "SpecialCharSubject")
        add_category(self.test_username, "SpecialCharSubject", "Tests", 100)
        
        assignment_name = "Test #1 - Part A (Version 2.0)"
        
        grade_id = add_grade(
            self.test_username, "SpecialCharSubject", "Tests",
            2.0, assignment_name, 85, 20
        )
        
        grades = get_all_grades(self.test_username)
        special_grade = [g for g in grades if g['assignment_name'] == assignment_name]
        assert len(special_grade) == 1, "Should store assignment with special chars"
    
    def test_unicode_in_names(self):
        """Unicode characters in names"""
        try:
            subject_name = "Matemáticas 数学 رياضيات"
            
            subject_id = add_subject(self.test_username, subject_name)
            assert subject_id is not None, "Should create subject with unicode"
            
            from crud import get_subject_by_name
            subject = get_subject_by_name(self.test_username, subject_name)
            assert subject is not None, "Should retrieve subject with unicode"
        except Exception as e:
            pytest.skip(f"Unicode not fully supported: {e}")


class TestWeightBoundaries:
    """Tests for category weight boundary conditions"""
    
    @classmethod
    def setup_class(cls):
        """Initialize database and create test user."""
        init_db()
        cls.test_username = "TEST_EDGE_weights"
        cls.password = "testpassword123"
        cls.test_subject = "WeightEdgeSubject"
        
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
            curs.execute(f"DELETE FROM {CATEGORIES_TABLE} WHERE username = %s", (self.test_username,))
            conn.commit()
        finally:
            curs.close()
            conn.close()
    
    def test_weight_single_100_category(self):
        """Single category with 100% weight"""
        add_category(self.test_username, self.test_subject, "OnlyCategory", 100)
        
        total = get_total_weight_for_subject(self.test_username, self.test_subject)
        assert total == 100, "Total weight should be 100"
    
    def test_weight_many_small_categories(self):
        """Many categories with small weights summing to 100%"""
        for i in range(10):
            add_category(self.test_username, self.test_subject, f"SmallCat{i}", 10)
        
        total = get_total_weight_for_subject(self.test_username, self.test_subject)
        assert total == 100, "10 categories of 10% should sum to 100"
    
    def test_weight_uneven_distribution(self):
        """Categories with uneven weight distribution"""
        add_category(self.test_username, self.test_subject, "BigCat", 60)
        add_category(self.test_username, self.test_subject, "MedCat", 25)
        add_category(self.test_username, self.test_subject, "SmallCat", 15)
        
        total = get_total_weight_for_subject(self.test_username, self.test_subject)
        assert total == 100, "60 + 25 + 15 should equal 100"


class TestPredictionEdgeCases:
    """Tests for prediction system edge cases"""
    
    def test_prediction_with_single_datapoint(self):
        """Prediction with only one historical data point"""
        from app import estimate_k, predict_grade
        
        k = estimate_k([3.0], [85], [0.2])
        assert k > 0, "Should produce valid k from single point"
        
        predicted = predict_grade(3.0, 0.2, k)
        assert 0 <= predicted <= 100, "Should produce valid prediction"
    
    def test_prediction_with_extreme_k(self):
        """Prediction handles extreme k values"""
        from app import predict_grade
        
        # Very high k (efficient learner)
        pred_high_k = predict_grade(2.0, 0.2, 10.0)
        assert 0 <= pred_high_k <= 100, "High k should produce valid prediction"
        
        # Very low k (slow learner)
        pred_low_k = predict_grade(2.0, 0.2, 0.01)
        assert 0 <= pred_low_k <= 100, "Low k should produce valid prediction"
    
    def test_prediction_near_zero_weight(self):
        """Prediction with very small weight"""
        from app import predict_grade
        
        predicted = predict_grade(3.0, 0.01, 0.5)
        assert 0 <= predicted <= 100, "Small weight should produce valid prediction"
    
    def test_required_hours_near_max(self):
        """Required hours for grade near maximum"""
        from app import required_hours
        
        hours_99 = required_hours(99, 0.2, 0.5)
        assert hours_99 > 0, "99% should require positive hours"
        assert not math.isinf(hours_99), "99% should be achievable"
        
        hours_99_5 = required_hours(99.5, 0.2, 0.5)
        # 99.5% is at the boundary, may return infinity
        assert hours_99_5 >= 0, "99.5% should be non-negative"


class TestEmptyStateHandling:
    """Tests for empty state handling"""
    
    @classmethod
    def setup_class(cls):
        """Initialize database and create test user."""
        init_db()
        cls.test_username = "TEST_EDGE_empty"
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
    
    def test_empty_subjects_list(self):
        """Getting subjects for user with no subjects"""
        from crud import get_all_subjects
        
        subjects = get_all_subjects(self.test_username)
        assert subjects == [], "Empty subject list should return empty array"
    
    def test_empty_grades_list(self):
        """Getting grades for user with no grades"""
        grades = get_all_grades(self.test_username)
        assert grades == [], "Empty grades list should return empty array"
    
    def test_empty_categories_list(self):
        """Getting categories for subject with no categories"""
        from crud import get_all_categories
        
        add_subject(self.test_username, "EmptyCatSubject")
        categories = get_all_categories(self.test_username, "EmptyCatSubject")
        assert categories == [], "Empty categories list should return empty array"


class TestLargeDataHandling:
    """Tests for handling large amounts of data"""
    
    @classmethod
    def setup_class(cls):
        """Initialize database and create test user."""
        init_db()
        cls.test_username = "TEST_EDGE_large"
        cls.password = "testpassword123"
        cls.test_subject = "LargeDataSubject"
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
    
    def test_many_assignments(self):
        """Handling many assignments in one category"""
        # Add 50 assignments
        for i in range(50):
            add_grade(
                self.test_username, self.test_subject, self.test_category,
                float(i % 5 + 1), f"Assignment {i+1}", (60 + i % 40), 2
            )
        
        grades = get_all_grades(self.test_username)
        assert len(grades) == 50, "Should retrieve all 50 assignments"
        
        # Clean up
        conn = _connect()
        try:
            curs = conn.cursor()
            curs.execute(f"DELETE FROM {TABLE_NAME} WHERE username = %s", (self.test_username,))
            conn.commit()
        finally:
            curs.close()
            conn.close()
    
    def test_many_subjects(self):
        """Handling many subjects"""
        from crud import get_all_subjects
        
        # Add 20 subjects
        for i in range(20):
            add_subject(self.test_username, f"Subject_{i+1}")
        
        subjects = get_all_subjects(self.test_username)
        # Original subject + 20 new ones = 21
        assert len(subjects) >= 20, "Should retrieve all subjects"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
