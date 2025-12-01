import pymysql
import os
import dotenv

dotenv.load_dotenv()

def connection():
    #establish connection by using the connector and adding the necessary things in .env
    dbconnection = pymysql.connect(
        user = os.getenv('Userid'),
        password = os.getenv('Password'),
        host = 'riku.shoshin.uwaterloo.ca',
        database = 'SE101_Team_21'
    )
    cursor = dbconnection.cursor()
    return dbconnection, cursor
    #dbconnection.close()
