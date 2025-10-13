"""
Simple shared setup function for team testing
"""
import os
import logging
from dotenv import load_dotenv
import todo

def setup_test_environment():
    """
    Simple setup function that team members can call at the start of their tests.
    Returns True if setup successful, False if credentials missing.
    """
    # Load environment variables
    load_dotenv()
    
    # Check if we have database credentials
    if not all([os.getenv('TODO_DB_USER'), os.getenv('TODO_DB_PASSWORD'), os.getenv('TODO_DB_NAME')]):
        return False
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Clean up database - clean all common test data
    cleanup_test_data()
    
    return True

def cleanup_test_data():
    """Clean up common test data"""
    try:
        connection = todo.connect2DB()
        if connection:
            cursor = connection.cursor()
            # Clean common test items
            test_items = [
                "Unit test task",
                "Duplicate test task", 
                "Already completed task",
                "Invalid type test",
                "Invalid length test",
                "Edge case task",
                "Boundary test task",
                "Team test task",
                "Update test task",
                "Next task test",
                "Smoke test task"
            ]
            
            for item in test_items:
                cursor.execute("DELETE FROM ToDoData WHERE item = %s", (item,))
            
            connection.commit()
            cursor.close()
            connection.close()
    except:
        pass  # Ignore cleanup errors

def cleanup_after_test():
    """Clean up after tests - call this at the end of your test file"""
    try:
        connection = todo.connect2DB()
        if connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM tasks")
            connection.commit()
            cursor.close()
            connection.close()
    except:
        pass  # Ignore cleanup errors