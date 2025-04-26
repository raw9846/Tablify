from flask import Flask, render_template, request, redirect, url_for, session, flash
from db import get_db_connection  # Import your DB connector
from collections import OrderedDict

app = Flask(__name__)
app.secret_key = 'supersecretkey123'

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
    # clear everything in session
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
        m.Name       AS name,
        i.Name       AS ingredient
      FROM ingredients_for_recipes r
      JOIN menuitems   m ON r.FoodID       = m.FoodID
      JOIN ingredients i ON r.IngredientID = i.IngredientID
      WHERE m.Account_id = %s
      ORDER BY m.Name
    ''', (account_id,))

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    # group ingredients under each recipe name
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
        i.IngredientID     AS IngredientID,
        i.Name             AS Name,
        s.SupplierID       AS SupplierID,
        s.SupplierName     AS SupplierName,
        i.NumInventory   AS NumInventory
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

@app.route('/register')
def register_page():
    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)

