#!/usr/bin/env python3
"""
Test Subjects - Comprehensive tests for subject management.
Based on comprehensive test plan covering subject CRUD, retire/unretire, and isolation.
"""

import sys
import os
import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

from crud import (
    create_user, add_subject, get_all_subjects, get_subject_by_name,
    delete_subject, rename_subject, get_retired_subjects,
    add_category, add_grade, get_all_grades, get_all_categories
)
from db import _connect, init_db, USERS_TABLE, SUBJECTS_TABLE, TABLE_NAME, CATEGORIES_TABLE


class TestSubjectCreation:
    """Tests for subject creation functionality (SUBJ-001 to SUBJ-004)"""
    
    @classmethod
    def setup_class(cls):
        """Initialize database and create test user."""
        init_db()
        cls.test_username = "TEST_SUBJ_user"
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
    
    def teardown_method(self):
        """Clean up subjects after each test."""
        conn = _connect()
        try:
            curs = conn.cursor()
            curs.execute(f"DELETE FROM {TABLE_NAME} WHERE username = %s", (self.test_username,))
            curs.execute(f"DELETE FROM {CATEGORIES_TABLE} WHERE username = %s", (self.test_username,))
            curs.execute(f"DELETE FROM {SUBJECTS_TABLE} WHERE username = %s", (self.test_username,))
            conn.commit()
        finally:
            curs.close()
            conn.close()
    
    def test_subj_001_create_valid_subject(self):
        """SUBJ-001: Create subject with valid name"""
        subject_name = "Mathematics 101"
        
        subject_id = add_subject(self.test_username, subject_name)
        
        assert subject_id is not None, "Subject creation should return an ID"
        
        # Verify subject exists
        subjects = get_all_subjects(self.test_username)
        subject_names = [s['name'] for s in subjects]
        assert subject_name in subject_names, "Subject should appear in list"
    
    def test_subj_002_create_duplicate_subject(self):
        """SUBJ-002: Attempt to create subject with duplicate name"""
        subject_name = "Duplicate Test"
        
        # Create first subject
        add_subject(self.test_username, subject_name)
        
        # Attempt to create duplicate - should raise exception
        with pytest.raises(Exception):
            add_subject(self.test_username, subject_name)
    
    def test_subj_003_subject_appears_immediately(self):
        """SUBJ-003: Subject appears in navigation immediately after creation"""
        subject_name = "New Subject Immediate"
        
        # Get initial subjects
        initial_subjects = get_all_subjects(self.test_username)
        initial_count = len(initial_subjects)
        
        # Create subject
        add_subject(self.test_username, subject_name)
        
        # Get subjects again - should include new subject
        new_subjects = get_all_subjects(self.test_username)
        assert len(new_subjects) == initial_count + 1, "Subject count should increase by 1"
        
        new_subject_names = [s['name'] for s in new_subjects]
        assert subject_name in new_subject_names, "New subject should be in list"
    
    def test_subj_004_subject_with_special_characters(self):
        """SUBJ-004: Create subject with special characters in name"""
        subject_name = "CS 101 - Intro & Basics!"
        
        subject_id = add_subject(self.test_username, subject_name)
        assert subject_id is not None, "Should create subject with special characters"
        
        # Verify it can be retrieved
        subject = get_subject_by_name(self.test_username, subject_name)
        assert subject is not None, "Should retrieve subject with special characters"
        assert subject['name'] == subject_name, "Name should match exactly"


class TestSubjectRetrieval:
    """Tests for subject retrieval functionality (SUBJ-005 to SUBJ-007)"""
    
    @classmethod
    def setup_class(cls):
        """Initialize database and create test user with subjects."""
        init_db()
        cls.test_username = "TEST_SUBJ_retrieval_user"
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
        
        # Create test subjects
        cls.subject1_name = "Physics"
        cls.subject2_name = "Chemistry"
        cls.subject3_name = "Biology"
        
        cls.subject1_id = add_subject(cls.test_username, cls.subject1_name)
        cls.subject2_id = add_subject(cls.test_username, cls.subject2_name)
        cls.subject3_id = add_subject(cls.test_username, cls.subject3_name)
    
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
    
    def test_subj_005_get_all_subjects(self):
        """SUBJ-005: Retrieve all subjects for user"""
        subjects = get_all_subjects(self.test_username)
        
        assert len(subjects) >= 3, "Should have at least 3 subjects"
        
        subject_names = [s['name'] for s in subjects]
        assert self.subject1_name in subject_names
        assert self.subject2_name in subject_names
        assert self.subject3_name in subject_names
    
    def test_subj_006_get_subject_by_name(self):
        """SUBJ-006: Retrieve specific subject by name"""
        subject = get_subject_by_name(self.test_username, self.subject1_name)
        
        assert subject is not None, "Should find subject by name"
        assert subject['name'] == self.subject1_name, "Name should match"
        assert subject['id'] == self.subject1_id, "ID should match"
    
    def test_subj_007_get_nonexistent_subject(self):
        """SUBJ-007: Attempt to retrieve non-existent subject"""
        subject = get_subject_by_name(self.test_username, "NonexistentSubject12345")
        
        assert subject is None, "Should return None for non-existent subject"
    
    def test_subj_subjects_sorted_alphabetically(self):
        """Subjects should be returned in alphabetical order"""
        subjects = get_all_subjects(self.test_username)
        subject_names = [s['name'] for s in subjects]
        
        # Check they are sorted
        sorted_names = sorted(subject_names)
        assert subject_names == sorted_names, "Subjects should be sorted alphabetically"


class TestSubjectDeletion:
    """Tests for subject deletion functionality (SUBJ-008 to SUBJ-010)"""
    
    @classmethod
    def setup_class(cls):
        """Initialize database and create test user."""
        init_db()
        cls.test_username = "TEST_SUBJ_delete_user"
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
    
    def teardown_method(self):
        """Clean up after each test."""
        conn = _connect()
        try:
            curs = conn.cursor()
            curs.execute(f"DELETE FROM {TABLE_NAME} WHERE username = %s", (self.test_username,))
            curs.execute(f"DELETE FROM {CATEGORIES_TABLE} WHERE username = %s", (self.test_username,))
            curs.execute(f"DELETE FROM {SUBJECTS_TABLE} WHERE username = %s", (self.test_username,))
            conn.commit()
        finally:
            curs.close()
            conn.close()
    
    def test_subj_008_delete_empty_subject(self):
        """SUBJ-008: Delete subject with no assignments"""
        subject_name = "EmptySubject"
        subject_id = add_subject(self.test_username, subject_name)
        
        # Verify it exists
        assert get_subject_by_name(self.test_username, subject_name) is not None
        
        # Delete it
        rows_deleted = delete_subject(self.test_username, subject_id)
        
        assert rows_deleted > 0, "Should delete at least one row"
        
        # Verify it's gone
        assert get_subject_by_name(self.test_username, subject_name) is None, "Subject should be deleted"
    
    def test_subj_009_delete_subject_with_data(self):
        """SUBJ-009: Delete subject cascades to categories and assignments"""
        subject_name = "SubjectWithData"
        subject_id = add_subject(self.test_username, subject_name)
        
        # Add category
        category_id = add_category(self.test_username, subject_name, "TestCategory", 100)
        
        # Add assignment
        grade_id = add_grade(self.test_username, subject_name, "TestCategory", 2.0, "Test Assignment", 85, 100)
        
        # Verify data exists
        grades = get_all_grades(self.test_username)
        assert any(g['subject'] == subject_name for g in grades), "Assignment should exist"
        
        categories = get_all_categories(self.test_username, subject_name)
        assert len(categories) > 0, "Category should exist"
        
        # Delete subject
        delete_subject(self.test_username, subject_id)
        
        # Verify subject is gone
        assert get_subject_by_name(self.test_username, subject_name) is None, "Subject should be deleted"
        
        # Verify categories are gone
        categories_after = get_all_categories(self.test_username, subject_name)
        assert len(categories_after) == 0, "Categories should be cascade deleted"
        
        # Verify assignments are gone
        grades_after = get_all_grades(self.test_username)
        assert not any(g['subject'] == subject_name for g in grades_after), "Assignments should be cascade deleted"
    
    def test_subj_010_delete_nonexistent_subject(self):
        """SUBJ-010: Attempt to delete non-existent subject"""
        rows_deleted = delete_subject(self.test_username, 999999)
        
        assert rows_deleted == 0, "Should return 0 for non-existent subject"


class TestSubjectRename:
    """Tests for subject rename functionality (SUBJ-011 to SUBJ-012)"""
    
    @classmethod
    def setup_class(cls):
        """Initialize database and create test user."""
        init_db()
        cls.test_username = "TEST_SUBJ_rename_user"
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
    
    def teardown_method(self):
        """Clean up after each test."""
        conn = _connect()
        try:
            curs = conn.cursor()
            curs.execute(f"DELETE FROM {TABLE_NAME} WHERE username = %s", (self.test_username,))
            curs.execute(f"DELETE FROM {CATEGORIES_TABLE} WHERE username = %s", (self.test_username,))
            curs.execute(f"DELETE FROM {SUBJECTS_TABLE} WHERE username = %s", (self.test_username,))
            conn.commit()
        finally:
            curs.close()
            conn.close()
    
    def test_subj_011_rename_subject(self):
        """SUBJ-011: Rename subject updates all related data"""
        old_name = "OldSubjectName"
        new_name = "NewSubjectName"
        
        # Create subject with category and assignment
        add_subject(self.test_username, old_name)
        add_category(self.test_username, old_name, "TestCategory", 100)
        add_grade(self.test_username, old_name, "TestCategory", 2.0, "Test Assignment", 85, 100)
        
        # Rename
        result = rename_subject(self.test_username, old_name, new_name)
        assert result is True, "Rename should succeed"
        
        # Verify old name is gone
        assert get_subject_by_name(self.test_username, old_name) is None, "Old name should not exist"
        
        # Verify new name exists
        subject = get_subject_by_name(self.test_username, new_name)
        assert subject is not None, "New name should exist"
        
        # Verify categories updated
        categories = get_all_categories(self.test_username, new_name)
        assert len(categories) > 0, "Categories should be under new name"
        
        # Verify assignments updated
        grades = get_all_grades(self.test_username)
        assignment_subjects = [g['subject'] for g in grades]
        assert new_name in assignment_subjects, "Assignments should be under new name"
        assert old_name not in assignment_subjects, "No assignments should be under old name"
    
    def test_subj_012_rename_to_existing_name(self):
        """SUBJ-012: Cannot rename subject to existing name"""
        name1 = "SubjectOne"
        name2 = "SubjectTwo"
        
        add_subject(self.test_username, name1)
        add_subject(self.test_username, name2)
        
        # Attempt to rename name1 to name2 - should fail
        with pytest.raises(ValueError):
            rename_subject(self.test_username, name1, name2)


class TestSubjectRetire:
    """Tests for subject retire/unretire functionality"""
    
    @classmethod
    def setup_class(cls):
        """Initialize database and create test user."""
        init_db()
        cls.test_username = "TEST_SUBJ_retire_user"
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
    
    def teardown_method(self):
        """Clean up after each test."""
        conn = _connect()
        try:
            curs = conn.cursor()
            curs.execute(f"DELETE FROM {TABLE_NAME} WHERE username = %s", (self.test_username,))
            curs.execute(f"DELETE FROM {CATEGORIES_TABLE} WHERE username = %s", (self.test_username,))
            curs.execute(f"DELETE FROM {SUBJECTS_TABLE} WHERE username = %s", (self.test_username,))
            conn.commit()
        finally:
            curs.close()
            conn.close()
    
    def test_retire_subject(self):
        """Retired subjects are excluded from main navigation"""
        subject_name = "SubjectToRetire"
        subject_id = add_subject(self.test_username, subject_name)
        
        # Initially should appear in active subjects
        active_subjects = get_all_subjects(self.test_username, include_retired=False)
        assert any(s['name'] == subject_name for s in active_subjects), "Subject should be active initially"
        
        # Retire the subject
        conn = _connect()
        try:
            curs = conn.cursor()
            curs.execute(f"UPDATE {SUBJECTS_TABLE} SET is_retired = TRUE WHERE id = %s", (subject_id,))
            conn.commit()
        finally:
            curs.close()
            conn.close()
        
        # Should NOT appear in active subjects
        active_subjects_after = get_all_subjects(self.test_username, include_retired=False)
        assert not any(s['name'] == subject_name for s in active_subjects_after), "Retired subject should not appear in active list"
        
        # Should appear in retired subjects
        retired_subjects = get_retired_subjects(self.test_username)
        assert any(s['name'] == subject_name for s in retired_subjects), "Subject should appear in retired list"
    
    def test_unretire_subject(self):
        """Unretired subjects return to main navigation"""
        subject_name = "SubjectToUnretire"
        subject_id = add_subject(self.test_username, subject_name)
        
        # Retire then unretire
        conn = _connect()
        try:
            curs = conn.cursor()
            curs.execute(f"UPDATE {SUBJECTS_TABLE} SET is_retired = TRUE WHERE id = %s", (subject_id,))
            conn.commit()
            
            # Verify it's retired
            retired = get_retired_subjects(self.test_username)
            assert any(s['name'] == subject_name for s in retired), "Subject should be retired"
            
            # Unretire
            curs.execute(f"UPDATE {SUBJECTS_TABLE} SET is_retired = FALSE WHERE id = %s", (subject_id,))
            conn.commit()
        finally:
            curs.close()
            conn.close()
        
        # Should appear in active subjects again
        active_subjects = get_all_subjects(self.test_username, include_retired=False)
        assert any(s['name'] == subject_name for s in active_subjects), "Unretired subject should be active"
        
        # Should NOT appear in retired subjects
        retired_after = get_retired_subjects(self.test_username)
        assert not any(s['name'] == subject_name for s in retired_after), "Unretired subject should not be in retired list"
    
    def test_retired_subject_data_preserved(self):
        """Retiring a subject preserves its data"""
        subject_name = "DataPreservationTest"
        subject_id = add_subject(self.test_username, subject_name)
        
        # Add category and assignment
        add_category(self.test_username, subject_name, "TestCategory", 100)
        add_grade(self.test_username, subject_name, "TestCategory", 2.0, "Test Assignment", 85, 100)
        
        # Retire
        conn = _connect()
        try:
            curs = conn.cursor()
            curs.execute(f"UPDATE {SUBJECTS_TABLE} SET is_retired = TRUE WHERE id = %s", (subject_id,))
            conn.commit()
        finally:
            curs.close()
            conn.close()
        
        # Data should still exist
        grades = get_all_grades(self.test_username)
        assert any(g['subject'] == subject_name for g in grades), "Assignment data should be preserved"
        
        categories = get_all_categories(self.test_username, subject_name)
        assert len(categories) > 0, "Category data should be preserved"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
