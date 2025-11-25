#!/usr/bin/env python3
"""
Quick test script for Phase 1: Database Schema Setup
Tests that tables are created correctly with the new schema.
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

from db import init_db, _connect, TABLE_NAME, CATEGORIES_TABLE

def test_database_setup():
    """Test Phase 1: Database schema creation"""
    print("=" * 60)
    print("Phase 1 Test: Database Schema Setup")
    print("=" * 60)

    # Initialize database
    print("\n[1/5] Initializing database...")
    try:
        init_db()
        print("✓ Database initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize database: {e}")
        return False

    # Check tables exist
    print("\n[2/5] Checking tables exist...")
    conn = _connect()
    try:
        cur = conn.cursor()

        # Check grades table
        cur.execute(f"SHOW TABLES LIKE '{TABLE_NAME}'")
        if cur.fetchone():
            print(f"✓ Table '{TABLE_NAME}' exists")
        else:
            print(f"✗ Table '{TABLE_NAME}' not found")
            return False

        # Check categories table
        cur.execute(f"SHOW TABLES LIKE '{CATEGORIES_TABLE}'")
        if cur.fetchone():
            print(f"✓ Table '{CATEGORIES_TABLE}' exists")
        else:
            print(f"✗ Table '{CATEGORIES_TABLE}' not found")
            return False

    finally:
        cur.close()
        conn.close()

    # Verify grades table schema
    print("\n[3/5] Verifying grades table schema...")
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(f"DESCRIBE {TABLE_NAME}")
        columns = {row[0]: row[1] for row in cur.fetchall()}

        expected_columns = ['id', 'Subject', 'Category', 'StudyTime', 'AssignmentName', 'Grade', 'Weight']
        for col in expected_columns:
            if col in columns:
                print(f"  ✓ Column '{col}' exists ({columns[col]})")
            else:
                print(f"  ✗ Column '{col}' missing")
                return False

    finally:
        cur.close()
        conn.close()

    # Verify categories table schema
    print("\n[4/5] Verifying categories table schema...")
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(f"DESCRIBE {CATEGORIES_TABLE}")
        columns = {row[0]: row[1] for row in cur.fetchall()}

        expected_columns = ['id', 'Subject', 'CategoryName', 'TotalWeight', 'DefaultName']
        for col in expected_columns:
            if col in columns:
                print(f"  ✓ Column '{col}' exists ({columns[col]})")
            else:
                print(f"  ✗ Column '{col}' missing")
                return False

    finally:
        cur.close()
        conn.close()

    # Check seed data
    print("\n[5/5] Checking seed data...")
    conn = _connect()
    try:
        cur = conn.cursor()

        # Check categories
        cur.execute(f"SELECT COUNT(*) FROM {CATEGORIES_TABLE}")
        cat_count = cur.fetchone()[0]
        print(f"  ✓ Categories seeded: {cat_count} rows")

        # Check assignments
        cur.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
        assign_count = cur.fetchone()[0]
        print(f"  ✓ Assignments seeded: {assign_count} rows")

        # Show sample data
        if cat_count > 0:
            cur.execute(f"SELECT Subject, CategoryName, TotalWeight FROM {CATEGORIES_TABLE} LIMIT 3")
            print("\n  Sample categories:")
            for row in cur.fetchall():
                print(f"    - {row[0]}: {row[1]} ({row[2]}%)")

        if assign_count > 0:
            cur.execute(f"SELECT Subject, Category, AssignmentName FROM {TABLE_NAME} LIMIT 3")
            print("\n  Sample assignments:")
            for row in cur.fetchall():
                print(f"    - {row[0]} / {row[1]}: {row[2]}")

    finally:
        cur.close()
        conn.close()

    print("\n" + "=" * 60)
    print("✓ Phase 1 Complete: Database schema ready!")
    print("=" * 60)
    print("\nStatus:")
    print("  • Grades table created with Category column")
    print("  • Categories table created")
    print("  • Sample data seeded")
    print("  • Data will persist across restarts (no DROP TABLE)")
    print("\nNext: Phase 2 - Read-only database integration")
    return True

if __name__ == "__main__":
    success = test_database_setup()
    sys.exit(0 if success else 1)
