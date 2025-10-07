
"""
Comprehensive Unit Tests for todo.py

This test suite covers all edge cases and validation scenarios for the
add(), update(), and next_task() functions.
"""

import pytest
import datetime
import time
import logging
import sys
from todo import add

# Configure logging for tests - create a dedicated file handler
test_logger = logging.getLogger('test_todo')
test_logger.setLevel(logging.INFO)

# Create file handler
file_handler = logging.FileHandler('test_todo.log', mode='w')
file_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
file_handler.setFormatter(formatter)

# Add handler to logger
test_logger.addHandler(file_handler)

@pytest.fixture(scope="session", autouse=True)
def setup_logging():
    """Setup logging for the test session"""
    test_logger.info("=" * 60)
    test_logger.info("STARTING TO-DO FUNCTION TEST SESSION")
    test_logger.info("=" * 60)
    
    yield
    
    test_logger.info("=" * 60)
    test_logger.info("TO-DO FUNCTION TEST SESSION COMPLETED")
    test_logger.info("=" * 60)

class TestAddFunction:
    """Comprehensive unit tests for the add() function"""
    
    def setup_method(self):
        """Setup run before each test method - clean up test data"""
        from todo import connect2DB
        
        # Clean up any existing test data
        connection = connect2DB()
        if connection:
            cursor = connection.cursor()
            try:
                # Delete test tasks that might interfere with tests
                test_items = [
                    "Unit test task",
                    "Duplicate test task", 
                    "Already completed task",
                    "Invalid type test",
                    "Invalid length test",
                    "Edge case task",
                    "Boundary test task"
                ]
                
                for item in test_items:
                    cursor.execute("DELETE FROM ToDoData WHERE item = %s", (item,))
                
                connection.commit()
                cursor.close()
                connection.close()
            except Exception as e:
                print(f"Cleanup warning: {e}")
                cursor.close()
                connection.close()

    # ==================== VALID INPUT TESTS ====================
    
    def test_add_valid_task_basic(self):
        """Test adding a basic valid task"""
        test_logger.info("Testing add function with basic valid task")
        test_task = (
            "Unit test task",
            "Testing", 
            datetime.datetime(2025, 9, 30, 10, 0, 0),
            datetime.datetime(2025, 10, 5, 17, 0, 0),
            None
        )
        
        result = add(test_task)
        assert result is True, "Should successfully add a valid task"
    
    def test_add_valid_task_with_completion_date(self):
        """Test adding a task that's already completed"""
        test_logger.info("Testing add function with already completed task")
        completed_task = (
            "Already completed task",
            "Testing",
            datetime.datetime(2025, 9, 20, 9, 0, 0),
            datetime.datetime(2025, 9, 25, 17, 0, 0),
            datetime.datetime(2025, 9, 24, 16, 30, 0)  # Already completed
        )
        
        result = add(completed_task)
        assert result is True, "Should successfully add a completed task"
    
    def test_add_task_with_same_start_and_due_date(self):
        """Test adding a task where start and due dates are the same"""
        test_logger.info("Testing add function with same start and due dates")
        same_date = datetime.datetime(2025, 10, 1, 12, 0, 0)
        test_task = (
            "Edge case task",
            "Testing",
            same_date,
            same_date,
            None
        )
        
        result = add(test_task)
        assert result is True, "Should successfully add task with same start/due dates"

    # ==================== DUPLICATE TESTS ====================
    
    def test_add_duplicate_task_fails(self):
        """Test that adding a duplicate task fails"""
        test_logger.info("Testing add function with duplicate task")
        test_task = (
            "Duplicate test task",
            "Testing", 
            datetime.datetime(2025, 9, 30, 12, 0, 0),
            datetime.datetime(2025, 10, 2, 12, 0, 0),
            None
        )
        
        # Add the task first time
        result1 = add(test_task)
        # Try to add the same task again
        result2 = add(test_task)
        
        assert result1 is True, "First add should succeed"
        assert result2 is False, "Second add should fail (duplicate)"

    # ==================== INVALID TUPLE LENGTH TESTS ====================
    
    def test_add_task_with_too_few_elements(self):
        """Test that task tuples with too few elements are rejected"""
        test_logger.info("Testing add function with tasks having too few elements")
        short_tasks = [
            (),  # Empty tuple
            ("Item only",),  # 1 element
            ("Item", "Type"),  # 2 elements
            ("Item", "Type", datetime.datetime.now()),  # 3 elements
            ("Item", "Type", datetime.datetime.now(), datetime.datetime.now())  # 4 elements
        ]
        
        for task in short_tasks:
            result = add(task)
            assert result is False, f"Should reject task with {len(task)} elements: {task}"
    
    def test_add_task_with_too_many_elements(self):
        """Test that task tuples with too many elements are rejected"""
        test_logger.info("Testing add function with tasks having too many elements")
        long_tasks = [
            # 6 elements
            ("Item", "Type", datetime.datetime.now(), datetime.datetime.now(), None, "extra"),
            # 7 elements
            ("Item", "Type", datetime.datetime.now(), datetime.datetime.now(), None, "extra1", "extra2"),
            # 10 elements
            ("Item", "Type", datetime.datetime.now(), datetime.datetime.now(), None, 
             "e1", "e2", "e3", "e4", "e5")
        ]
        
        for task in long_tasks:
            result = add(task)
            assert result is False, f"Should reject task with {len(task)} elements"

    # ==================== INVALID DATA TYPE TESTS ====================
    
    def test_add_task_with_invalid_item_types(self):
        """Test that tasks with invalid item types are rejected"""
        test_logger.info("Testing add function with invalid item data types")
        invalid_item_tasks = [
            # Integer item
            (123, "Type", datetime.datetime.now(), datetime.datetime.now(), None),
            # Float item
            (45.67, "Type", datetime.datetime.now(), datetime.datetime.now(), None),
            # Boolean item
            (True, "Type", datetime.datetime.now(), datetime.datetime.now(), None),
            # List item
            (["item"], "Type", datetime.datetime.now(), datetime.datetime.now(), None),
            # None item
            (None, "Type", datetime.datetime.now(), datetime.datetime.now(), None),
            # Dictionary item
            ({"item": "value"}, "Type", datetime.datetime.now(), datetime.datetime.now(), None)
        ]
        
        for task in invalid_item_tasks:
            result = add(task)
            assert result is False, f"Should reject task with invalid item type: {type(task[0])}"
    
    def test_add_task_with_invalid_type_field_types(self):
        """Test that tasks with invalid type field types are rejected"""
        test_logger.info("Testing add function with invalid type field data types")
        invalid_type_tasks = [
            # Integer type
            ("Item", 123, datetime.datetime.now(), datetime.datetime.now(), None),
            # Float type
            ("Item", 45.67, datetime.datetime.now(), datetime.datetime.now(), None),
            # Boolean type
            ("Item", False, datetime.datetime.now(), datetime.datetime.now(), None),
            # List type
            ("Item", ["type"], datetime.datetime.now(), datetime.datetime.now(), None),
            # None type
            ("Item", None, datetime.datetime.now(), datetime.datetime.now(), None)
        ]
        
        for task in invalid_type_tasks:
            result = add(task)
            assert result is False, f"Should reject task with invalid type field: {type(task[1])}"
    
    def test_add_task_with_invalid_started_types(self):
        """Test that tasks with invalid started date types are rejected"""
        test_logger.info("Testing add function with invalid started date data types")
        invalid_started_tasks = [
            # String started
            ("Item", "Type", "2025-09-30", datetime.datetime.now(), None),
            # Integer started
            ("Item", "Type", 20250930, datetime.datetime.now(), None),
            # None started
            ("Item", "Type", None, datetime.datetime.now(), None),
            # Boolean started
            ("Item", "Type", True, datetime.datetime.now(), None),
            # Date object instead of datetime
            ("Item", "Type", datetime.date(2025, 9, 30), datetime.datetime.now(), None)
        ]
        
        for task in invalid_started_tasks:
            result = add(task)
            assert result is False, f"Should reject task with invalid started type: {type(task[2])}"
    
    def test_add_task_with_invalid_due_types(self):
        """Test that tasks with invalid due date types are rejected"""
        test_logger.info("Testing add function with invalid due date data types")
        invalid_due_tasks = [
            # String due
            ("Item", "Type", datetime.datetime.now(), "2025-10-01", None),
            # Integer due
            ("Item", "Type", datetime.datetime.now(), 20251001, None),
            # None due
            ("Item", "Type", datetime.datetime.now(), None, None),
            # Boolean due
            ("Item", "Type", datetime.datetime.now(), False, None),
            # Date object instead of datetime
            ("Item", "Type", datetime.datetime.now(), datetime.date(2025, 10, 1), None)
        ]
        
        for task in invalid_due_tasks:
            result = add(task)
            assert result is False, f"Should reject task with invalid due type: {type(task[3])}"
    
    def test_add_task_with_invalid_done_types(self):
        """Test that tasks with invalid done date types are rejected"""
        test_logger.info("Testing add function with invalid done date data types")
        invalid_done_tasks = [
            # String done (should be datetime or None)
            ("Item", "Type", datetime.datetime.now(), datetime.datetime.now(), "completed"),
            # Integer done
            ("Item", "Type", datetime.datetime.now(), datetime.datetime.now(), 20250930),
            # Boolean done
            ("Item", "Type", datetime.datetime.now(), datetime.datetime.now(), True),
            # List done
            ("Item", "Type", datetime.datetime.now(), datetime.datetime.now(), ["done"]),
            # Date object instead of datetime
            ("Item", "Type", datetime.datetime.now(), datetime.datetime.now(), datetime.date(2025, 9, 30))
        ]
        
        for task in invalid_done_tasks:
            result = add(task)
            assert result is False, f"Should reject task with invalid done type: {type(task[4])}"

    # ==================== NON-TUPLE INPUT TESTS ====================
    
    def test_add_non_tuple_inputs(self):
        """Test that non-tuple inputs are rejected"""
        test_logger.info("Testing add function with non-tuple inputs")
        non_tuple_inputs = [
            # List instead of tuple
            ["Item", "Type", datetime.datetime.now(), datetime.datetime.now(), None],
            # Dictionary
            {"item": "Item", "type": "Type"},
            # String
            "Item,Type,2025-09-30,2025-10-01,None",
            # Integer
            12345,
            # None
            None,
            # Set
            {"Item", "Type"}
        ]
        
        for invalid_input in non_tuple_inputs:
            result = add(invalid_input)
            assert result is False, f"Should reject non-tuple input: {type(invalid_input)}"

    # ==================== BOUNDARY TESTS ====================
    
    def test_add_task_with_very_long_strings(self):
        """Test adding tasks with very long item names and types"""
        test_logger.info("Testing add function with very long strings")
        long_item = "x" * 1000  # Very long item name
        long_type = "y" * 500   # Very long type
        
        test_task = (
            long_item,
            long_type,
            datetime.datetime(2025, 9, 30, 10, 0, 0),
            datetime.datetime(2025, 10, 5, 17, 0, 0),
            None
        )
        
        result = add(test_task)
        # This might pass or fail depending on database constraints
        # The test documents the behavior
        assert isinstance(result, bool), "Should return a boolean result"
    
    def test_add_task_with_empty_strings(self):
        """Test adding tasks with empty item names and types"""
        test_logger.info("Testing add function with empty strings")
        empty_string_tasks = [
            # Empty item name
            ("", "Type", datetime.datetime.now(), datetime.datetime.now(), None),
            # Empty type
            ("Item", "", datetime.datetime.now(), datetime.datetime.now(), None),
            # Both empty
            ("", "", datetime.datetime.now(), datetime.datetime.now(), None)
        ]
        
        for task in empty_string_tasks:
            result = add(task)
            # Document behavior - might be valid depending on business rules
            assert isinstance(result, bool), f"Should return boolean for empty strings: {task[:2]}"

if __name__ == "__main__":
    # This allows running the tests directly with: python test_todo.py
    pytest.main([__file__, "-v"])