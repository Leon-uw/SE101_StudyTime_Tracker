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
    INDEX idx_user_subject_category (username, Subject, Category)
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
        # Create all three tables
        cur.execute(GRADES_DDL)
        cur.execute(CATEGORIES_DDL)
        cur.execute(SUBJECTS_DDL)
        cur.execute(USERS_DDL)
        conn.commit()
    finally:
        cur.close()
        conn.close()

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
            cur.execute(subject_query, ('admin', subject))

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
            cur.execute(category_query, ('admin', subject, name, weight, default))

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
            cur.execute(assignment_query, ('admin', subject, category, time, name, grade, weight))

        conn.commit()
        print(f"✓ Seeded {len(categories)} categories and {len(assignments)} sample assignments")

    except mysql.connector.Error as e:
        conn.rollback()
        print(f"✗ Error seeding data: {e}")
    finally:
        cur.close()
        conn.close()
