import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = 'riku.shoshin.uwaterloo.ca'
DB_USER = os.getenv("Userid", "root")
DB_PASS = os.getenv("Password", "")
DB_NAME = 'SE101_Team_21'
TABLE_NAME = f"{DB_USER}_grades"

def add_is_prediction_column():
    conn = mysql.connector.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME
    )
    cursor = conn.cursor()
    try:
        # Check if column exists
        cursor.execute(f"SHOW COLUMNS FROM {TABLE_NAME} LIKE 'IsPrediction'")
        result = cursor.fetchone()
        if not result:
            print("Adding IsPrediction column...")
            cursor.execute(f"ALTER TABLE {TABLE_NAME} ADD COLUMN IsPrediction BOOLEAN DEFAULT FALSE")
            conn.commit()
            print("Column added successfully.")
        else:
            print("IsPrediction column already exists.")
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    add_is_prediction_column()
