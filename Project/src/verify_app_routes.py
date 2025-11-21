import unittest
import json
from app import app
from db import _connect, TABLE_NAME, CATEGORIES_TABLE, SUBJECTS_TABLE

class TestAppRoutes(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.username = "test_route_user"
        self.clean_up_user(self.username)

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

    def test_add_subject_route(self):
        self.login()
        response = self.client.post('/add_subject', data={'subject_name': 'RouteMath'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['subject'], 'RouteMath')

        # Verify it's in the DB for this user
        conn = _connect()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(f"SELECT * FROM {SUBJECTS_TABLE} WHERE username = %s AND name = %s", (self.username, 'RouteMath'))
        result = cursor.fetchone()
        self.assertIsNotNone(result)
        cursor.close()
        conn.close()

    def test_rename_subject_route(self):
        self.login()
        self.client.post('/add_subject', data={'subject_name': 'OldName'})
        
        response = self.client.post('/rename_subject', data={'old_name': 'OldName', 'new_name': 'NewName'})
        self.assertEqual(response.status_code, 200)
        
        # Verify change in DB
        conn = _connect()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(f"SELECT * FROM {SUBJECTS_TABLE} WHERE username = %s AND name = %s", (self.username, 'NewName'))
        result = cursor.fetchone()
        self.assertIsNotNone(result)
        cursor.close()
        conn.close()

    def test_delete_subject_route(self):
        self.login()
        self.client.post('/add_subject', data={'subject_name': 'DeleteMe'})
        
        response = self.client.post('/delete_subject', data={'subject_name': 'DeleteMe'})
        self.assertEqual(response.status_code, 200)
        
        # Verify deletion
        conn = _connect()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(f"SELECT * FROM {SUBJECTS_TABLE} WHERE username = %s AND name = %s", (self.username, 'DeleteMe'))
        result = cursor.fetchone()
        self.assertIsNone(result)
        cursor.close()
        conn.close()

if __name__ == "__main__":
    unittest.main()
