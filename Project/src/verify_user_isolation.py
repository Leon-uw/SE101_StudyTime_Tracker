import unittest
import mysql.connector
from db import _connect, TABLE_NAME, CATEGORIES_TABLE, SUBJECTS_TABLE
from crud import add_subject, add_category, add_grade, get_all_grades, get_all_subjects, get_all_categories

class TestUserIsolation(unittest.TestCase):
    def setUp(self):
        # Clean up test data before each test
        self.clean_up_user("test_user_a")
        self.clean_up_user("test_user_b")

    def tearDown(self):
        # Clean up test data after each test
        self.clean_up_user("test_user_a")
        self.clean_up_user("test_user_b")

    def clean_up_user(self, username):
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {TABLE_NAME} WHERE username = %s", (username,))
        cursor.execute(f"DELETE FROM {CATEGORIES_TABLE} WHERE username = %s", (username,))
        cursor.execute(f"DELETE FROM {SUBJECTS_TABLE} WHERE username = %s", (username,))
        conn.commit()
        cursor.close()
        conn.close()

    def test_data_isolation(self):
        print("Testing data isolation...")
        
        # 1. User A adds data
        print("User A adding data...")
        add_subject("test_user_a", "Math")
        add_category("test_user_a", "Math", "Homework", 50)
        add_grade("test_user_a", "Math", "Homework", 2.0, "HW1", 90, 10)

        # 2. User B adds data
        print("User B adding data...")
        add_subject("test_user_b", "History")
        add_category("test_user_b", "History", "Essays", 50)
        add_grade("test_user_b", "History", "Essays", 3.0, "Essay1", 85, 10)

        # 3. Verify User A sees only their data
        print("Verifying User A data...")
        subjects_a = get_all_subjects("test_user_a")
        self.assertEqual(len(subjects_a), 1)
        self.assertEqual(subjects_a[0]['name'], "Math")

        grades_a = get_all_grades("test_user_a")
        self.assertEqual(len(grades_a), 1)
        self.assertEqual(grades_a[0]['assignment_name'], "HW1")

        # 4. Verify User B sees only their data
        print("Verifying User B data...")
        subjects_b = get_all_subjects("test_user_b")
        self.assertEqual(len(subjects_b), 1)
        self.assertEqual(subjects_b[0]['name'], "History")

        grades_b = get_all_grades("test_user_b")
        self.assertEqual(len(grades_b), 1)
        self.assertEqual(grades_b[0]['assignment_name'], "Essay1")

        print("Data isolation verified successfully!")

if __name__ == "__main__":
    unittest.main()
