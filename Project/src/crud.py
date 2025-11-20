import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import init_db, _connect, TABLE_NAME, CATEGORIES_TABLE, SUBJECTS_TABLE
import mysql.connector

def get_all_grades():
    """Get all grade records from the database with lowercase field names."""
    conn = _connect()
    try:
        curs = conn.cursor(dictionary=True)
        curs.execute(f"SELECT * FROM {TABLE_NAME}")
        results = curs.fetchall()

        # Convert to lowercase keys for consistency with Sprint 2A dictionaries
        return [
            {
                'id': row['id'],
                'subject': row['Subject'],
                'category': row['Category'],
                'study_time': row['StudyTime'],
                'assignment_name': row['AssignmentName'],
                'grade': row['Grade'],
                'weight': row['Weight'],
                'is_prediction': bool(row['IsPrediction']) if 'IsPrediction' in row else False
            }
            for row in results
        ]
    finally:
        curs.close()
        conn.close()

def get_all_categories(subject=None):
    """Get all category definitions from the database with lowercase field names.

    Args:
        subject: Optional subject filter. If provided, only return categories for that subject.

    Returns:
        List of category dictionaries with lowercase keys matching Sprint 2A format.
    """
    conn = _connect()
    try:
        curs = conn.cursor(dictionary=True)

        if subject:
            curs.execute(f"SELECT * FROM {CATEGORIES_TABLE} WHERE Subject = %s ORDER BY CategoryName", (subject,))
        else:
            curs.execute(f"SELECT * FROM {CATEGORIES_TABLE} ORDER BY Subject, CategoryName")

        results = curs.fetchall()

        # Convert to lowercase keys matching Sprint 2A weight_categories format
        return [
            {
                'id': row['id'],
                'subject': row['Subject'],
                'name': row['CategoryName'],
                'total_weight': row['TotalWeight'],
                'default_name': row['DefaultName'] or ''
            }
            for row in results
        ]
    finally:
        curs.close()
        conn.close()

def get_categories_as_dict():
    """Get categories organized by subject, matching Sprint 2A weight_categories structure.

    Returns:
        Dictionary: {subject: [category_dicts]} matching Sprint 2A format
    """
    categories = get_all_categories()

    # Organize by subject
    result = {}
    for cat in categories:
        subject = cat['subject']
        if subject not in result:
            result[subject] = []

        # Remove 'subject' key from individual category dict
        cat_copy = {k: v for k, v in cat.items() if k != 'subject'}
        result[subject].append(cat_copy)

    return result

def add_grade(subject, category, study_time, assignment_name, grade, weight, is_prediction=False):
    """Add a new assignment to the database"""
    conn = _connect()
    try:
        curs = conn.cursor()
        query = f"""
        INSERT INTO {TABLE_NAME} (Subject, Category, StudyTime, AssignmentName, Grade, Weight, IsPrediction)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        curs.execute(query, (subject, category, study_time, assignment_name, grade, weight, is_prediction))
        conn.commit()
        return curs.lastrowid  # Return the ID of the inserted record
    except mysql.connector.Error as e:
        conn.rollback()
        raise e
    finally:
        curs.close()
        conn.close()

def update_grade(grade_id, subject, category, study_time, assignment_name, grade, weight, is_prediction=False):
    """Update an existing grade"""
    conn = _connect()
    try:
        curs = conn.cursor()
        query = f"""
        UPDATE {TABLE_NAME}
        SET Subject = %s, Category = %s, StudyTime = %s, AssignmentName = %s, Grade = %s, Weight = %s, IsPrediction = %s
        WHERE id = %s
        """
        curs.execute(query, (subject, category, study_time, assignment_name, grade, weight, is_prediction, grade_id))
        conn.commit()
        return curs.rowcount
    except mysql.connector.Error as e:
        conn.rollback()
        raise e
    finally:
        curs.close()
        conn.close()

def delete_grade(grade_id):
    """Delete a single grade"""
    conn = _connect()
    try:
        curs = conn.cursor()
        query = f"DELETE FROM {TABLE_NAME} WHERE id = %s"
        curs.execute(query, (grade_id,))
        conn.commit()
        return curs.rowcount
    except mysql.connector.Error as e:
        conn.rollback()
        raise e
    finally:
        curs.close()
        conn.close()

def delete_grades_bulk(grade_ids):
    """Delete multiple grades"""
    if not grade_ids:
        return 0

    conn = _connect()
    try:
        curs = conn.cursor()
        placeholders = ','.join(['%s'] * len(grade_ids))
        query = f"DELETE FROM {TABLE_NAME} WHERE id IN ({placeholders})"
        curs.execute(query, tuple(grade_ids))
        conn.commit()
        return curs.rowcount
    except mysql.connector.Error as e:
        conn.rollback()
        raise e
    finally:
        curs.close()
        conn.close()

def recalculate_and_update_weights(subject, category_name):
    """Recalculate weights for all assignments in a category and update database.

    This function:
    1. Gets the category definition (total_weight) from the database
    2. Counts assignments in the category
    3. Calculates new weight per assignment (total_weight / num_assignments)
    4. Updates all assignments in the category with the new weight

    Args:
        subject: Subject name
        category_name: Category name

    Returns:
        Number of assignments updated, or 0 if category not found
    """
    conn = _connect()
    try:
        curs = conn.cursor(dictionary=True)

        # Get category definition to get total_weight
        curs.execute(
            f"SELECT TotalWeight FROM {CATEGORIES_TABLE} WHERE Subject = %s AND CategoryName = %s",
            (subject, category_name)
        )
        category = curs.fetchone()

        if not category:
            return 0  # Category doesn't exist

        total_weight = category['TotalWeight']

        # Count assignments in this category
        curs.execute(
            f"SELECT COUNT(*) as count FROM {TABLE_NAME} WHERE Subject = %s AND Category = %s",
            (subject, category_name)
        )
        count_result = curs.fetchone()
        num_assignments = count_result['count']

        if num_assignments == 0:
            return 0  # No assignments to update

        # Calculate new weight per assignment
        new_weight = total_weight / num_assignments

        # Update all assignments in this category
        update_query = f"""
            UPDATE {TABLE_NAME}
            SET Weight = %s
            WHERE Subject = %s AND Category = %s
        """
        curs.execute(update_query, (new_weight, subject, category_name))
        conn.commit()

        return curs.rowcount
    except mysql.connector.Error as e:
        conn.rollback()
        raise e
    finally:
        curs.close()
        conn.close()

def add_category(subject, category_name, total_weight, default_name=''):
    """Add a new category definition to the database"""
    conn = _connect()
    try:
        curs = conn.cursor()
        query = f"""
        INSERT INTO {CATEGORIES_TABLE} (Subject, CategoryName, TotalWeight, DefaultName)
        VALUES (%s, %s, %s, %s)
        """
        curs.execute(query, (subject, category_name, total_weight, default_name))
        conn.commit()
        return curs.lastrowid
    except mysql.connector.Error as e:
        conn.rollback()
        raise e
    finally:
        curs.close()
        conn.close()

def update_category(category_id, subject, category_name, total_weight, default_name=''):
    """Update an existing category definition"""
    conn = _connect()
    try:
        curs = conn.cursor()
        query = f"""
        UPDATE {CATEGORIES_TABLE}
        SET Subject = %s, CategoryName = %s, TotalWeight = %s, DefaultName = %s
        WHERE id = %s
        """
        curs.execute(query, (subject, category_name, total_weight, default_name, category_id))
        conn.commit()
        return curs.rowcount
    except mysql.connector.Error as e:
        conn.rollback()
        raise e
    finally:
        curs.close()
        conn.close()

def delete_category(category_id):
    """Delete a category definition"""
    conn = _connect()
    try:
        curs = conn.cursor()
        query = f"DELETE FROM {CATEGORIES_TABLE} WHERE id = %s"
        curs.execute(query, (category_id,))
        conn.commit()
        return curs.rowcount
    except mysql.connector.Error as e:
        conn.rollback()
        raise e
    finally:
        curs.close()
        conn.close()

def get_total_weight_for_subject(subject, exclude_category_id=None):
    """Calculate total weight of all categories for a subject, optionally excluding one category.

    Args:
        subject: Subject name
        exclude_category_id: Optional category ID to exclude from total (for update validation)

    Returns:
        Total weight as float
    """
    conn = _connect()
    try:
        curs = conn.cursor(dictionary=True)

        if exclude_category_id:
            query = f"""
                SELECT SUM(TotalWeight) as total
                FROM {CATEGORIES_TABLE}
                WHERE Subject = %s AND id != %s
            """
            curs.execute(query, (subject, exclude_category_id))
        else:
            query = f"""
                SELECT SUM(TotalWeight) as total
                FROM {CATEGORIES_TABLE}
                WHERE Subject = %s
            """
            curs.execute(query, (subject,))

        result = curs.fetchone()
        return result['total'] or 0
    finally:
        curs.close()
        conn.close()

# ============================================================================
# PHASE 7: Subject CRUD Operations
# ============================================================================

def get_all_subjects():
    """Get all subjects from the database.

    Returns:
        List of subject dictionaries with 'id', 'name', and 'created_at' keys
    """
    conn = _connect()
    try:
        curs = conn.cursor(dictionary=True)
        curs.execute(f"SELECT * FROM {SUBJECTS_TABLE} ORDER BY name")
        results = curs.fetchall()

        return [
            {
                'id': row['id'],
                'name': row['name'],
                'created_at': row['created_at']
            }
            for row in results
        ]
    finally:
        curs.close()
        conn.close()

def add_subject(name):
    """Add a new subject to the database.

    Args:
        name: Subject name (must be unique)

    Returns:
        ID of the inserted subject

    Raises:
        mysql.connector.IntegrityError: If subject name already exists
    """
    conn = _connect()
    try:
        curs = conn.cursor()
        query = f"""
        INSERT INTO {SUBJECTS_TABLE} (name)
        VALUES (%s)
        """
        curs.execute(query, (name,))
        conn.commit()
        return curs.lastrowid
    except mysql.connector.Error as e:
        conn.rollback()
        raise e
    finally:
        curs.close()
        conn.close()

def delete_subject(subject_id):
    """Delete a subject from the database.

    This will also delete all assignments and categories for this subject (cascade).

    Args:
        subject_id: ID of the subject to delete

    Returns:
        Number of subjects deleted (0 or 1)
    """
    conn = _connect()
    try:
        curs = conn.cursor(dictionary=True)

        # First get the subject name
        curs.execute(f"SELECT name FROM {SUBJECTS_TABLE} WHERE id = %s", (subject_id,))
        subject = curs.fetchone()

        if not subject:
            return 0

        subject_name = subject['name']

        # Delete all assignments for this subject
        curs.execute(f"DELETE FROM {TABLE_NAME} WHERE Subject = %s", (subject_name,))

        # Delete all categories for this subject
        curs.execute(f"DELETE FROM {CATEGORIES_TABLE} WHERE Subject = %s", (subject_name,))

        # Delete the subject itself
        curs.execute(f"DELETE FROM {SUBJECTS_TABLE} WHERE id = %s", (subject_id,))

        conn.commit()
        return curs.rowcount
    except mysql.connector.Error as e:
        conn.rollback()
        raise e
    finally:
        curs.close()
        conn.close()

def get_subject_by_name(name):
    """Get a subject by name.

    Args:
        name: Subject name to search for

    Returns:
        Subject dictionary with 'id', 'name', and 'created_at' keys, or None if not found
    """
    conn = _connect()
    try:
        curs = conn.cursor(dictionary=True)
        curs.execute(f"SELECT * FROM {SUBJECTS_TABLE} WHERE name = %s", (name,))
        result = curs.fetchone()

        if result:
            return {
                'id': result['id'],
                'name': result['name'],
                'created_at': result['created_at']
            }
        return None
    finally:
        curs.close()
        conn.close()

def rename_subject(old_name, new_name):
    """Renames a subject across all tables.
    
    Args:
        old_name: Current name of the subject
        new_name: New name for the subject
        
    Returns:
        True if successful
        
    Raises:
        ValueError: If new_name already exists
        mysql.connector.Error: If database error occurs
    """
    conn = _connect()
    curs = conn.cursor()
    try:
        # Check if new name already exists
        curs.execute(f"SELECT id FROM {SUBJECTS_TABLE} WHERE name = %s", (new_name,))
        if curs.fetchone():
            raise ValueError(f"Subject '{new_name}' already exists.")

        # Update SUBJECTS_TABLE
        curs.execute(f"UPDATE {SUBJECTS_TABLE} SET name = %s WHERE name = %s", (new_name, old_name))
        
        # Update GRADES_TABLE
        curs.execute(f"UPDATE {TABLE_NAME} SET Subject = %s WHERE Subject = %s", (new_name, old_name))
        
        # Update CATEGORIES_TABLE
        curs.execute(f"UPDATE {CATEGORIES_TABLE} SET Subject = %s WHERE Subject = %s", (new_name, old_name))
        
        conn.commit()
        return True
    except mysql.connector.Error as e:
        conn.rollback()
        raise e
    finally:
        curs.close()
        conn.close()
