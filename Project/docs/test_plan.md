# Test Plan - Study Time Tracker Application

**Project:** SE101 Team 21 - Study Time Tracker  
**Version:** 1.0  
**Date:** November 12, 2025

## 1. Overview

This test plan documents the implemented tests for the Study Time Tracker application's database connectivity and CRUD operations. The application uses Flask for the web framework and MySQL for data persistence.

## 2. Test Objectives

- Verify database connectivity and basic connection operations
- Test CRUD operations (Create, Read, Update) for grade records
- Ensure proper error handling for database operations
- Confirm MySQL integration works correctly

## 3. Test Environment

### 3.1 Setup Requirements
- **Python Version:** 3.14.0
- **Virtual Environment:** `.venv` in project root
- **Database:** MySQL (remote server: `riku.shoshin.uwaterloo.ca`)
- **Testing Framework:** pytest 9.0.1
- **Dependencies:** Flask, mysql-connector-python, python-dotenv

### 3.2 Test Data
- Test records use `TEST_` prefix in Subject field for easy identification
- Cleanup performed before each test to ensure isolation
- Database table: `{DB_USER}_grades` (e.g., `root_grades`)

## 4. Test Categories

### 4.1 Database Connection Tests (`Test_connection`)

#### 4.1.1 Connection Success Test
- **Objective:** Verify successful database connection
- **Test Method:** `test_connection_success()`
- **Expected Result:** Returns valid connection and cursor objects
- **Pass Criteria:** `connection is not None` and `curs is not None`

#### 4.1.2 Cursor Creation Test
- **Objective:** Validate cursor functionality
- **Test Method:** `test_connection_creating_cursor()`
- **Expected Result:** Cursor has `execute` method available
- **Pass Criteria:** `hasattr(curs, 'execute')` returns True

#### 4.1.3 Connection Closure Test
- **Objective:** Ensure proper connection cleanup
- **Test Method:** `test_connection_close()`
- **Expected Result:** Connection status changes from connected to disconnected
- **Pass Criteria:** `connection.is_connected()` returns False after close

#### 4.1.4 Connection Failure Handling Test
- **Objective:** Test error handling for connection failures
- **Test Method:** `test_connection_failure()`
- **Expected Result:** Exception raised when connection fails
- **Pass Criteria:** `pytest.raises(Exception)` catches connection error

### 4.2 CRUD Operations Tests (`Test_CRUD_Operations`)

#### 4.2.1 Grade Addition Tests

##### 4.2.1.1 Successful Grade Addition
- **Objective:** Test adding complete grade records
- **Test Method:** `test_add_grade_success()`
- **Test Data:** 
  - Subject: "TEST_Math"
  - Study Time: 2.5 hours
  - Assignment: "Test Assignment 1"
  - Grade: 85
  - Weight: 10
- **Expected Result:** Returns valid grade ID and data persists in database
- **Pass Criteria:** 
  - `grade_id is not None`
  - `isinstance(grade_id, int)`
  - Database record matches input data

##### 4.2.1.2 Grade Addition with NULL Grade
- **Objective:** Test adding records with no grade (incomplete assignments)
- **Test Method:** `test_add_grade_with_null_grade()`
- **Test Data:** Similar to above but `grade = None`
- **Expected Result:** Record added with NULL grade value
- **Pass Criteria:** Database record has `Grade IS NULL`

##### 4.2.1.3 Database Error Handling
- **Objective:** Test error handling during grade addition
- **Test Method:** `test_add_grade_database_error()`
- **Mock Condition:** Database connection failure
- **Expected Result:** `mysql.connector.Error` exception raised
- **Pass Criteria:** Exception properly propagated

#### 4.2.2 Grade Update Tests

##### 4.2.2.1 Successful Grade Update
- **Objective:** Test updating existing grade records
- **Test Method:** `test_update_grade_success()`
- **Process:**
  1. Add initial grade record
  2. Update all fields with new values
  3. Verify changes persisted
- **Expected Result:** Exactly one row updated with new values
- **Pass Criteria:** 
  - `rows_affected == 1`
  - Database record matches updated values

##### 4.2.2.2 Non-existent Record Update
- **Objective:** Test updating records that don't exist
- **Test Method:** `test_update_grade_nonexistent_id()`
- **Test Data:** Grade ID 99999 (non-existent)
- **Expected Result:** No rows affected
- **Pass Criteria:** `rows_affected == 0`

##### 4.2.2.3 Update Error Handling
- **Objective:** Test error handling during grade updates
- **Test Method:** `test_update_grade_database_error()`
- **Mock Condition:** Database connection failure
- **Expected Result:** `mysql.connector.Error` exception raised
- **Pass Criteria:** Exception properly propagated

#### 4.2.3 Data Retrieval Tests

##### 4.2.3.1 Get All Grades Test
- **Objective:** Test retrieving all grade records
- **Test Method:** `test_get_all_grades()`
- **Process:**
  1. Add multiple test records
  2. Retrieve all grades
  3. Verify test records present
- **Expected Result:** List of dictionaries with correct structure
- **Pass Criteria:**
  - Returns list object
  - Contains expected test records
  - Each record has required fields: `id`, `Subject`, `StudyTime`, `AssignmentName`, `Grade`, `Weight`

  4.2.4 Grade Deletion Tests
4.2.4.1 Successful Grade Deletion

Objective: Delete an existing grade record

Test Method: test_delete_grade_success()

Process:

Add a grade using add_grade()

Verify it exists

Call delete_grade(id)

Confirm record no longer exists in DB

Expected Result:

rows_deleted == 1

Row is removed from database

Pass Criteria: Database no longer returns the record

4.2.4.2 Non-existent Grade Deletion

Objective: Ensure deleting an invalid ID does nothing

Test Method: test_delete_grade_nonexistent_id()

Test Data: Use a very large ID (e.g., 999999)

Expected Result:

rows_deleted == 0

Pass Criteria: No rows modified

4.2.4.3 Delete Error Handling

Objective: Verify behavior when DB error occurs

Test Method: test_delete_grade_database_error()

Mock Condition: cursor.execute raises mysql.connector.Error

Expected Result:

Exception is propagated

Transaction is rolled back

Pass Criteria: Test catches the error properly

## 5. Test Execution

### 5.1 Running Tests

```bash
# Activate virtual environment
cd /Users/leon/SE101/project_team_21/Project
source .venv/bin/activate

# Run all tests
python -m pytest tests/test_code.py -v

# Run specific test categories
python -m pytest tests/test_code.py::Test_connection -v
python -m pytest tests/test_code.py::Test_CRUD_Operations -v
```

### 5.2 Test Data Management

- **Setup:** Each test class initializes database using `init_db()`
- **Cleanup:** Before each test, removes all records with `Subject LIKE 'TEST_%'`
- **Isolation:** Each test is independent and doesn't affect others

## 6. Database Schema

### 6.1 Table Structure
```sql
CREATE TABLE {DB_USER}_grades (
    id INT AUTO_INCREMENT PRIMARY KEY,
    Subject VARCHAR(255) NOT NULL,
    StudyTime DOUBLE NOT NULL,
    AssignmentName VARCHAR(255) NOT NULL,
    Grade DOUBLE NULL,           -- Allows NULL for incomplete assignments
    Weight DOUBLE NOT NULL
);
```

### 6.2 Key Features
- **Auto-incrementing ID:** Primary key for unique identification
- **NULL Grades:** Supports incomplete assignments
- **User-specific tables:** Each user gets their own table (e.g., `root_grades`)

## 7. Current Test Results

### 7.1 Test Summary
- **Total Tests:** 11
- **Connection Tests:** 4
- **CRUD Tests:** 7
- **Pass Rate:** 100% (11/11 passing)

### 7.2 Test Categories Status
✅ **Database Connection Tests:** All 4 tests passing  
✅ **CRUD Operation Tests:** All 7 tests passing  
✅ **Error Handling:** All error scenarios covered  
✅ **Data Integrity:** All data validation tests passing  

## 8. Integration Points

### 8.1 Flask Application Integration
- CRUD functions designed for use by Flask routes (`/add`, `/update`)
- Database initialization available for app startup
- Functions tested independently of web interface

## 9. Dependencies and Requirements

### 9.1 Python Packages
```txt
mysql-connector-python==9.5.0
Flask==3.1.2
python-dotenv==1.2.1
pytest==9.0.1
pytest-html==4.1.1
```

### 9.2 Environment Variables
- `Userid`: Database username
- `Password`: Database password
- Must be configured in `.env` file

## 10. Conclusion

The implemented test suite provides coverage of the core database functionality and CRUD operations that have been developed. All 11 tests are currently passing, indicating that the database connectivity and basic CRUD operations (add_grade, update_grade, get_all_grades) are working correctly.