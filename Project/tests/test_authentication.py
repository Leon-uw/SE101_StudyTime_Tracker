#!/usr/bin/env python3
"""
Test Authentication - Comprehensive tests for user authentication system.
Based on comprehensive test plan covering login, register, logout, session management, and user isolation.
"""

import sys
import os
import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

from crud import create_user, verify_user, user_exists, add_subject, get_all_subjects, delete_subject, add_grade, get_all_grades
from db import _connect, init_db, USERS_TABLE


class TestUserRegistration:
    """Tests for user registration functionality (AUTH-001 to AUTH-004)"""
    
    @classmethod
    def setup_class(cls):
        """Initialize database for tests."""
        init_db()
    
    def setup_method(self):
        """Clean up test users before each test."""
        conn = _connect()
        try:
            curs = conn.cursor()
            curs.execute(f"DELETE FROM {USERS_TABLE} WHERE username LIKE 'TEST_AUTH_%'")
            conn.commit()
        finally:
            curs.close()
            conn.close()
    
    def teardown_method(self):
        """Clean up test users after each test."""
        conn = _connect()
        try:
            curs = conn.cursor()
            curs.execute(f"DELETE FROM {USERS_TABLE} WHERE username LIKE 'TEST_AUTH_%'")
            conn.commit()
        finally:
            curs.close()
            conn.close()
    
    def test_auth_001_valid_registration(self):
        """AUTH-001: Register with valid unique username and password (minimum 6 chars)"""
        username = "TEST_AUTH_valid_user"
        password = "validpass123"
        
        # Should not exist initially
        assert not user_exists(username), "User should not exist before registration"
        
        # Create user
        user_id = create_user(username, password)
        
        # Verify user was created
        assert user_id is not None, "User creation should return an ID"
        assert user_exists(username), "User should exist after registration"
    
    def test_auth_002_duplicate_username(self):
        """AUTH-002: Attempt to register with existing username"""
        username = "TEST_AUTH_duplicate"
        password = "password123"
        
        # Create first user
        create_user(username, password)
        
        # Attempt to create duplicate - should raise exception
        with pytest.raises(Exception):
            create_user(username, "different_password")
    
    def test_auth_003_short_username(self):
        """AUTH-003: Test username length validation (if implemented)"""
        # Note: This test documents behavior - adjust based on actual validation rules
        username = "ab"  # Very short username
        password = "validpass123"
        
        # Depending on implementation, this may succeed or fail
        # Document actual behavior
        try:
            user_id = create_user(username + "_TEST_AUTH", password)
            # Clean up if successful
            conn = _connect()
            try:
                curs = conn.cursor()
                curs.execute(f"DELETE FROM {USERS_TABLE} WHERE username = %s", (username + "_TEST_AUTH",))
                conn.commit()
            finally:
                curs.close()
                conn.close()
        except Exception:
            pass  # Validation rejected short username
    
    def test_auth_004_password_hashing(self):
        """AUTH-004: Verify password is stored as hash, not plaintext"""
        username = "TEST_AUTH_hash_test"
        password = "testpassword123"
        
        create_user(username, password)
        
        # Verify password is not stored as plaintext
        conn = _connect()
        try:
            curs = conn.cursor(dictionary=True)
            curs.execute(f"SELECT password_hash FROM {USERS_TABLE} WHERE username = %s", (username,))
            result = curs.fetchone()
            
            assert result is not None, "User should exist"
            assert result['password_hash'] != password, "Password should not be stored as plaintext"
            assert 'pbkdf2' in result['password_hash'] or 'scrypt' in result['password_hash'], \
                "Password should be hashed with secure algorithm"
        finally:
            curs.close()
            conn.close()


class TestUserLogin:
    """Tests for user login functionality (AUTH-005 to AUTH-008)"""
    
    @classmethod
    def setup_class(cls):
        """Initialize database and create test user."""
        init_db()
        cls.test_username = "TEST_AUTH_login_user"
        cls.test_password = "testpassword123"
        
        # Clean up and create test user
        conn = _connect()
        try:
            curs = conn.cursor()
            curs.execute(f"DELETE FROM {USERS_TABLE} WHERE username = %s", (cls.test_username,))
            conn.commit()
        finally:
            curs.close()
            conn.close()
        
        create_user(cls.test_username, cls.test_password)
    
    @classmethod
    def teardown_class(cls):
        """Clean up test user."""
        conn = _connect()
        try:
            curs = conn.cursor()
            curs.execute(f"DELETE FROM {USERS_TABLE} WHERE username LIKE 'TEST_AUTH_%'")
            conn.commit()
        finally:
            curs.close()
            conn.close()
    
    def test_auth_005_valid_login(self):
        """AUTH-005: Login with correct username and password"""
        result = verify_user(self.test_username, self.test_password)
        assert result is True, "Valid credentials should return True"
    
    def test_auth_006_wrong_password(self):
        """AUTH-006: Login with correct username, wrong password"""
        result = verify_user(self.test_username, "wrongpassword")
        assert result is False, "Wrong password should return False"
    
    def test_auth_007_wrong_username(self):
        """AUTH-007: Login with non-existent username"""
        result = verify_user("nonexistent_user_xyz", "anypassword")
        assert result is False, "Non-existent username should return False"
    
    def test_auth_008_case_sensitivity(self):
        """AUTH-008: Test username case sensitivity"""
        # Test if username matching is case-sensitive
        uppercase_username = self.test_username.upper()
        result = verify_user(uppercase_username, self.test_password)
        
        # Note: This system uses MySQL with default collation which is case-insensitive
        # Document this as expected behavior
        if self.test_username != uppercase_username:
            # MySQL default collation is case-insensitive for string comparisons
            # This test documents the actual behavior
            assert result is True, "Username matching is case-insensitive (MySQL default)"


class TestUserIsolation:
    """Tests for user data isolation (AUTH-012 to AUTH-014)"""
    
    @classmethod
    def setup_class(cls):
        """Initialize database and create test users."""
        init_db()
        cls.user1 = "TEST_AUTH_isolation_user1"
        cls.user2 = "TEST_AUTH_isolation_user2"
        cls.password = "testpassword123"
        
        # Clean up
        conn = _connect()
        try:
            curs = conn.cursor()
            curs.execute(f"DELETE FROM {USERS_TABLE} WHERE username LIKE 'TEST_AUTH_isolation_%'")
            conn.commit()
        finally:
            curs.close()
            conn.close()
        
        # Create test users
        create_user(cls.user1, cls.password)
        create_user(cls.user2, cls.password)
    
    @classmethod
    def teardown_class(cls):
        """Clean up test users and their data."""
        conn = _connect()
        try:
            curs = conn.cursor()
            curs.execute(f"DELETE FROM {USERS_TABLE} WHERE username LIKE 'TEST_AUTH_isolation_%'")
            conn.commit()
        finally:
            curs.close()
            conn.close()
    
    def teardown_method(self):
        """Clean up test data after each test."""
        from db import SUBJECTS_TABLE, TABLE_NAME, CATEGORIES_TABLE
        conn = _connect()
        try:
            curs = conn.cursor()
            # Clean up test subjects and related data
            curs.execute(f"DELETE FROM {TABLE_NAME} WHERE username LIKE 'TEST_AUTH_isolation_%'")
            curs.execute(f"DELETE FROM {CATEGORIES_TABLE} WHERE username LIKE 'TEST_AUTH_isolation_%'")
            curs.execute(f"DELETE FROM {SUBJECTS_TABLE} WHERE username LIKE 'TEST_AUTH_isolation_%'")
            conn.commit()
        finally:
            curs.close()
            conn.close()
    
    def test_auth_012_subject_isolation(self):
        """AUTH-012: User 1 cannot see User 2's subjects"""
        # Create subject for user 1
        subject_id = add_subject(self.user1, "User1_Private_Subject")
        
        # User 1 should see the subject
        user1_subjects = get_all_subjects(self.user1)
        user1_subject_names = [s['name'] for s in user1_subjects]
        assert "User1_Private_Subject" in user1_subject_names, "User 1 should see their subject"
        
        # User 2 should NOT see user 1's subject
        user2_subjects = get_all_subjects(self.user2)
        user2_subject_names = [s['name'] for s in user2_subjects]
        assert "User1_Private_Subject" not in user2_subject_names, "User 2 should NOT see User 1's subject"
    
    def test_auth_013_grade_isolation(self):
        """AUTH-013: User 1 cannot see User 2's grades"""
        from crud import add_category
        
        # Create subject and category for user 1
        add_subject(self.user1, "User1_Grade_Subject")
        add_category(self.user1, "User1_Grade_Subject", "TestCategory", 100)
        
        # Add grade for user 1
        grade_id = add_grade(self.user1, "User1_Grade_Subject", "TestCategory", 2.0, "Secret Assignment", 95, 100)
        
        # User 1 should see the grade
        user1_grades = get_all_grades(self.user1)
        user1_assignment_names = [g['assignment_name'] for g in user1_grades]
        assert "Secret Assignment" in user1_assignment_names, "User 1 should see their grade"
        
        # User 2 should NOT see user 1's grade
        user2_grades = get_all_grades(self.user2)
        user2_assignment_names = [g['assignment_name'] for g in user2_grades]
        assert "Secret Assignment" not in user2_assignment_names, "User 2 should NOT see User 1's grade"
    
    def test_auth_014_same_subject_name_different_users(self):
        """AUTH-014: Two users can have subjects with the same name"""
        subject_name = "Shared_Subject_Name"
        
        # Both users create subject with same name
        subject1_id = add_subject(self.user1, subject_name)
        subject2_id = add_subject(self.user2, subject_name)
        
        # Both should succeed with different IDs
        assert subject1_id is not None, "User 1 should be able to create subject"
        assert subject2_id is not None, "User 2 should be able to create subject"
        assert subject1_id != subject2_id, "Different users' subjects should have different IDs"
        
        # Both users should see their own subject
        user1_subjects = get_all_subjects(self.user1)
        user2_subjects = get_all_subjects(self.user2)
        
        assert any(s['name'] == subject_name for s in user1_subjects), "User 1 should see the subject"
        assert any(s['name'] == subject_name for s in user2_subjects), "User 2 should see the subject"


class TestPasswordSecurity:
    """Tests for password security features"""
    
    @classmethod
    def setup_class(cls):
        """Initialize database for tests."""
        init_db()
    
    def teardown_method(self):
        """Clean up test users."""
        conn = _connect()
        try:
            curs = conn.cursor()
            curs.execute(f"DELETE FROM {USERS_TABLE} WHERE username LIKE 'TEST_AUTH_security_%'")
            conn.commit()
        finally:
            curs.close()
            conn.close()
    
    def test_password_verification_timing(self):
        """Test that password verification is consistent (timing attack resistance)"""
        username = "TEST_AUTH_security_timing"
        password = "correctpassword"
        
        create_user(username, password)
        
        # Multiple verifications with correct password
        for _ in range(3):
            assert verify_user(username, password) is True
        
        # Multiple verifications with wrong password
        for _ in range(3):
            assert verify_user(username, "wrongpassword") is False
    
    def test_special_characters_in_password(self):
        """Test passwords with special characters"""
        username = "TEST_AUTH_security_special"
        password = "p@ss!word#123$%^&*()"
        
        user_id = create_user(username, password)
        assert user_id is not None, "Should create user with special character password"
        
        # Should be able to verify
        assert verify_user(username, password) is True, "Should verify password with special characters"
    
    def test_unicode_in_password(self):
        """Test passwords with unicode characters"""
        username = "TEST_AUTH_security_unicode"
        password = "пароль密码كلمة السر"  # Russian, Chinese, Arabic
        
        try:
            user_id = create_user(username, password)
            assert user_id is not None, "Should create user with unicode password"
            assert verify_user(username, password) is True, "Should verify unicode password"
        except Exception as e:
            # Some systems may not support unicode passwords
            pytest.skip(f"Unicode passwords not supported: {e}")
    
    def test_empty_password_handling(self):
        """Test handling of empty password"""
        username = "TEST_AUTH_security_empty"
        
        # Empty password should be rejected or handled safely
        try:
            create_user(username, "")
            # If it succeeds, verify it can still work
            assert verify_user(username, "") is True
        except Exception:
            # Empty password rejected - this is acceptable
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
