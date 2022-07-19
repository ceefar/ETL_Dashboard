# ---- imports ----
 
# for db
import pymysql
import os
from dotenv import load_dotenv

# load environment variables from .env file
load_dotenv()
host = os.environ.get("mysql_host")
user = os.environ.get("mysql_user")
password = os.environ.get("mysql_pass")
database = os.environ.get("mysql_db")

# establish a database connection
connection = pymysql.connect(
    host = host,
    user = user,
    password = password,
    database = database
)

def add_to_db(command):
    """ gets stuff from a db """
    cursor = connection.cursor()
    connection.ping()
    cursor.execute(f"{command}") 
    connection.commit()

def get_from_db(command):
    """ gets stuff from a db, returns the result """
    cursor = connection.cursor()
    connection.ping()
    cursor.execute(f"{command}") 
    myresult = cursor.fetchall()
    connection.commit()
    return(myresult)

# ---- end setup ----