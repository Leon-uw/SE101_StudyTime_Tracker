import unittest
import json
from app import app
from db import _connect, TABLE_NAME, CATEGORIES_TABLE, SUBJECTS_TABLE
from crud import add_subject, add_category, add_grade

class TestPrediction(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.username = "test_predict_user"
        self.clean_up_user(self.username)
        
        # Setup initial data
        add_subject(self.username, "Math")
        add_category(self.username, "Math", "Homework", 50)
        # Add enough data for prediction (need at least 2 graded assignments)
        add_grade(self.username, "Math", "Homework", 2.0, "HW1", 90, 10)
        # add_grade(self.username, "Math", "Homework", 3.0, "HW2", 95, 10)

    def tearDown(self):
        self.clean_up_user(self.username)

    def clean_up_user(self, username):
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {TABLE_NAME} WHERE username = %s", (username,))
        cursor.execute(f"DELETE FROM {CATEGORIES_TABLE} WHERE username = %s", (username,))
        cursor.execute(f"DELETE FROM {SUBJECTS_TABLE} WHERE username = %s", (username,))
        conn.commit()
        cursor.close()
        conn.close()

    def login(self):
        with self.client.session_transaction() as sess:
            sess['user'] = self.username

    def test_predict_route(self):
        self.login()
        # Simulate the request sent by the frontend
        response = self.client.post('/predict', data={
            'subject': 'Math',
            'category': 'Homework', # This is what the fixed JS should send
            'weight': '10',
            'hours': '4.0',
            'grade_lock': 'true'
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('predicted_grade', data)
        print(f"Predicted grade: {data.get('predicted_grade')}")

if __name__ == "__main__":
    unittest.main()
