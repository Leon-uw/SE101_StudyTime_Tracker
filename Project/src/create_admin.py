from crud import create_user, user_exists
import sys

def create_admin():
    username = "admin"
    password = "admin_password_123"
    
    if user_exists(username):
        print(f"User '{username}' already exists.")
        return

    try:
        create_user(username, password)
        print(f"Successfully created user '{username}' with password '{password}'")
    except Exception as e:
        print(f"Failed to create admin user: {e}")

if __name__ == "__main__":
    create_admin()
