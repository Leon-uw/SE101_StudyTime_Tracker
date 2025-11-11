# src/db.py
import os
import mysql.connector

# Read from env so tests/CI can inject creds safely
DB_HOST = os.getenv("GC_DB_HOST", "localhost")
DB_PORT = int(os.getenv("GC_DB_PORT", "3306"))
DB_USER = os.getenv("GC_DB_USER", "root")
DB_PASS = os.getenv("GC_DB_PASS", "")
DB_NAME = os.getenv("GC_DB_NAME", "gradecalc_dev")
TABLE_NAME = os.getenv("GC_TABLE_NAME", "grades")

# Your required columns:
# courses -> course (TEXT so we don't guess a max length)
# time spent (minutes) -> time_spent INT
# assignment# -> assignment_no INT
# grade 0–100 -> DECIMAL(5,2)
# weight (decimal) -> DECIMAL(6,3)  (works for 20.000 or 0.200; we'll confirm convention)
# users (unsure) -> user_id INT NULL for now
DDL = f"""
CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
    id INT AUTO_INCREMENT PRIMARY KEY,
    course TEXT NOT NULL,
    time_spent INT NOT NULL,
    assignment_no INT NOT NULL,
    grade DECIMAL(5,2) NOT NULL,
    weight DECIMAL(6,3) NOT NULL,
    user_id INT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

def _connect(db=None):
    return mysql.connector.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, database=db or DB_NAME
    )

def init_db():
    """Create database and table if they don't exist."""
    # Create DB if missing
    admin = mysql.connector.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS)
    admin.autocommit = True
    cur = admin.cursor()
    cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} DEFAULT CHARSET utf8mb4")
    cur.close()
    admin.close()

    # Create table if missing
    conn = _connect(DB_NAME)
    try:
        cur = conn.cursor()
        cur.execute(DDL)
        conn.commit()
    finally:
        cur.close()
        conn.close()
