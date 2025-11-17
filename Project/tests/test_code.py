import pytest
import logging
import sys
import os

# Add the parent directory to the path so we can import src modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import connect2DB
from src import crud
from src.db import init_db, _connect, TABLE_NAME
from unittest.mock import patch
import mysql.connector

class Test_connection:
    #success
    def test_connection_success(self):
        logging.info("Testing successful connection")
        connection, curs = connect2DB.connection()
        assert connection is not None, "Should successfully return connection"
        assert curs is not None, "Should have a cursor ready"
        curs.close()
        connection.close()
    #success w/cursor
    def test_connection_creating_cursor(self):
        logging.info("Testing successful cursor creation")
        connection, curs = connect2DB.connection()
        assert curs is not None, "should have a cursor ready to go"
        assert hasattr(curs, 'execute'), "Should successfully return a cursor"
        #assert curs is not None, "Should have a cursor ready"
        curs.close()
        connection.close()
    #testing successful closure
    def test_connection_close(self):
        logging.info("Testing if connection closes")
        connection, curs = connect2DB.connection()
        assert connection.is_connected(), "Should have the connection up now"
        curs.close()
        connection.close()
        assert not connection.is_connected(), "Should successfully close connection"
    #testing failure handling
    @patch('src.connect2DB.mysql.connector.connect')
    def test_connection_failure(self, mock_connect):
        logging.info("Testing connection issues")
        mock_connect.side_effect = Exception("Connection failed!")

        with pytest.raises(Exception):
            connect2DB.connection()
class Test_CRUD_Operations:
    """Test cases for CRUD operations (add_grade and update_grade)"""
    
    @classmethod
    def setup_class(cls):
        """Set up test database and table before running tests"""
        logging.info("Setting up test database")
        try:
            init_db()
            logging.info("Test database initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize test database: {e}")
            raise
    
    def setup_method(self):
        """Clean up test data before each test"""
        logging.info("Cleaning up test data")
        conn = _connect()
        try:
            cur = conn.cursor()
            cur.execute(f"DELETE FROM {TABLE_NAME} WHERE Subject LIKE 'TEST_%'")
            conn.commit()
        except Exception as e:
            logging.warning(f"Cleanup failed: {e}")
        finally:
            cur.close()
            conn.close()
    
    def test_add_grade_success(self):
        """Test successful grade addition"""
        logging.info("Testing successful grade addition")
        
        # Test data
        subject = "TEST_Math"
        study_time = 2.5
        assignment_name = "Test Assignment 1"
        grade = 85
        weight = 10
        
        # Add grade
        grade_id = crud.add_grade(subject, study_time, assignment_name, grade, weight)
        
        # Verify grade was added
        assert grade_id is not None, "Should return a grade ID"
        assert isinstance(grade_id, int), "Grade ID should be an integer"
        
        # Verify data in database
        conn = _connect()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(f"SELECT * FROM {TABLE_NAME} WHERE id = %s", (grade_id,))
            result = cur.fetchone()
            
            assert result is not None, "Grade should be found in database"
            assert result['Subject'] == subject, "Subject should match"
            assert result['StudyTime'] == study_time, "Study time should match"
            assert result['AssignmentName'] == assignment_name, "Assignment name should match"
            assert result['Grade'] == grade, "Grade should match"
            assert result['Weight'] == weight, "Weight should match"
        finally:
            cur.close()
            conn.close()
    
    def test_add_grade_with_null_grade(self):
        """Test adding grade with NULL grade value"""
        logging.info("Testing grade addition with NULL grade")
        
        # Test data with None grade
        subject = "TEST_Science"
        study_time = 1.5
        assignment_name = "Test Lab Report"
        grade = None
        weight = 15
        
        # Add grade
        grade_id = crud.add_grade(subject, study_time, assignment_name, grade, weight)
        
        # Verify grade was added
        assert grade_id is not None, "Should return a grade ID"
        
        # Verify data in database
        conn = _connect()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(f"SELECT * FROM {TABLE_NAME} WHERE id = %s", (grade_id,))
            result = cur.fetchone()
            
            assert result is not None, "Grade should be found in database"
            assert result['Grade'] is None, "Grade should be NULL"
        finally:
            cur.close()
            conn.close()
    
    def test_add_grade_database_error(self):
        """Test add_grade handling database errors"""
        logging.info("Testing add_grade database error handling")
        
        with patch('src.crud._connect') as mock_connect:
            mock_conn = mock_connect.return_value
            mock_cur = mock_conn.cursor.return_value
            mock_cur.execute.side_effect = mysql.connector.Error("Database error")
            
            with pytest.raises(mysql.connector.Error):
                crud.add_grade("TEST_Subject", 1.0, "Test", 90, 10)
    
    def test_update_grade_success(self):
        """Test successful grade update"""
        logging.info("Testing successful grade update")
        
        # First add a grade to update
        original_subject = "TEST_History"
        original_study_time = 3.0
        original_assignment = "Original Assignment"
        original_grade = 75
        original_weight = 20
        
        grade_id = crud.add_grade(original_subject, original_study_time, 
                                original_assignment, original_grade, original_weight)
        
        # Update the grade
        new_subject = "TEST_History_Updated"
        new_study_time = 3.5
        new_assignment = "Updated Assignment"
        new_grade = 85
        new_weight = 25
        
        rows_affected = crud.update_grade(grade_id, new_subject, new_study_time, 
                                        new_assignment, new_grade, new_weight)
        
        # Verify update was successful
        assert rows_affected == 1, "Should update exactly one row"
        
        # Verify updated data in database
        conn = _connect()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(f"SELECT * FROM {TABLE_NAME} WHERE id = %s", (grade_id,))
            result = cur.fetchone()
            
            assert result is not None, "Updated grade should be found"
            assert result['Subject'] == new_subject, "Subject should be updated"
            assert result['StudyTime'] == new_study_time, "Study time should be updated"
            assert result['AssignmentName'] == new_assignment, "Assignment name should be updated"
            assert result['Grade'] == new_grade, "Grade should be updated"
            assert result['Weight'] == new_weight, "Weight should be updated"
        finally:
            cur.close()
            conn.close()
    
    def test_update_grade_nonexistent_id(self):
        """Test updating grade with non-existent ID"""
        logging.info("Testing update with non-existent ID")
        
        # Try to update non-existent grade
        rows_affected = crud.update_grade(99999, "TEST_Subject", 1.0, "Test", 90, 10)
        
        # Should return 0 rows affected
        assert rows_affected == 0, "Should return 0 for non-existent ID"
    
    def test_update_grade_database_error(self):
        """Test update_grade handling database errors"""
        logging.info("Testing update_grade database error handling")
        
        with patch('src.crud._connect') as mock_connect:
            mock_conn = mock_connect.return_value
            mock_cur = mock_conn.cursor.return_value
            mock_cur.execute.side_effect = mysql.connector.Error("Database error")
            
            with pytest.raises(mysql.connector.Error):
                crud.update_grade(1, "TEST_Subject", 1.0, "Test", 90, 10)
    
    def test_get_all_grades(self):
        """Test retrieving all grades"""
        logging.info("Testing get_all_grades function")
        
        # Add some test data
        grade_id_1 = crud.add_grade("TEST_Math", 2.0, "Test 1", 85, 10)
        grade_id_2 = crud.add_grade("TEST_Science", 1.5, "Test 2", 90, 15)
        
        # Get all grades
        all_grades = crud.get_all_grades()
        
        # Verify results
        assert isinstance(all_grades, list), "Should return a list"
        
        # Find our test grades
        test_grades = [g for g in all_grades if g['Subject'].startswith('TEST_')]
        assert len(test_grades) >= 2, "Should find at least 2 test grades"
        
        # Verify structure of returned data
        for grade in test_grades:
            assert 'id' in grade, "Should have id field"
            assert 'Subject' in grade, "Should have Subject field"
            assert 'StudyTime' in grade, "Should have StudyTime field"
            assert 'AssignmentName' in grade, "Should have AssignmentName field"
            assert 'Grade' in grade, "Should have Grade field (can be None)"
            assert 'Weight' in grade, "Should have Weight field"

    def test_delete_grade_success(self):
        """Test successful grade deletion"""
        logging.info("Testing successful grade deletion")

        # First add a grade we can delete
        subject = "TEST_Delete_Subject"
        study_time = 2.0
        assignment_name = "Delete Me"
        grade = 70
        weight = 5

        grade_id = crud.add_grade(subject, study_time, assignment_name, grade, weight)

        # Sanity check: make sure it exists before deleting
        conn = _connect()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(f"SELECT * FROM {TABLE_NAME} WHERE id = %s", (grade_id,))
            result = cur.fetchone()
            assert result is not None, "Grade should exist before deletion"
        finally:
            cur.close()
            conn.close()

        # Act: delete the grade
        rows_deleted = crud.delete_grade(grade_id)

        # Assert
        assert rows_deleted == 1, "Should delete exactly one row"

        # Verify it's actually gone
        conn = _connect()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(f"SELECT * FROM {TABLE_NAME} WHERE id = %s", (grade_id,))
            result = cur.fetchone()
            assert result is None, "Grade should no longer exist after deletion"
        finally:
            cur.close()
            conn.close()

    def test_delete_grade_nonexistent_id(self):
        """Test deleting grade with non-existent ID"""
        logging.info("Testing delete with non-existent ID")

        # Choose an ID that shouldn't exist (cleanup already wipes TEST_ rows)
        nonexistent_id = 999999

        rows_deleted = crud.delete_grade(nonexistent_id)

        # Should not delete anything
        assert rows_deleted == 0, "Should return 0 for non-existent ID"

    def test_delete_grade_database_error(self):
        """Test delete_grade handling database errors"""
        logging.info("Testing delete_grade database error handling")

        with patch('src.crud._connect') as mock_connect:
            mock_conn = mock_connect.return_value
            mock_cur = mock_conn.cursor.return_value
            mock_cur.execute.side_effect = mysql.connector.Error("Database error")

            with pytest.raises(mysql.connector.Error):
                crud.delete_grade(1)




