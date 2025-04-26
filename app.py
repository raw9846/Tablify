from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from db import get_db_connection  # Import your DB connector
from collections import OrderedDict
from decimal import Decimal

app = Flask(__name__)
app.secret_key = 'supersecretkey123'

@app.route('/register', methods=['GET', 'POST'])
def register_page():
    if request.method == 'POST':
        account_id = request.form['account_id']
        password = request.form['password']
        restaurant_name = request.form['restaurant_name']

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if account already exists
        cursor.execute('SELECT * FROM account WHERE Account_id = %s', (account_id,))
        existing_account = cursor.fetchone()

        if existing_account:
            flash('Account ID already exists. Please log in.', 'warning')
            return redirect(url_for('login'))

        # Insert new account
        try:
            cursor.execute('''
                INSERT INTO account (Account_id, Password, RestaurantName)
                VALUES (%s, %s, %s)
            ''', (account_id, password, restaurant_name))
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            conn.rollback()
            flash('Error creating account.', 'danger')
            print(e)
        finally:
            cursor.close()
            conn.close()

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        account_id = request.form['account_id']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM account WHERE Account_id = %s", (account_id,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        # Password is plain text (not hashed)
        if user and user['Password'] == password:
            session['Account_id'] = user['Account_id']
            session['restaurant'] = user['RestaurantName']
            flash('Login successful!', 'success')
            return redirect(url_for('menu_page'))  # Redirect to menu page
        else:
            flash('Invalid credentials. Please try again.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

    
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
    if 'Account_id' not in session:
        flash('Please sign in first.', 'warning')
        return redirect(url_for('login'))
    
    account_id = session['Account_id'] 
    
    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM menuitems WHERE Account_id = %s',(account_id,))    
    items  = cursor.fetchall()
    cursor.close(); conn.close()
    return render_template('menu.html', items=items)


@app.route('/recipe')
def recipes_page():
    if 'Account_id' not in session:
        flash('Please sign in first.', 'warning')
        return redirect(url_for('login'))
    
    account_id = session['Account_id']
    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute('''
      SELECT
        m.Name AS name,
        i.Name AS ingredient
      FROM ingredients_for_recipes r
      JOIN menuitems   m ON r.FoodID       = m.FoodID
      JOIN ingredients i ON r.IngredientID = i.IngredientID
      WHERE m.Account_id = %s
      ORDER BY m.Name
    ''', (account_id,))

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    grouped = OrderedDict()
    for row in rows:
        grouped.setdefault(row['name'], []).append(row['ingredient'])

    recipes = [{'name': name, 'ingredients': ings} for name, ings in grouped.items()]
    return render_template('recipe.html', recipes=recipes)

@app.route('/ingredients')
def ingredients_page():
    if 'Account_id' not in session:
        flash('Please sign in first.', 'warning')
        return redirect(url_for('login'))
    
    account_id = session['Account_id'] 
    
    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('''
      SELECT
        i.IngredientID AS IngredientID,
        i.Name AS Name,
        s.SupplierID AS SupplierID,
        s.SupplierName AS SupplierName,
        i.NumInventory AS NumInventory
      FROM ingredients i
      JOIN suppliers s
        ON i.SupplierID = s.SupplierID
        WHERE i.Account_id = %s
    ''', (account_id,))
    ingredients = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('ingredients.html', ingredients=ingredients)


@app.route('/tables')
def tables_page():
    return render_template('tables.html')

#@app.route('/register')
##   return render_template('register.html')

# ========= EDIT FUNCTION FOR MENU PAGE (prob useful for other pages too) ===========

@app.route('/api/menu_ing/<int:food_id>')
# get the ingredients for a specifc menu
def api_menu_ing(food_id):
    account_id = session['Account_id']
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute(
      'SELECT * FROM menuitems '
      'WHERE FoodID=%s AND Account_id=%s',
      (food_id, account_id)
    )
    item = cur.fetchone() or {}

    cur.execute(
      'SELECT IngredientID '
      'FROM ingredients_for_recipes '
      'WHERE FoodID=%s AND Account_id=%s',
      (food_id, account_id)
    )
    item['ingredients'] = [i['IngredientID'] for i in cur.fetchall()]

    cur.close()
    conn.close()
    return jsonify(item)

@app.route('/api/ing')
#get list of ingredients for the current account
def api_ing():
    account_id = session['Account_id']
    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute('''
      SELECT
        IngredientID,
        Name
      FROM ingredients
      WHERE Account_id = %s
    ''', (account_id,))

    ingredients = cursor.fetchall()

    cursor.close()
    conn.close()
    return jsonify({ 'ingredients': ingredients })


def next_id(cur, table,  col, account_id):
    # choose next id for a table
    cur.execute(f'''
    SELECT COALESCE(MAX({col}), 0) + 1 AS id
      FROM {table}
    WHERE Account_id = %s
    ''', (account_id,))

    return cur.fetchone()['id']

@app.route('/api/new_ing/<string:ing_name>/<string:supplier_name>', methods=['POST'])
def api_new_ing(ing_name, supplier_name):
    #put new ingredient and supplier into the database
    account_id = session['Account_id']
    conn       = get_db_connection()
    cur        = conn.cursor(dictionary=True)

    # Create the supplier
    sup_id = next_id(cur, 'suppliers', 'SupplierID', account_id)
    cur.execute(
        'INSERT INTO suppliers (SupplierID, SupplierName, Account_id) '
        'VALUES (%s, %s, %s)',
        (sup_id, supplier_name, account_id)
    )

    # Create the ingredient with zero inventory
    ing_id = next_id(cur, 'ingredients', 'IngredientID', account_id)
    cur.execute(
        'INSERT INTO ingredients '
        '(IngredientID, Name, SupplierID, NumInventory, Account_id) '
        'VALUES (%s, %s, %s, 0, %s)',
        (ing_id, ing_name, sup_id, account_id)
    )

    conn.commit()
    cur.close()
    conn.close()
    return '', 201
    
@app.route('/api/new_menu/<string:name>/<float:price>', methods=['POST'])
def api_new_menu(name, price):
    #put new menu item into the database
    price = Decimal(str(price))  # convert float→string→Decimal
    account_id = session['Account_id']
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    # Create the menu item
    food_id = next_id(cur, 'menuitems', 'FoodID', account_id)
    cur.execute(
        'INSERT INTO menuitems (FoodID, Name, Price, Account_id) '
        'VALUES (%s, %s, %s, %s)',
        (food_id, name, price, account_id)
    )

    conn.commit()
    cur.close()
    conn.close()
    return '', 201

@app.route('/api/menu_add_ing/<int:food_id>/<int:ing_id>', methods=['POST'])
def add_menu_ingredient(food_id, ing_id):
    # Add one ingredient from a menu item
    account_id = session['Account_id']
    conn = get_db_connection()
    cur  = conn.cursor()
    cur.execute(
        'INSERT IGNORE INTO ingredients_for_recipes '
        '(IngredientID, FoodID, Account_id) VALUES (%s, %s, %s)',
        (ing_id, food_id, account_id)
    )
    conn.commit()
    cur.close(); conn.close()
    return '', 204

@app.route('/api/menu_rmv_ing/<int:food_id>/<int:ing_id>', methods=['DELETE'])
def remove_menu_ingredient(food_id, ing_id):
    # Remove one ingredient from a menu item
    account_id = session['Account_id']
    conn = get_db_connection()
    cur  = conn.cursor()
    cur.execute(
        'DELETE FROM ingredients_for_recipes '
        'WHERE IngredientID=%s AND FoodID=%s AND Account_id=%s',
        (ing_id, food_id, account_id)
    )
    conn.commit()
    cur.close(); conn.close()
    return '', 204

@app.route('/api/edit_menu/<int:food_id>/<string:name>/<float:price>',methods=['PUT'])
def api_edit_menu(food_id, name, price):
    # Edit a menu item
    account_id = session['Account_id']
    conn       = get_db_connection()
    cur        = conn.cursor()

    price = Decimal(str(price))

    # Perform the update, scoped to this account
    cur.execute(
        'UPDATE menuitems '
        '   SET Name = %s, Price = %s '
        ' WHERE FoodID = %s AND Account_id = %s',
        (name, price, food_id, account_id)
    )

    conn.commit()
    cur.close()
    conn.close()
    return '', 204

@app.route('/api/increment_inventory/<int:ing_id>', methods=['PUT'])
def api_increment_inventory(ing_id):
    # Increment the inventory of an ingredient
    account_id = session['Account_id']
    conn       = get_db_connection()
    cur        = conn.cursor()

    # Perform the update, scoped to this account
    cur.execute(
        'UPDATE ingredients '
        '   SET NumInventory = NumInventory + 1 '
        ' WHERE IngredientID = %s AND Account_id = %s',
        (ing_id, account_id)
    )

    conn.commit()
    cur.close()
    conn.close()
    return '', 204

if __name__ == '__main__':
    app.run(debug=True)

