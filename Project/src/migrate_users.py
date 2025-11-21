import mysql.connector
from db import _connect, TABLE_NAME, CATEGORIES_TABLE, SUBJECTS_TABLE

def migrate():
    conn = _connect()
    try:
        cursor = conn.cursor()
        
        # 1. Migrate GRADES table
        print(f"Checking {TABLE_NAME}...")
        cursor.execute(f"SHOW COLUMNS FROM {TABLE_NAME} LIKE 'username'")
        if not cursor.fetchone():
            print(f"Adding username column to {TABLE_NAME}...")
            # Add column with default value 'admin' for existing records
            cursor.execute(f"ALTER TABLE {TABLE_NAME} ADD COLUMN username VARCHAR(255) NOT NULL DEFAULT 'admin' AFTER id")
            # Drop old index if exists
            try:
                cursor.execute(f"DROP INDEX idx_subject_category ON {TABLE_NAME}")
            except mysql.connector.Error:
                pass
            # Add new index
            cursor.execute(f"CREATE INDEX idx_user_subject_category ON {TABLE_NAME} (username, Subject, Category)")
            print(f"Migrated {TABLE_NAME}")
        else:
            print(f"{TABLE_NAME} already has username column")

        # 2. Migrate CATEGORIES table
        print(f"Checking {CATEGORIES_TABLE}...")
        cursor.execute(f"SHOW COLUMNS FROM {CATEGORIES_TABLE} LIKE 'username'")
        if not cursor.fetchone():
            print(f"Adding username column to {CATEGORIES_TABLE}...")
            cursor.execute(f"ALTER TABLE {CATEGORIES_TABLE} ADD COLUMN username VARCHAR(255) NOT NULL DEFAULT 'admin' AFTER id")
            
            # Drop old unique key
            try:
                cursor.execute(f"DROP INDEX unique_subject_category ON {CATEGORIES_TABLE}")
            except mysql.connector.Error:
                pass
                
            # Add new unique key
            cursor.execute(f"CREATE UNIQUE INDEX unique_user_subject_category ON {CATEGORIES_TABLE} (username, Subject, CategoryName)")
            print(f"Migrated {CATEGORIES_TABLE}")
        else:
            print(f"{CATEGORIES_TABLE} already has username column")

        # 3. Migrate SUBJECTS table
        print(f"Checking {SUBJECTS_TABLE}...")
        cursor.execute(f"SHOW COLUMNS FROM {SUBJECTS_TABLE} LIKE 'username'")
        if not cursor.fetchone():
            print(f"Adding username column to {SUBJECTS_TABLE}...")
            cursor.execute(f"ALTER TABLE {SUBJECTS_TABLE} ADD COLUMN username VARCHAR(255) NOT NULL DEFAULT 'admin' AFTER id")
            
            # Drop old index/unique constraint
            try:
                cursor.execute(f"DROP INDEX name ON {SUBJECTS_TABLE}") # Unique constraint usually named after column
            except mysql.connector.Error:
                pass
            try:
                cursor.execute(f"DROP INDEX idx_name ON {SUBJECTS_TABLE}")
            except mysql.connector.Error:
                pass

            # Add new constraints
            cursor.execute(f"CREATE UNIQUE INDEX unique_user_subject ON {SUBJECTS_TABLE} (username, name)")
            cursor.execute(f"CREATE INDEX idx_user_name ON {SUBJECTS_TABLE} (username, name)")
            print(f"Migrated {SUBJECTS_TABLE}")
        else:
            print(f"{SUBJECTS_TABLE} already has username column")

        conn.commit()
        print("Migration completed successfully!")

    except mysql.connector.Error as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    migrate()
