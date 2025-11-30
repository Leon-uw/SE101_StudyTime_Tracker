# Local SQLite database configuration for development
# Use this when you can't access the remote MySQL server

import sqlite3
import os

# Database file location
DB_FILE = os.path.join(os.path.dirname(__file__), 'local_dev.db')

# Table names
TABLE_NAME = "grades"
CATEGORIES_TABLE = "categories"
SUBJECTS_TABLE = "subjects"
USERS_TABLE = "users"

# MySQL-compatible wrapper for SQLite
class SQLiteConnection:
    """Wrapper to make SQLite behave more like MySQL connector"""
    def __init__(self, conn):
        self.conn = conn
        self.conn.row_factory = sqlite3.Row  # Enable dict-like access
        
    def cursor(self, dictionary=False):
        return SQLiteCursor(self.conn.cursor(), dictionary)
    
    def commit(self):
        self.conn.commit()
    
    def rollback(self):
        self.conn.rollback()
    
    def close(self):
        self.conn.close()
    
    @property
    def autocommit(self):
        return self.conn.isolation_level is None
    
    @autocommit.setter
    def autocommit(self, value):
        self.conn.isolation_level = None if value else 'DEFERRED'

class SQLiteCursor:
    """Cursor wrapper that converts MySQL %s placeholders to SQLite ?"""
    def __init__(self, cursor, dictionary=False):
        self.cursor = cursor
        self.dictionary = dictionary
        
    def execute(self, query, params=None):
        # Convert MySQL %s to SQLite ?
        if params:
            query = query.replace('%s', '?')
        return self.cursor.execute(query, params or [])
    
    def executemany(self, query, params_list):
        query = query.replace('%s', '?')
        return self.cursor.executemany(query, params_list)
    
    def fetchone(self):
        row = self.cursor.fetchone()
        if row and self.dictionary:
            return dict(row)
        return row
    
    def fetchall(self):
        rows = self.cursor.fetchall()
        if rows and self.dictionary:
            return [dict(row) for row in rows]
        return rows
    
    def close(self):
        self.cursor.close()
    
    @property
    def rowcount(self):
        return self.cursor.rowcount
    
    @property
    def lastrowid(self):
        return self.cursor.lastrowid

# SQLite DDL (slightly different from MySQL)
GRADES_DDL = f"""
CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    Subject TEXT NOT NULL,
    Category TEXT NOT NULL,
    StudyTime REAL NOT NULL,
    AssignmentName TEXT NOT NULL,
    Grade REAL,
    Weight REAL NOT NULL,
    IsPrediction INTEGER DEFAULT 0,
    PredictedGrade REAL,
    Position INTEGER NOT NULL DEFAULT 0
);
"""

CATEGORIES_DDL = f"""
CREATE TABLE IF NOT EXISTS {CATEGORIES_TABLE} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    Subject TEXT NOT NULL,
    CategoryName TEXT NOT NULL,
    TotalWeight REAL NOT NULL,
    DefaultName TEXT,
    UNIQUE(username, Subject, CategoryName)
);
"""

SUBJECTS_DDL = f"""
CREATE TABLE IF NOT EXISTS {SUBJECTS_TABLE} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_retired INTEGER DEFAULT 0,
    UNIQUE(username, name)
);
"""

USERS_DDL = f"""
CREATE TABLE IF NOT EXISTS {USERS_TABLE} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

def _connect():
    """Get SQLite connection wrapped to be MySQL-compatible"""
    return SQLiteConnection(sqlite3.connect(DB_FILE))

def ensure_retired_column():
    """Add is_retired column to subjects table if it doesn't exist (SQLite)."""
    conn = _connect()
    try:
        cur = conn.cursor()
        # Check if column exists
        cur.execute(f"PRAGMA table_info({SUBJECTS_TABLE})")
        columns = [row[1] for row in cur.cursor.fetchall()]
        if 'is_retired' not in columns:
            cur.execute(f"ALTER TABLE {SUBJECTS_TABLE} ADD COLUMN is_retired INTEGER DEFAULT 0")
            conn.commit()
            print(f"Added is_retired column to {SUBJECTS_TABLE}")
    except Exception as e:
        print(f"Warning: Could not add is_retired column: {e}")
    finally:
        cur.close()
        conn.close()

def ensure_predicted_grade_column():
    """Add PredictedGrade column to grades table if it doesn't exist (SQLite)."""
    conn = _connect()
    try:
        cur = conn.cursor()
        # Check if column exists
        cur.execute(f"PRAGMA table_info({TABLE_NAME})")
        columns = [row[1] for row in cur.cursor.fetchall()]
        if 'PredictedGrade' not in columns:
            cur.execute(f"ALTER TABLE {TABLE_NAME} ADD COLUMN PredictedGrade REAL")
            conn.commit()
            print(f"Added PredictedGrade column to {TABLE_NAME}")
    except Exception as e:
        print(f"Warning: Could not add PredictedGrade column: {e}")
    finally:
        cur.close()
        conn.close()

def init_db():
    """Create database and tables if they don't exist."""
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(GRADES_DDL)
        cur.execute(CATEGORIES_DDL)
        cur.execute(SUBJECTS_DDL)
        cur.execute(USERS_DDL)
        conn.commit()
        print(f"✓ Database initialized at {DB_FILE}")
    finally:
        cur.close()
        conn.close()
    
    ensure_retired_column()
    ensure_predicted_grade_column()
    seed_initial_data()

def seed_initial_data():
    """Populate database with sample data (only if empty)."""
    conn = _connect()
    try:
        cur = conn.cursor()
        
        # Check if data already exists
        cur.execute(f"SELECT COUNT(*) FROM {CATEGORIES_TABLE}")
        count = cur.fetchone()[0]
        
        if count > 0:
            return
        
        # Insert subjects
        subjects = [("testuser", "Mathematics"), ("testuser", "History"), ("testuser", "Science")]
        cur.executemany(f"INSERT INTO {SUBJECTS_TABLE} (username, name) VALUES (%s, %s)", subjects)
        
        # Insert categories
        categories = [
            ("testuser", "Mathematics", "Homework", 20, "Homework #"),
            ("testuser", "Mathematics", "Quizzes", 30, "Quiz #"),
            ("testuser", "History", "Essays", 15, ""),
            ("testuser", "Science", "Labs", 25, "Lab #"),
            ("testuser", "Science", "Projects", 30, "Project #"),
        ]
        cur.executemany(
            f"INSERT INTO {CATEGORIES_TABLE} (username, Subject, CategoryName, TotalWeight, DefaultName) VALUES (%s, %s, %s, %s, %s)",
            categories
        )
        
        # Insert sample assignments
        assignments = [
            ("testuser", "Mathematics", "Homework", 2.5, "Homework 1", 85, 10.0, 0, 0),
            ("testuser", "History", "Essays", 1.5, "Essay on Rome", 92, 15.0, 0, 1),
            ("testuser", "Science", "Labs", 3.0, "Lab Report", 78, 20.0, 0, 2),
            ("testuser", "Mathematics", "Quizzes", 1.0, "Quiz 1", 95, 5.0, 0, 3),
            ("testuser", "Science", "Projects", 2.5, "Project Proposal", None, 15.0, 0, 4),
            ("testuser", "Mathematics", "Homework", 2.0, "Homework 2", 88, 10.0, 0, 5),
        ]
        cur.executemany(
            f"INSERT INTO {TABLE_NAME} (username, Subject, Category, StudyTime, AssignmentName, Grade, Weight, IsPrediction, Position) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            assignments
        )
        
        # Create test user (password: "password")
        from werkzeug.security import generate_password_hash
        test_user_hash = generate_password_hash("password", method='pbkdf2:sha256')
        cur.execute(f"INSERT INTO {USERS_TABLE} (username, password_hash) VALUES (%s, %s)", ("testuser", test_user_hash))
        
        conn.commit()
        print(f"✓ Seeded {len(categories)} categories and {len(assignments)} sample assignments")
        print(f"✓ Created test user: testuser / password")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Error seeding data: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cur.close()
        conn.close()

def retire_subject(username, subject_name):
    """Mark a subject as retired."""
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(
            f"UPDATE {SUBJECTS_TABLE} SET is_retired = 1 WHERE username = %s AND name = %s",
            (username, subject_name)
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        cur.close()
        conn.close()

def unretire_subject(username, subject_name):
    """Mark a subject as not retired (active)."""
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(
            f"UPDATE {SUBJECTS_TABLE} SET is_retired = 0 WHERE username = %s AND name = %s",
            (username, subject_name)
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        cur.close()
        conn.close()

def get_retired_subjects(username):
    """Get all retired subjects for a user."""
    conn = _connect()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            f"SELECT * FROM {SUBJECTS_TABLE} WHERE username = %s AND is_retired = 1 ORDER BY name",
            (username,)
        )
        results = cur.fetchall()
        return [
            {
                'id': row['id'],
                'name': row['name'],
                'created_at': row['created_at'],
                'is_retired': True
            }
            for row in results
        ]
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    init_db()
    print("Database setup complete!")
