from crud import create_user, verify_user, user_exists, delete_grades_bulk, _connect, USERS_TABLE
import mysql.connector

def verify_auth_flow():
    print("Verifying Authentication Flow...")
    
    test_user = "test_auth_user"
    test_pass = "secure_password_123"
    
    # Clean up any previous test run
    conn = _connect()
    curs = conn.cursor()
    curs.execute(f"DELETE FROM {USERS_TABLE} WHERE username = %s", (test_user,))
    conn.commit()
    curs.close()
    conn.close()
    
    # 1. Verify User Does Not Exist
    if user_exists(test_user):
        print("FAIL: User should not exist yet.")
        return False
    print("PASS: User does not exist initially.")
    
    # 2. Register User
    try:
        user_id = create_user(test_user, test_pass)
        print(f"PASS: User created with ID {user_id}")
    except Exception as e:
        print(f"FAIL: Registration failed: {e}")
        return False
        
    # 3. Verify User Exists
    if not user_exists(test_user):
        print("FAIL: User should exist after registration.")
        return False
    print("PASS: User exists after registration.")
    
    # 4. Verify Login (Correct Password)
    if verify_user(test_user, test_pass):
        print("PASS: Login successful with correct password.")
    else:
        print("FAIL: Login failed with correct password.")
        return False
        
    # 5. Verify Login (Incorrect Password)
    if not verify_user(test_user, "wrong_password"):
        print("PASS: Login failed with incorrect password.")
    else:
        print("FAIL: Login succeeded with incorrect password (SECURITY RISK).")
        return False
        
    print("\nALL CHECKS PASSED!")
    return True

if __name__ == "__main__":
    verify_auth_flow()
