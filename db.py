import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host= "127.0.0.1",      # Not localhost anymore
        user="root",
        password="",
        database="restaurant"
    )
