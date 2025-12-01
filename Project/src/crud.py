import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

# Conditional database import
if os.getenv("USE_LOCAL_DB", "").lower() == "true":
    from db_local import init_db, _connect, TABLE_NAME, CATEGORIES_TABLE, SUBJECTS_TABLE, USERS_TABLE
    # SQLite uses different placeholder syntax
    PARAM_PLACEHOLDER = "?"
    DICT_CURSOR = None  # SQLite doesn't use DictCursor
else:
    from db import init_db, _connect, TABLE_NAME, CATEGORIES_TABLE, SUBJECTS_TABLE, USERS_TABLE
    import pymysql
    from pymysql.cursors import DictCursor as DICT_CURSOR
    PARAM_PLACEHOLDER = "%s"
from werkzeug.security import generate_password_hash, check_password_hash


def _get_dict_cursor(conn):
    """Get a dictionary cursor compatible with both PyMySQL and SQLite."""
    if DICT_CURSOR:
        return conn.cursor(DICT_CURSOR)
    else:
        # For SQLite, use row_factory
        conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        return conn.cursor()


def _column_exists(conn, table, col):
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*)
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
          AND COLUMN_NAME = %s
    """, (table, col))
    exists = cur.fetchone()[0] > 0
    cur.close()
    return exists

def ensure_schema():
    """Add Position column if missing and backfill it deterministically."""
    conn = _connect()
    try:
        # 1) Add column if missing
        if not _column_exists(conn, TABLE_NAME, "Position"):
            cur = conn.cursor()
            cur.execute(f"ALTER TABLE {TABLE_NAME} ADD COLUMN Position INT NOT NULL DEFAULT 0")
            conn.commit()
            cur.close()

        # 2) Backfill per user if everything is zero/unset
        _backfill_positions(conn)

    finally:
        conn.close()

def _backfill_positions(conn):
    """For each username, set Position = 0..n-1 using current id order (stable)."""
    cur = _get_dict_cursor(conn)

    # Find distinct users
    cur.execute(f"SELECT DISTINCT username FROM {TABLE_NAME}")
    users = [r["username"] for r in cur.fetchall()]

    for u in users:
        # Pull all ids for user ordered by existing Position then fallback to id
        cur.execute(
            f"SELECT id FROM {TABLE_NAME} WHERE username=%s ORDER BY Position ASC, id ASC",
            (u,)
        )
        ids = [r["id"] for r in cur.fetchall()]
        # If Position already looks good (strictly increasing from 0), skip
        ok = True
        cur2 = conn.cursor()
        cur2.execute(
            f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE username=%s AND Position NOT BETWEEN 0 AND 1000000",
            (u,)
        )
        if cur2.fetchone()[0] > 0:
            ok = False
        cur2.close()

        if not ids or ok:
            continue

        # Rewrite positions 0..n-1
        upd = conn.cursor()
        for pos, _id in enumerate(ids):
            upd.execute(f"UPDATE {TABLE_NAME} SET Position=%s WHERE id=%s AND username=%s",
                        (pos, _id, u))
        conn.commit()
        upd.close()

    cur.close()

def next_position_for_user(username):
    """Return next integer position for a user's new row."""
    conn = _connect()
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT COALESCE(MAX(Position), -1) + 1 FROM {TABLE_NAME} WHERE username=%s", (username,))
        return int(cur.fetchone()[0] or 0)
    finally:
        cur.close()
        conn.close()


# ============================================================================
# PHASE 8: User Authentication
# ============================================================================

def create_user(username, password):
    """Create a new user with hashed password."""
    conn = _connect()
    try:
        curs = conn.cursor()
        password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        
        query = f"INSERT INTO {USERS_TABLE} (username, password_hash) VALUES (%s, %s)"
        curs.execute(query, (username, password_hash))
        conn.commit()
        return curs.lastrowid
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        curs.close()
        conn.close()

def verify_user(username, password):
    """Verify username and password against database."""
    conn = _connect()
    try:
        curs = _get_dict_cursor(conn)
        query = f"SELECT password_hash FROM {USERS_TABLE} WHERE username = %s"
        curs.execute(query, (username,))
        result = curs.fetchone()
        
        if result and check_password_hash(result['password_hash'], password):
            return True
        return False
    finally:
        curs.close()
        conn.close()

def user_exists(username):
    """Check if a username already exists."""
    conn = _connect()
    try:
        curs = conn.cursor()
        query = f"SELECT id FROM {USERS_TABLE} WHERE username = %s"
        curs.execute(query, (username,))
        return curs.fetchone() is not None
    finally:
        curs.close()
        conn.close()

def set_subject_retirement_status(username: str, subject_name: str, is_retired: bool):
    """
    Placeholder for database function to set the 'is_retired' status of a subject
    in the SUBJECTS_TABLE. This assumes SUBJECTS_TABLE has an 'is_retired' column.
    """
    conn = _connect()
    cur = conn.cursor()
    try:
        cur.execute(
            f"UPDATE {SUBJECTS_TABLE} SET is_retired = %s WHERE username = %s AND name = %s",
            (is_retired, username, subject_name)
        )
        conn.commit()
    finally:
        try: cur.close()
        except: pass
        try: conn.close()
        except: pass

def get_all_grades(username):
    """Get all grade records for a specific user."""
    conn = _connect()
    try:
        curs = _get_dict_cursor(conn)
        curs.execute(
            f"""SELECT id, Subject, Category, StudyTime, AssignmentName,
                    Grade, Weight, IsPrediction, PredictedGrade, Position
                FROM {TABLE_NAME}
                WHERE username = %s
                ORDER BY Position ASC, id ASC""",
            (username,)
        )
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
                'is_prediction': bool(row['IsPrediction']) if 'IsPrediction' in row else False,
                'predicted_grade': row.get('PredictedGrade'),
                'position': row['Position'],
            }
            for row in results
        ]
    finally:
        curs.close()
        conn.close()

def get_all_categories(username, subject=None):
    """Get all category definitions for a user."""
    conn = _connect()
    try:
        curs = _get_dict_cursor(conn)

        if subject:
            curs.execute(f"SELECT * FROM {CATEGORIES_TABLE} WHERE username = %s AND Subject = %s ORDER BY CategoryName", (username, subject))
        else:
            curs.execute(f"SELECT * FROM {CATEGORIES_TABLE} WHERE username = %s ORDER BY Subject, CategoryName", (username,))

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

def get_category_by_id(username, category_id):
    """Get a single category by ID for a user."""
    conn = _connect()
    try:
        curs = _get_dict_cursor(conn)
        curs.execute(f"SELECT * FROM {CATEGORIES_TABLE} WHERE id = %s AND username = %s", (category_id, username))
        row = curs.fetchone()
        if row:
            return {
                'id': row['id'],
                'subject': row['Subject'],
                'name': row['CategoryName'],
                'total_weight': row['TotalWeight'],
                'default_name': row['DefaultName'] or ''
            }
        return None
    finally:
        curs.close()
        conn.close()

def get_categories_as_dict(username):
    """Get categories organized by subject for a user."""
    categories = get_all_categories(username)

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

def add_grade(username, subject, category, study_time, assignment_name, grade, weight, is_prediction=False, predicted_grade=None):
    """Add a new assignment to the database for a user"""
    conn = _connect()
    try:
        curs = conn.cursor()

        curs.execute(f"SELECT COALESCE(MAX(Position), -1) + 1 FROM {TABLE_NAME} WHERE username=%s", (username,))
        next_pos = curs.fetchone()[0]

        query = f"""
        INSERT INTO {TABLE_NAME}
            (username, Subject, Category, StudyTime, AssignmentName, Grade, Weight, IsPrediction, PredictedGrade, Position)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        curs.execute(query, (username, subject, category, study_time, assignment_name, grade, weight, is_prediction, predicted_grade, next_pos))
        conn.commit()
        return curs.lastrowid  # Return the ID of the inserted record
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        curs.close()
        conn.close()

def update_grade(username, grade_id, subject, category, study_time, assignment_name, grade, weight, is_prediction=False, predicted_grade=None):
    """Update an existing grade for a user"""
    conn = _connect()
    try:
        curs = conn.cursor()
        # Ensure we only update if it belongs to the user
        query = f"""
        UPDATE {TABLE_NAME}
        SET Subject = %s, Category = %s, StudyTime = %s, AssignmentName = %s, Grade = %s, Weight = %s, IsPrediction = %s, PredictedGrade = %s
        WHERE id = %s AND username = %s
        """
        curs.execute(query, (subject, category, study_time, assignment_name, grade, weight, is_prediction, predicted_grade, grade_id, username))
        conn.commit()
        return curs.rowcount
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        curs.close()
        conn.close()

def delete_grade(username, grade_id):
    """Delete a single grade for a user"""
    conn = _connect()
    try:
        curs = conn.cursor()
        query = f"DELETE FROM {TABLE_NAME} WHERE id = %s AND username = %s"
        curs.execute(query, (grade_id, username))
        conn.commit()
        return curs.rowcount
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        curs.close()
        conn.close()

def delete_grades_bulk(username, grade_ids):
    """Delete multiple grades for a user"""
    if not grade_ids:
        return 0

    conn = _connect()
    try:
        curs = conn.cursor()
        placeholders = ','.join(['%s'] * len(grade_ids))
        # Add username check
        query = f"DELETE FROM {TABLE_NAME} WHERE id IN ({placeholders}) AND username = %s"
        # Append username to the end of parameters
        params = tuple(grade_ids) + (username,)
        curs.execute(query, params)
        conn.commit()
        return curs.rowcount
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        curs.close()
        conn.close()

def recalculate_and_update_weights(username, subject, category_name):
    """Recalculate weights for all assignments in a category for a user."""
    conn = _connect()
    try:
        curs = _get_dict_cursor(conn)

        # Get category definition to get total_weight
        curs.execute(
            f"SELECT TotalWeight FROM {CATEGORIES_TABLE} WHERE username = %s AND Subject = %s AND CategoryName = %s",
            (username, subject, category_name)
        )
        category = curs.fetchone()

        if not category:
            return 0  # Category doesn't exist

        total_weight = category['TotalWeight']

        # Count assignments in this category
        curs.execute(
            f"SELECT COUNT(*) as count FROM {TABLE_NAME} WHERE username = %s AND Subject = %s AND Category = %s",
            (username, subject, category_name)
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
            WHERE username = %s AND Subject = %s AND Category = %s
        """
        curs.execute(update_query, (new_weight, username, subject, category_name))
        conn.commit()

        return curs.rowcount
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        curs.close()
        conn.close()

def add_category(username, subject, category_name, total_weight, default_name=''):
    """Add a new category definition to the database for a user"""
    conn = _connect()
    try:
        curs = conn.cursor()
        query = f"""
        INSERT INTO {CATEGORIES_TABLE} (username, Subject, CategoryName, TotalWeight, DefaultName)
        VALUES (%s, %s, %s, %s, %s)
        """
        curs.execute(query, (username, subject, category_name, total_weight, default_name))
        conn.commit()
        return curs.lastrowid
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        curs.close()
        conn.close()

def update_category(username, category_id, subject, category_name, total_weight, default_name=''):
    """Update an existing category definition for a user"""
    conn = _connect()
    try:
        curs = conn.cursor()
        query = f"""
        UPDATE {CATEGORIES_TABLE}
        SET Subject = %s, CategoryName = %s, TotalWeight = %s, DefaultName = %s
        WHERE id = %s AND username = %s
        """
        curs.execute(query, (subject, category_name, total_weight, default_name, category_id, username))
        conn.commit()
        return curs.rowcount
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        curs.close()
        conn.close()

def update_assignment_names_for_category(username, subject, category_name, old_pattern, new_pattern):
    """
    Update assignment names that match the old naming pattern to use the new pattern.
    
    For example, if old_pattern is "Quiz #" and new_pattern is "Test #", this will
    update assignments named "Quiz 1", "Quiz 2" to "Test 1", "Test 2".
    
    The pattern uses "#" as a placeholder for the number.
    """
    import re
    conn = _connect()
    try:
        # Get all assignments for this category
        curs = _get_dict_cursor(conn)
        curs.execute(
            f"""SELECT id, AssignmentName FROM {TABLE_NAME} 
                WHERE username = %s AND Subject = %s AND Category = %s""",
            (username, subject, category_name)
        )
        assignments = curs.fetchall()
        
        if not assignments or not old_pattern or not new_pattern:
            return 0
        
        # Split old pattern by # to get prefix and suffix
        old_parts = old_pattern.split('#')
        old_prefix = old_parts[0] if len(old_parts) > 0 else ''
        old_suffix = old_parts[1] if len(old_parts) > 1 else ''
        
        # Split new pattern by # to get prefix and suffix
        new_parts = new_pattern.split('#')
        new_prefix = new_parts[0] if len(new_parts) > 0 else ''
        new_suffix = new_parts[1] if len(new_parts) > 1 else ''
        
        if not old_prefix and not old_suffix:
            return 0
        
        # Create regex pattern to match old naming scheme
        # Escape special regex characters
        escaped_old_prefix = re.escape(old_prefix)
        escaped_old_suffix = re.escape(old_suffix)
        pattern = re.compile(f'^{escaped_old_prefix}(\\d+){escaped_old_suffix}$', re.IGNORECASE)
        
        updated_count = 0
        update_curs = conn.cursor()
        
        for assignment in assignments:
            match = pattern.match(assignment['AssignmentName'].strip())
            if match:
                # Extract the number
                number = match.group(1)
                # Create the new name using the new pattern (number goes exactly where # is)
                new_name = f"{new_prefix}{number}{new_suffix}"
                
                # Update the assignment name
                update_curs.execute(
                    f"UPDATE {TABLE_NAME} SET AssignmentName = %s WHERE id = %s AND username = %s",
                    (new_name, assignment['id'], username)
                )
                updated_count += update_curs.rowcount
        
        conn.commit()
        update_curs.close()
        return updated_count
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        curs.close()
        conn.close()

def delete_category(username, category_id):
    """Delete a category definition for a user"""
    conn = _connect()
    try:
        curs = conn.cursor()
        query = f"DELETE FROM {CATEGORIES_TABLE} WHERE id = %s AND username = %s"
        curs.execute(query, (category_id, username))
        conn.commit()
        return curs.rowcount
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        curs.close()
        conn.close()

def get_total_weight_for_subject(username, subject, exclude_category_id=None):
    """Calculate total weight of all categories for a subject for a user."""
    conn = _connect()
    try:
        curs = _get_dict_cursor(conn)

        if exclude_category_id:
            query = f"""
                SELECT SUM(TotalWeight) as total
                FROM {CATEGORIES_TABLE}
                WHERE username = %s AND Subject = %s AND id != %s
            """
            curs.execute(query, (username, subject, exclude_category_id))
        else:
            query = f"""
                SELECT SUM(TotalWeight) as total
                FROM {CATEGORIES_TABLE}
                WHERE username = %s AND Subject = %s
            """
            curs.execute(query, (username, subject))

        result = curs.fetchone()
        return result['total'] or 0
    finally:
        curs.close()
        conn.close()

# ============================================================================
# PHASE 7: Subject CRUD Operations
# ============================================================================

def get_all_subjects(username, include_retired=False):
    """Get all subjects for a user. By default excludes retired subjects."""
    conn = _connect()
    try:
        curs = _get_dict_cursor(conn)
        if include_retired:
            curs.execute(f"SELECT * FROM {SUBJECTS_TABLE} WHERE username = %s ORDER BY name", (username,))
        else:
            # Exclude retired subjects (is_retired = FALSE or NULL)
            curs.execute(f"SELECT * FROM {SUBJECTS_TABLE} WHERE username = %s AND (is_retired = FALSE OR is_retired IS NULL) ORDER BY name", (username,))
        results = curs.fetchall()

        return [
            {
                'id': row['id'],
                'name': row['name'],
                'created_at': row['created_at'],
                'is_retired': row.get('is_retired', False) or False
            }
            for row in results
        ]
    finally:
        curs.close()
        conn.close()

def get_retired_subjects(username):
    """Get all retired subjects for a user."""
    conn = _connect()
    try:
        curs = _get_dict_cursor(conn)
        curs.execute(f"SELECT * FROM {SUBJECTS_TABLE} WHERE username = %s AND is_retired = TRUE ORDER BY name", (username,))
        results = curs.fetchall()

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
        curs.close()
        conn.close()

def add_subject(username, name):
    """Add a new subject for a user."""
    conn = _connect()
    try:
        curs = conn.cursor()
        query = f"""
        INSERT INTO {SUBJECTS_TABLE} (username, name)
        VALUES (%s, %s)
        """
        curs.execute(query, (username, name))
        conn.commit()
        return curs.lastrowid
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        curs.close()
        conn.close()

def delete_subject(username, subject_id):
    """Delete a subject for a user."""
    conn = _connect()
    try:
        curs = _get_dict_cursor(conn)

        # First get the subject name, ensuring it belongs to the user
        curs.execute(f"SELECT name FROM {SUBJECTS_TABLE} WHERE id = %s AND username = %s", (subject_id, username))
        subject = curs.fetchone()

        if not subject:
            return 0

        subject_name = subject['name']

        # Delete all assignments for this subject
        curs.execute(f"DELETE FROM {TABLE_NAME} WHERE username = %s AND Subject = %s", (username, subject_name))

        # Delete all categories for this subject
        curs.execute(f"DELETE FROM {CATEGORIES_TABLE} WHERE username = %s AND Subject = %s", (username, subject_name))

        # Delete the subject itself
        curs.execute(f"DELETE FROM {SUBJECTS_TABLE} WHERE id = %s AND username = %s", (subject_id, username))

        conn.commit()
        return curs.rowcount
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        curs.close()
        conn.close()

def get_subject_by_name(username, name):
    """Get a subject by name for a user."""
    conn = _connect()
    try:
        curs = _get_dict_cursor(conn)
        curs.execute(f"SELECT * FROM {SUBJECTS_TABLE} WHERE username = %s AND name = %s", (username, name))
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

def rename_subject(username, old_name, new_name):
    """Renames a subject across all tables for a user."""
    conn = _connect()
    curs = conn.cursor()
    try:
        # Check if new name already exists for this user
        curs.execute(f"SELECT id FROM {SUBJECTS_TABLE} WHERE username = %s AND name = %s", (username, new_name))
        if curs.fetchone():
            raise ValueError(f"Subject '{new_name}' already exists.")

        # Update SUBJECTS_TABLE
        curs.execute(f"UPDATE {SUBJECTS_TABLE} SET name = %s WHERE username = %s AND name = %s", (new_name, username, old_name))
        
        # Update GRADES_TABLE
        curs.execute(f"UPDATE {TABLE_NAME} SET Subject = %s WHERE username = %s AND Subject = %s", (new_name, username, old_name))
        
        # Update CATEGORIES_TABLE
        curs.execute(f"UPDATE {CATEGORIES_TABLE} SET Subject = %s WHERE username = %s AND Subject = %s", (new_name, username, old_name))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        curs.close()
        conn.close()
