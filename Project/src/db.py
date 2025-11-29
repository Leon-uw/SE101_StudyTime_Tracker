# src/db.py
import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

# Read from env so tests/CI can inject creds safely
DB_HOST = 'riku.shoshin.uwaterloo.ca'
DB_USER = os.getenv("Userid", "root")
DB_PASS = os.getenv("Password", "")
DB_NAME = 'SE101_Team_21'
TABLE_NAME = f"{DB_USER}_grades"
CATEGORIES_TABLE = f"{DB_USER}_categories"
SUBJECTS_TABLE = f"{DB_USER}_subjects"

# Grades table DDL - includes Category column
GRADES_DDL = f"""
CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username varchar(255) NOT NULL,
    Subject varchar(255) NOT NULL,
    Category varchar(255) NOT NULL,
    StudyTime double NOT NULL,
    AssignmentName varchar(255) NOT NULL,
    Grade double NULL,
    Weight double NOT NULL,
    IsPrediction BOOLEAN DEFAULT FALSE,
    Position INT NOT NULL DEFAULT 0,
    INDEX idx_user_subject_category (username, Subject, Category),
    INDEX idx_user_position (username, Position)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""



# Categories table DDL
CATEGORIES_DDL = f"""
CREATE TABLE IF NOT EXISTS {CATEGORIES_TABLE} (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username varchar(255) NOT NULL,
    Subject varchar(255) NOT NULL,
    CategoryName varchar(255) NOT NULL,
    TotalWeight double NOT NULL,
    DefaultName varchar(255),
    UNIQUE KEY unique_user_subject_category (username, Subject, CategoryName)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

# Subjects table DDL - PHASE 7: Subjects now persist independently
SUBJECTS_DDL = f"""
CREATE TABLE IF NOT EXISTS {SUBJECTS_TABLE} (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username varchar(255) NOT NULL,
    name varchar(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_user_subject (username, name),
    INDEX idx_user_name (username, name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

USERS_TABLE = f"{DB_USER}_users"

# Users table DDL
USERS_DDL = f"""
CREATE TABLE IF NOT EXISTS {USERS_TABLE} (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username varchar(255) NOT NULL UNIQUE,
    password_hash varchar(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

# User Preferences table DDL - stores per-subject settings like grade_lock
USER_PREFERENCES_TABLE = f"{DB_USER}_user_preferences"

USER_PREFERENCES_DDL = f"""
CREATE TABLE IF NOT EXISTS {USER_PREFERENCES_TABLE} (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username varchar(255) NOT NULL,
    subject varchar(255) NOT NULL,
    grade_lock BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_user_subject_pref (username, subject),
    INDEX idx_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

def _connect(db=None):
    return mysql.connector.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASS, database=db or DB_NAME
    )

def init_db():
    """Create database and tables if they don't exist."""
    # Create DB if missing
    admin = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASS)
    admin.autocommit = True
    cur = admin.cursor()
    cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} DEFAULT CHARSET utf8mb4")
    cur.close()
    admin.close()

    # Create tables if missing (no longer dropping - preserves data)
    conn = _connect(DB_NAME)
    try:
        cur = conn.cursor()
        # Create all tables
        cur.execute(GRADES_DDL)
        cur.execute(CATEGORIES_DDL)
        cur.execute(SUBJECTS_DDL)
        cur.execute(USERS_DDL)
        cur.execute(USER_PREFERENCES_DDL)
        conn.commit()
    finally:
        cur.close()
        conn.close()

    ensure_position_column()
    ensure_retired_column()

    # Seed initial data if tables are empty
    seed_initial_data()



def seed_initial_data():
    """Populate database with Sprint 2A sample data (only if empty)."""
    conn = _connect()
    try:
        cur = conn.cursor()

        # Check if categories already exist
        cur.execute(f"SELECT COUNT(*) FROM {CATEGORIES_TABLE}")
        count = cur.fetchone()[0]

        if count > 0:
            # Data already exists, skip seeding
            return

        # PHASE 7: Insert subjects first
        subjects = ["Mathematics", "History", "Science"]
        subject_query = f"""
            INSERT INTO {SUBJECTS_TABLE} (username, name)
            VALUES (%s, %s)
        """
        for subject in subjects:
            cur.execute(subject_query, ('testuser', subject))

        # Insert sample categories (from Sprint 2A weight_categories)
        categories = [
            ("Mathematics", "Homework", 20, "Homework #"),
            ("Mathematics", "Quizzes", 30, "Quiz #"),
            ("History", "Essays", 15, ""),
            ("Science", "Labs", 25, "Lab #"),
            ("Science", "Projects", 30, "Project #"),
        ]

        category_query = f"""
            INSERT INTO {CATEGORIES_TABLE}
            (username, Subject, CategoryName, TotalWeight, DefaultName)
            VALUES (%s, %s, %s, %s, %s)
        """

        for subject, name, weight, default in categories:
            cur.execute(category_query, ('testuser', subject, name, weight, default))

        # Insert sample assignments (from Sprint 2A study_data)
        assignments = [
            ("Mathematics", "Homework", 2.5, "Homework 1", 85, 10.0),
            ("History", "Essays", 1.5, "Essay on Rome", 92, 15.0),
            ("Science", "Labs", 3.0, "Lab Report", 78, 20.0),
            ("Mathematics", "Quizzes", 1.0, "Quiz 1", 95, 5.0),
            ("Science", "Projects", 2.5, "Project Proposal", None, 15.0),
            ("Mathematics", "Homework", 2.0, "Homework 2", 88, 10.0),
        ]

        assignment_query = f"""
            INSERT INTO {TABLE_NAME}
            (username, Subject, Category, StudyTime, AssignmentName, Grade, Weight)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        for subject, category, time, name, grade, weight in assignments:
            cur.execute(assignment_query, ('testuser', subject, category, time, name, grade, weight))

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
    finally:
        cur.close()
        conn.close()

def ensure_position_column():
    """Add Position column + index if missing, then backfill per user in current order."""
    conn = _connect()
    try:
        cur = conn.cursor()
        # Check if Position exists
        cur.execute("""
            SELECT COUNT(*) FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND COLUMN_NAME='Position'
        """, (DB_NAME, TABLE_NAME))
        has_col = cur.fetchone()[0] > 0

        if not has_col:
            # Add column + index
            cur.execute(f"ALTER TABLE {TABLE_NAME} ADD COLUMN Position INT NOT NULL DEFAULT 0")
            cur.execute(f"CREATE INDEX idx_user_position ON {TABLE_NAME} (username, Position)")

            # Backfill positions per user in (username, id) order
            # We'll do it in Python to avoid multi-statement SQL hassles.
            c2 = conn.cursor(dictionary=True)
            c2.execute(f"SELECT id, username FROM {TABLE_NAME} ORDER BY username, id")
            pos_by_user = {}
            updates = []
            for row in c2:
                u = row['username']
                p = pos_by_user.get(u, 0)
                updates.append((p, row['id']))
                pos_by_user[u] = p + 1
            c2.close()

            if updates:
                cur.executemany(f"UPDATE {TABLE_NAME} SET Position=%s WHERE id=%s", updates)

            conn.commit()
    finally:
        try:
            cur.close()
        except Exception:
            pass
        conn.close()

def get_grade_lock_preferences(username):
    """
    Get all grade lock preferences for a user.
    Returns a dictionary: {subject: grade_lock_boolean}
    """
    conn = _connect()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            f"SELECT subject, grade_lock FROM {USER_PREFERENCES_TABLE} WHERE username = %s",
            (username,)
        )
        results = cur.fetchall()
        # Convert to dict
        return {row['subject']: bool(row['grade_lock']) for row in results}
    finally:
        cur.close()
        conn.close()

def set_grade_lock_preference(username, subject, grade_lock):
    """
    Set grade lock preference for a specific subject.
    Uses INSERT ... ON DUPLICATE KEY UPDATE to create or update.
    """
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(
            f"""
            INSERT INTO {USER_PREFERENCES_TABLE} (username, subject, grade_lock)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE grade_lock = VALUES(grade_lock)
            """,
            (username, subject, grade_lock)
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()

def get_grade_lock_for_subject(username, subject):
    """
    Get grade lock preference for a specific subject.
    Returns True by default if not set.
    """
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(
            f"SELECT grade_lock FROM {USER_PREFERENCES_TABLE} WHERE username = %s AND subject = %s",
            (username, subject)
        )
        result = cur.fetchone()
        if result:
            return bool(result[0])
        return True  # Default to True if not set
    finally:
        cur.close()
        conn.close()

def ensure_retired_column():
    """Add is_retired column to subjects table if it doesn't exist."""
    conn = _connect()
    try:
        cur = conn.cursor()
        # Check if column exists
        cur.execute(f"""
            SELECT COUNT(*) FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = '{DB_NAME}'
            AND TABLE_NAME = '{SUBJECTS_TABLE}'
            AND COLUMN_NAME = 'is_retired'
        """)
        if cur.fetchone()[0] == 0:
            cur.execute(f"""
                ALTER TABLE {SUBJECTS_TABLE}
                ADD COLUMN is_retired BOOLEAN DEFAULT FALSE
            """)
            conn.commit()
            print(f"Added is_retired column to {SUBJECTS_TABLE}")
    except Exception as e:
        print(f"Warning: Could not add is_retired column: {e}")
    finally:
        cur.close()
        conn.close()

def retire_subject(username, subject_name):
    """Mark a subject as retired."""
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(
            f"UPDATE {SUBJECTS_TABLE} SET is_retired = TRUE WHERE username = %s AND name = %s",
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
            f"UPDATE {SUBJECTS_TABLE} SET is_retired = FALSE WHERE username = %s AND name = %s",
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
            f"SELECT * FROM {SUBJECTS_TABLE} WHERE username = %s AND is_retired = TRUE ORDER BY name",
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
