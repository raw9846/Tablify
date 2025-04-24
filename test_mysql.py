import mysql.connector

try:
    conn = mysql.connector.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password="",  # If you set a password, put it here
        database="restaurant"
    )
    print("Connection successful!")
    conn.close()
except mysql.connector.Error as err:
    print("Connection error:", err)
