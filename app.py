from flask import Flask, jsonify, render_template
from db import get_db_connection  # Import your DB connector
from collections import OrderedDict

app = Flask(__name__)

@app.route('/-testdb')
def test_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES;")
    tables = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"tables": [table[0] for table in tables]}

@app.route('/menu')
def menu_page():
    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM menuitems')
    items  = cursor.fetchall()
    cursor.close(); conn.close()
    return render_template('menu.html', items=items)


@app.route('/recipe')
def recipes_page():
    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # fetch recipe name + ingredient name via your M:N table
    cursor.execute('''
      SELECT
        m.Name           AS name,
        i.Name           AS ingredient
      FROM ingredients_for_recipes r
      JOIN menuitems            m ON r.FoodID       = m.FoodID
      JOIN ingredients          i ON r.IngredientID = i.IngredientID
      ORDER BY m.Name
    ''')
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    # group ingredients under each recipe name
    grouped = OrderedDict()
    for row in rows:
        grouped.setdefault(row['name'], []).append(row['ingredient'])

    # build list for template
    recipes = [{'name': name, 'ingredients': ings}
               for name, ings in grouped.items()]

    return render_template('recipe.html', recipes=recipes)

@app.route('/ingredients')
def ingredients_page():
    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('''
      SELECT
        i.IngredientID     AS IngredientID,
        i.Name             AS Name,
        s.SupplierID       AS SupplierID,
        s.SupplierName     AS SupplierName,
        i.NumInventory   AS NumInventory
      FROM ingredients i
      JOIN suppliers s
        ON i.SupplierID = s.SupplierID
    ''')
    ingredients = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('ingredients.html', ingredients=ingredients)


@app.route('/tables')
def tables_page():
    return render_template('tables.html')

@app.route('/signin')
def signin_page():
    return render_template('signin.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)

