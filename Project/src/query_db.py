#!/usr/bin/env python3
"""
Interactive script to query the database
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

from db import _connect, TABLE_NAME, CATEGORIES_TABLE, USERS_TABLE
from crud import get_all_grades

def show_all_data():
    """Display all data in the database"""
    print("=" * 60)
    print("DATABASE CONTENTS")
    print("=" * 60)

    # Show users
    print("\n👥 USERS:")
    print("-" * 60)
    conn = _connect()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(f"SELECT id, username, created_at FROM {USERS_TABLE} ORDER BY id")
        users = cur.fetchall()

        for user in users:
            print(f"  [{user['id']}] {user['username']:20} | Created: {user['created_at']}")

        print(f"\nTotal: {len(users)} users")
    finally:
        cur.close()
        conn.close()

    # Show categories
    print("\n📁 CATEGORIES:")
    print("-" * 60)
    conn = _connect()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(f"SELECT * FROM {CATEGORIES_TABLE} ORDER BY Subject, CategoryName")
        categories = cur.fetchall()

        for cat in categories:
            print(f"  {cat['Subject']:15} | {cat['CategoryName']:15} | {cat['TotalWeight']:5.1f}% | '{cat['DefaultName']}'")

        print(f"\nTotal: {len(categories)} categories")
    finally:
        cur.close()
        conn.close()

    # Show assignments
    print("\n\n📝 ASSIGNMENTS:")
    print("-" * 60)
    conn = _connect()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(f"SELECT * FROM {TABLE_NAME} ORDER BY Subject, Category, id")
        assignments = cur.fetchall()

        for a in assignments:
            grade_str = f"{a['Grade']}%" if a['Grade'] is not None else "N/A"
            print(f"  [{a['id']}] {a['Subject']:12} / {a['Category']:12} | {a['AssignmentName']:20} | {a['StudyTime']:4.1f}h | {grade_str:6} | {a['Weight']:5.1f}%")

        print(f"\nTotal: {len(assignments)} assignments")
    finally:
        cur.close()
        conn.close()

    # Test CRUD function
    print("\n\n🔧 TESTING CRUD FUNCTION:")
    print("-" * 60)
    # Default to 'admin' for testing
    grades = get_all_grades('admin')
    print(f"  get_all_grades('admin') returned {len(grades)} rows")
    if grades:
        print(f"  Sample row keys: {list(grades[0].keys())}")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    show_all_data()
