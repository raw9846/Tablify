from flask import Flask, jsonify
from db import get_db_connection  # Import your DB connector

app = Flask(__name__)

@app.route('/test-db')
def test_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES;")
    tables = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"tables": [table[0] for table in tables]}


@app.route('/restaurant', methods=['GET'])
def get_restaurants():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM restaurants')  # replace with your table name
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(rows)  # Sends the rows as JSON

@app.route('/restaurant/count', methods=['GET'])
def get_menu_count():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    # change `menu_item` below to whatever your test-db returned
    cursor.execute('SELECT COUNT(*) AS count FROM `menuitems`;')
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify({'count': result['count']})



if __name__ == '__main__':
    app.run(debug=True)

