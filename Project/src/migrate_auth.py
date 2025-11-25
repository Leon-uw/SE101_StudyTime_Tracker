import mysql.connector
from db import _connect, USERS_TABLE, USERS_DDL

def migrate_auth():
    print(f"Migrating auth schema...")
    conn = _connect()
    try:
        cursor = conn.cursor()
        
        # Create users table
        print(f"Creating table {USERS_TABLE} if not exists...")
        cursor.execute(USERS_DDL)
        
        print("Migration completed successfully!")
        conn.commit()
        
    except mysql.connector.Error as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    migrate_auth()
