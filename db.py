import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="192.168.0.105",      # Not localhost anymore
        user="root",
        password="",
        database="restaurant"
    )
