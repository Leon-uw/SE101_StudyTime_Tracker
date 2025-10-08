DEBUG = False;

import pymysql
import os
import getpass
import argparse
import datetime

task = []
'''task()'''

class OptionalPassword(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        # If no value is provided, set the password to True (flag-like behavior)
        if values is None:
            setattr(namespace, self.dest, True)
        else:
            setattr(namespace, self.dest, values)

# parse function

def parseInput(defaultHost, defaultDatabase, defaultUser, defaultPassword,defaultID):    
    # Create the argument parser
    parser = argparse.ArgumentParser(description="Parse command-line arguments.")

    # Add the arguments for hostname, database, and username
    parser.add_argument('-H', '--hostname', default=defaultHost, help="Hostname")
    parser.add_argument('-d', '--database', default=defaultDatabase, help="Database")
    parser.add_argument('-u', '--username', default=defaultUser, help="Username")
    parser.add_argument('-s', '--studentID', default=defaultID, help="StudentID")
    
    # Add the password argument which may or may not take a parameter
    parser.add_argument('-p', '--password', nargs='?', action=OptionalPassword, help="Password (optional)")
    
    # Parse the arguments
    args = parser.parse_args()

    # Prompt if -p with no parameter
    # Set to default if no -p
    if args.password is None:
        args.password = defaultPassword
    elif args.password is True:
        args.password = getpass.getpass(
            prompt=f"Enter MySQL password for user '{args.username}' on host '{args.hostname}': ")

    return args

################################################################################
#
# connect2DB connects to the database server with passed parameters
#

def connect2DB(username=None, password=None, db=None):
    """
    Connect to database using provided credentials or environment variables
    """
    # Use environment variables as defaults if parameters not provided
    username = username or os.getenv('TODO_DB_USER', 'default_user')
    password = password or os.getenv('TODO_DB_PASSWORD', 'default_password') 
    db = db or os.getenv('TODO_DB_NAME', 'default_db')
    
    try:
        # Establishing the connection
        connection = pymysql.connect(
            host     = "riku.shoshin.uwaterloo.ca",
            user     = username,
            database = db,
            password = password
        )
        
        return connection

    except pymysql.MySQLError as err:
        print(f"Error: {err}")
        return None

################################################################################
#
# queryDatabase() executes the query and returns the cursor with the results
#

def queryDatabase(connection):
    try:
        cursor = connection.cursor()

        query = f""
        
        cursor.execute(query)
        return cursor
        
    except pymysql.Error as err:
        print(f"Query Error: {err}")
        return None
    
def add(task, username=None, password=None, database=None):
    """
    Add a task to the database
    
    Args:
        task: Tuple containing (item, type, started, due, done)
        username: Database username (optional, uses env var if not provided)
        password: Database password (optional, uses env var if not provided) 
        database: Database name (optional, uses env var if not provided)
    """
    
    connection = connect2DB(username, password, database)
    if connection is None:
        return False
    
    cursor = connection.cursor()

    #5 elements
    if not isinstance(task, tuple) or len(task) != 5:
        print("Error: must have exactly 5 elements (item, type, started, due, done).")
        connection.close()
        return False
    #unpack our package
    item, t_type, started, due, done = task
    #check item and task type are strings
    if not isinstance(item, str) or not isinstance(t_type, str):
        print("Error: Item and type must be strings.")
        connection.close()
        return False
    #check started and due are datetime objects
    if not isinstance(started, datetime.datetime) or not isinstance(due, datetime.datetime):
        print("Error: started and due must be datetime objects.")
        connection.close()
        return False
    #check done is blanck or datetime object
    if done is not None and not isinstance(done, datetime.datetime):
        print("Error: done date must be a datetime object or be blank.")
        connection.close()
        return False
    #is item already there - check if item exists in database
    try:
        # Query to check if item already exists
        check_query = "SELECT COUNT(*) FROM ToDoData WHERE item = %s"
        cursor.execute(check_query, (item,))
        
        # Get the count result
        result = cursor.fetchone()
        count = result[0]
        
        if count > 0:
            print(f"Error: Task with item '{item}' already exists.")
            cursor.close()
            connection.close()
            return False
            
    except pymysql.Error as err:
        print(f"Query Error: {err}")
        cursor.close()
        connection.close()
        return False
    
    # If we get here, the item doesn't exist, so insert the new task
    try:
        insert_query = """
        INSERT INTO ToDoData (item, type, started, due, done) 
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (item, t_type, started, due, done))
        connection.commit()  # Important: commit the transaction
        
        print(f"Task '{item}' added successfully.")
        cursor.close()
        connection.close()
        return True
        
    except pymysql.Error as err:
        print(f"Insert Error: {err}")
        connection.rollback()  # Undo any changes if error occurs
        cursor.close()
        connection.close()
        return False
