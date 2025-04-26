import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host= "172.19.0.1",      # Not localhost anymore
        user="root",
        password="",
        database="restaurant"
    )
