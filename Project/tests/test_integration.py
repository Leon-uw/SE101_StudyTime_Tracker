#!/usr/bin/env python3
"""
Test Integration - End-to-end integration tests for complete workflows.
Tests full user journeys and feature interactions.
"""

import sys
import os
import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

from crud import (
    create_user, verify_user, add_subject, get_all_subjects, delete_subject,
    add_category, get_all_categories, add_grade, update_grade, delete_grade,
    get_all_grades, recalculate_and_update_weights, get_subject_by_name,
    rename_subject
)
from db import _connect, init_db, USERS_TABLE, SUBJECTS_TABLE, TABLE_NAME, CATEGORIES_TABLE


class TestFullUserJourney:
    """End-to-end test simulating a complete user journey"""
    
    @classmethod
    def setup_class(cls):
        """Initialize database."""
        init_db()
    
    def test_complete_user_workflow(self):
        """Test complete workflow: register -> create subject -> add categories -> add grades -> view stats"""
        username = "TEST_INT_workflow_user"
        password = "testpassword123"
        
        # Clean up any existing test data
        conn = _connect()
        try:
            curs = conn.cursor()
            curs.execute(f"DELETE FROM {TABLE_NAME} WHERE username = %s", (username,))
            curs.execute(f"DELETE FROM {CATEGORIES_TABLE} WHERE username = %s", (username,))
            curs.execute(f"DELETE FROM {SUBJECTS_TABLE} WHERE username = %s", (username,))
            curs.execute(f"DELETE FROM {USERS_TABLE} WHERE username = %s", (username,))
            conn.commit()
        finally:
            curs.close()
            conn.close()
        
        try:
            # STEP 1: Register
            user_id = create_user(username, password)
            assert user_id is not None, "Registration should succeed"
            
            # STEP 2: Login
            login_success = verify_user(username, password)
            assert login_success is True, "Login should succeed"
            
            # STEP 3: Create subject
            subject_id = add_subject(username, "Mathematics")
            assert subject_id is not None, "Subject creation should succeed"
            
            subjects = get_all_subjects(username)
            assert len(subjects) == 1, "Should have one subject"
            
            # STEP 4: Create categories
            hw_cat_id = add_category(username, "Mathematics", "Homework", 30, "HW #")
            quiz_cat_id = add_category(username, "Mathematics", "Quizzes", 20, "Quiz #")
            exam_cat_id = add_category(username, "Mathematics", "Exams", 50, "Exam #")
            
            categories = get_all_categories(username, "Mathematics")
            assert len(categories) == 3, "Should have 3 categories"
            
            # Verify total weight is 100%
            total_weight = sum(c['total_weight'] for c in categories)
            assert total_weight == 100, "Total weight should be 100%"
            
            # STEP 5: Add assignments
            hw1_id = add_grade(username, "Mathematics", "Homework", 1.5, "HW 1", 90, 0)
            hw2_id = add_grade(username, "Mathematics", "Homework", 2.0, "HW 2", 85, 0)
            quiz1_id = add_grade(username, "Mathematics", "Quizzes", 1.0, "Quiz 1", 80, 0)
            exam1_id = add_grade(username, "Mathematics", "Exams", 5.0, "Exam 1", 78, 0)
            
            # Recalculate weights
            recalculate_and_update_weights(username, "Mathematics", "Homework")
            recalculate_and_update_weights(username, "Mathematics", "Quizzes")
            recalculate_and_update_weights(username, "Mathematics", "Exams")
            
            # STEP 6: Verify weights calculated correctly
            grades = get_all_grades(username)
            
            # Homework: 30% / 2 assignments = 15% each
            hw_grades = [g for g in grades if g['category'] == 'Homework']
            for hw in hw_grades:
                assert hw['weight'] == 15, f"Homework weight should be 15, got {hw['weight']}"
            
            # Quizzes: 20% / 1 assignment = 20%
            quiz_grades = [g for g in grades if g['category'] == 'Quizzes']
            assert quiz_grades[0]['weight'] == 20, "Quiz weight should be 20"
            
            # Exams: 50% / 1 assignment = 50%
            exam_grades = [g for g in grades if g['category'] == 'Exams']
            assert exam_grades[0]['weight'] == 50, "Exam weight should be 50"
            
            # STEP 7: Calculate weighted average
            total_earned_weight = 0
            weighted_sum = 0
            for g in grades:
                if g['grade'] is not None:
                    weighted_sum += g['grade'] * g['weight']
                    total_earned_weight += g['weight']
            
            weighted_avg = weighted_sum / total_earned_weight if total_earned_weight > 0 else 0
            assert 75 <= weighted_avg <= 95, f"Weighted average should be reasonable, got {weighted_avg}"
            
        finally:
            # Clean up
            conn = _connect()
            try:
                curs = conn.cursor()
                curs.execute(f"DELETE FROM {TABLE_NAME} WHERE username = %s", (username,))
                curs.execute(f"DELETE FROM {CATEGORIES_TABLE} WHERE username = %s", (username,))
                curs.execute(f"DELETE FROM {SUBJECTS_TABLE} WHERE username = %s", (username,))
                curs.execute(f"DELETE FROM {USERS_TABLE} WHERE username = %s", (username,))
                conn.commit()
            finally:
                curs.close()
                conn.close()


class TestMultiSubjectWorkflow:
    """Test workflows with multiple subjects"""
    
    @classmethod
    def setup_class(cls):
        """Initialize database and create test user."""
        init_db()
        cls.test_username = "TEST_INT_multi_subject"
        cls.password = "testpassword123"
        
        # Clean up
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
    
    def test_multiple_subjects_independent(self):
        """Multiple subjects maintain independent data"""
        # Create two subjects
        add_subject(self.test_username, "Physics")
        add_subject(self.test_username, "Chemistry")
        
        # Add categories to each
        add_category(self.test_username, "Physics", "Labs", 50)
        add_category(self.test_username, "Physics", "Tests", 50)
        add_category(self.test_username, "Chemistry", "Labs", 30)
        add_category(self.test_username, "Chemistry", "Tests", 70)
        
        # Add grades
        add_grade(self.test_username, "Physics", "Labs", 3.0, "Lab 1", 85, 0)
        add_grade(self.test_username, "Chemistry", "Labs", 2.5, "Lab 1", 90, 0)
        
        recalculate_and_update_weights(self.test_username, "Physics", "Labs")
        recalculate_and_update_weights(self.test_username, "Chemistry", "Labs")
        
        # Verify each subject has correct weights
        grades = get_all_grades(self.test_username)
        
        physics_lab = [g for g in grades if g['subject'] == 'Physics' and g['category'] == 'Labs'][0]
        chem_lab = [g for g in grades if g['subject'] == 'Chemistry' and g['category'] == 'Labs'][0]
        
        assert physics_lab['weight'] == 50, "Physics Lab should have 50% weight"
        assert chem_lab['weight'] == 30, "Chemistry Lab should have 30% weight"


class TestPredictionWorkflow:
    """Test prediction workflow integration"""
    
    @classmethod
    def setup_class(cls):
        """Initialize database and create test user with history."""
        init_db()
        cls.test_username = "TEST_INT_prediction"
        cls.password = "testpassword123"
        
        # Clean up
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
        add_subject(cls.test_username, "PredTestSubject")
        add_category(cls.test_username, "PredTestSubject", "Assignments", 100)
        
        # Add historical data for predictions
        add_grade(cls.test_username, "PredTestSubject", "Assignments", 2.0, "Past1", 75, 20)
        add_grade(cls.test_username, "PredTestSubject", "Assignments", 3.0, "Past2", 80, 20)
        add_grade(cls.test_username, "PredTestSubject", "Assignments", 4.0, "Past3", 85, 20)
        add_grade(cls.test_username, "PredTestSubject", "Assignments", 5.0, "Past4", 88, 20)
    
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
    
    def test_prediction_to_actual_conversion(self):
        """Test converting a prediction to an actual grade"""
        # Add a prediction
        pred_id = add_grade(
            self.test_username, "PredTestSubject", "Assignments",
            3.5, "Future Assignment", None, 20,
            is_prediction=True, predicted_grade=82
        )
        
        # Verify it's a prediction
        grades = get_all_grades(self.test_username)
        pred = [g for g in grades if g['id'] == pred_id][0]
        assert pred['is_prediction'] is True, "Should be marked as prediction"
        assert pred['grade'] is None, "Should have no actual grade"
        assert pred['predicted_grade'] == 82, "Should have predicted grade"
        
        # Convert to actual grade
        update_grade(
            self.test_username, pred_id, "PredTestSubject", "Assignments",
            3.5, "Future Assignment", 85, 20,
            is_prediction=False, predicted_grade=82
        )
        
        # Verify conversion
        grades_after = get_all_grades(self.test_username)
        converted = [g for g in grades_after if g['id'] == pred_id][0]
        assert converted['is_prediction'] is False, "Should no longer be prediction"
        assert converted['grade'] == 85, "Should have actual grade"
        assert converted['predicted_grade'] == 82, "Should retain predicted grade for accuracy"
        
        # Clean up
        delete_grade(self.test_username, pred_id)


class TestSubjectRenameWorkflow:
    """Test subject rename workflow"""
    
    @classmethod
    def setup_class(cls):
        """Initialize database and create test user."""
        init_db()
        cls.test_username = "TEST_INT_rename"
        cls.password = "testpassword123"
        
        # Clean up
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
    
    def test_rename_cascades_to_all_data(self):
        """Renaming subject updates all related data"""
        old_name = "OldSubjectName"
        new_name = "NewSubjectName"
        
        # Create subject with full data
        add_subject(self.test_username, old_name)
        add_category(self.test_username, old_name, "Tests", 50)
        add_category(self.test_username, old_name, "Labs", 50)
        add_grade(self.test_username, old_name, "Tests", 3.0, "Test 1", 85, 25)
        add_grade(self.test_username, old_name, "Labs", 2.0, "Lab 1", 90, 25)
        
        # Rename
        rename_subject(self.test_username, old_name, new_name)
        
        # Verify subject renamed
        assert get_subject_by_name(self.test_username, old_name) is None
        assert get_subject_by_name(self.test_username, new_name) is not None
        
        # Verify categories under new name
        categories = get_all_categories(self.test_username, new_name)
        assert len(categories) == 2, "Should have 2 categories under new name"
        
        old_categories = get_all_categories(self.test_username, old_name)
        assert len(old_categories) == 0, "Should have no categories under old name"
        
        # Verify grades under new name
        grades = get_all_grades(self.test_username)
        new_name_grades = [g for g in grades if g['subject'] == new_name]
        old_name_grades = [g for g in grades if g['subject'] == old_name]
        
        assert len(new_name_grades) == 2, "Should have 2 grades under new name"
        assert len(old_name_grades) == 0, "Should have no grades under old name"


class TestDeleteCascadeWorkflow:
    """Test cascade delete workflows"""
    
    @classmethod
    def setup_class(cls):
        """Initialize database and create test user."""
        init_db()
        cls.test_username = "TEST_INT_cascade"
        cls.password = "testpassword123"
        
        # Clean up
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
    
    def test_delete_subject_cascades(self):
        """Deleting subject removes all related data"""
        # Create subject with full data
        subject_id = add_subject(self.test_username, "ToDelete")
        add_category(self.test_username, "ToDelete", "Cat1", 50)
        add_category(self.test_username, "ToDelete", "Cat2", 50)
        add_grade(self.test_username, "ToDelete", "Cat1", 2.0, "Assignment 1", 80, 25)
        add_grade(self.test_username, "ToDelete", "Cat2", 3.0, "Assignment 2", 85, 25)
        
        # Verify data exists
        grades_before = get_all_grades(self.test_username)
        categories_before = get_all_categories(self.test_username, "ToDelete")
        
        assert len([g for g in grades_before if g['subject'] == "ToDelete"]) == 2
        assert len(categories_before) == 2
        
        # Delete subject
        delete_subject(self.test_username, subject_id)
        
        # Verify all data deleted
        assert get_subject_by_name(self.test_username, "ToDelete") is None
        
        grades_after = get_all_grades(self.test_username)
        categories_after = get_all_categories(self.test_username, "ToDelete")
        
        assert len([g for g in grades_after if g['subject'] == "ToDelete"]) == 0
        assert len(categories_after) == 0


class TestWeightRecalculationWorkflow:
    """Test weight recalculation in various scenarios"""
    
    @classmethod
    def setup_class(cls):
        """Initialize database and create test user."""
        init_db()
        cls.test_username = "TEST_INT_weights"
        cls.password = "testpassword123"
        
        # Clean up
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
        add_subject(cls.test_username, "WeightTest")
        add_category(cls.test_username, "WeightTest", "Tests", 60)  # 60% for tests
    
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
    
    def test_weights_rebalance_on_add(self):
        """Weights rebalance when adding new assignment"""
        # Add first assignment - gets 60%
        add_grade(self.test_username, "WeightTest", "Tests", 2.0, "Test 1", 80, 0)
        recalculate_and_update_weights(self.test_username, "WeightTest", "Tests")
        
        grades = get_all_grades(self.test_username)
        assert grades[0]['weight'] == 60, "Single test should have 60%"
        
        # Add second assignment - each gets 30%
        add_grade(self.test_username, "WeightTest", "Tests", 3.0, "Test 2", 85, 0)
        recalculate_and_update_weights(self.test_username, "WeightTest", "Tests")
        
        grades = get_all_grades(self.test_username)
        for g in grades:
            assert g['weight'] == 30, f"Each of 2 tests should have 30%, got {g['weight']}"
        
        # Add third assignment - each gets 20%
        add_grade(self.test_username, "WeightTest", "Tests", 4.0, "Test 3", 90, 0)
        recalculate_and_update_weights(self.test_username, "WeightTest", "Tests")
        
        grades = get_all_grades(self.test_username)
        for g in grades:
            assert g['weight'] == 20, f"Each of 3 tests should have 20%, got {g['weight']}"
    
    def test_weights_rebalance_on_delete(self):
        """Weights rebalance when deleting assignment"""
        # Add three assignments
        id1 = add_grade(self.test_username, "WeightTest", "Tests", 2.0, "Test 1", 80, 0)
        id2 = add_grade(self.test_username, "WeightTest", "Tests", 3.0, "Test 2", 85, 0)
        id3 = add_grade(self.test_username, "WeightTest", "Tests", 4.0, "Test 3", 90, 0)
        recalculate_and_update_weights(self.test_username, "WeightTest", "Tests")
        
        # Each has 20%
        grades = get_all_grades(self.test_username)
        for g in grades:
            assert g['weight'] == 20
        
        # Delete one
        delete_grade(self.test_username, id2)
        recalculate_and_update_weights(self.test_username, "WeightTest", "Tests")
        
        # Each remaining has 30%
        grades = get_all_grades(self.test_username)
        assert len(grades) == 2, "Should have 2 remaining"
        for g in grades:
            assert g['weight'] == 30, f"Each of 2 remaining should have 30%, got {g['weight']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
