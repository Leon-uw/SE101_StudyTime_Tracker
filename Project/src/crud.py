from db import init_db, _connect, TABLE_NAME
import mysql.connector
import os

def get_all_grades():
    """Get all grade records from the database."""
    conn = _connect()
    try:
        curs = conn.cursor(dictionary=True)
        curs.execute(f"SELECT * FROM {TABLE_NAME}")
        return curs.fetchall()
    finally:
        curs.close()
        conn.close()

def add_grade(subject, study_time, assignment_name, grade, weight):
    """add a new set of data into the table"""
    conn = _connect()
    try:
        curs = conn.cursor()
        query = f"""
        INSERT INTO {TABLE_NAME} (Subject, StudyTime, AssignmentName, Grade, Weight)
        VALUES (%s, %s, %s, %s, %s)
        """
        curs.execute(query, (subject, study_time, assignment_name, grade, weight))
        conn.commit()
    except mysql.connector.Error as e:
        conn.rollback()
        raise e
    finally:
        curs.close()
        conn.close()

def update_grade(grade_id, subject, study_time, assignment_name, grade, weight):
    """Update an existing grade from an existing grade"""
    conn = _connect()
    try:
        curs = conn.cursor()
        query = f"""
        UPDATE {TABLE_NAME}
        SET Subject = %s, StudyTime = %s, AssignmentName = %s, Grade = %s, Weight = %s
        WHERE id = %s
        """
        curs.execute(query, (subject, study_time, assignment_name, grade, weight, grade_id))
        conn.commit()
        return curs.rowcount
    except mysql.connector.Error as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
        curs.close()
