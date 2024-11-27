from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import sqlite3
import pandas as pd
from models.recommendation import recommend_products
import json

app = Flask(__name__)
app.secret_key = 'Shubham@123'  # Change this to a secure random key
DATABASE = 'users.db'

# Function to connect to the SQLite database
def get_db_connection(DATABASE=DATABASE):
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/',methods=['GET'])
def home():
    return render_template('login.html')

# Route for the login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user is None:
            flash('Username does not exist. Please sign up.', 'error')
            return redirect(url_for('signup'))
        elif user['password'] != password:
            flash('Incorrect password. Please try again.', 'error')
            return redirect(url_for('login'))
        else:
            session['user_id'] = user['id']
            flash('Login successful!', 'success')
            return redirect(url_for('main'))
    return render_template('login.html')

# Route for the signup page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists. Please choose another one.', 'error')
            return redirect(url_for('signup'))
        finally:
            conn.close()

    return render_template('signup.html')

# Route for the main page after login
@app.route('/main')
def main():
    user_id = session.get('user_id')  # Get the logged-in user's ID from session
    if not user_id:
        flash('Please log in to see recommendations.', 'error')
        return redirect(url_for('login'))

    # Assuming you want to use 'orders.db' as the database for product recommendations
    db_name = 'orders.db'
    
    # Call the recommend_products function with the required parameters
    recommendations = recommend_products(db_name, user_id)

    # Load the products from the CSV file as you were doing before
    df = pd.read_csv('GroceryProducts.csv')  # Update the path to your CSV file
    products = df.to_dict(orient='records')  # Convert DataFrame to a list of dictionaries

    # Render the main page with the products and recommendations
    return render_template('main.html', products=products, recommendations=recommendations)

@app.route('/update_cart', methods=['GET', 'POST'])
def update_cart():
    if request.method == 'POST':
        try:
            # Get cart data from the AJAX call
            cart_data = request.form.get('cart')  # Cart data as a JSON string
            if cart_data:
                cart_data = json.loads(cart_data)  # Convert to Python list

            user_id = session.get('user_id')  # Assume user_id is stored in session

            # Connect to the database and update cart for the current user
            with get_db_connection() as conn:
                # Fetch existing cart data for the user
                current_cart = conn.execute(
                    '''SELECT cart FROM users WHERE id = ?''', (user_id,)
                ).fetchone()

                # If user has an existing cart, merge with new cart items
                if current_cart and current_cart['cart']:
                    existing_cart = json.loads(current_cart['cart'])
                else:
                    existing_cart = []

                # Extend existing cart with new items and convert back to JSON
                existing_cart.extend(cart_data)
                updated_cart_json = json.dumps(existing_cart)

                # Update the user's cart in the database
                conn.execute(
                    '''UPDATE users SET cart = ? WHERE id = ?''', 
                    (updated_cart_json, user_id)
                )
                conn.commit()

            return jsonify({"status": "success", "message": "Cart updated successfully!"})

        except Exception as e:
            print('Error updating cart:', e)
            return jsonify({"status": "error", "message": "Failed to update cart."}), 500


@app.route('/cart', methods=['GET', 'POST'])
def cart():
    if request.method == 'POST':
        # Logic to update cart items based on form data
        cart_data = request.form.get('cart')  # Get the cart data from the AJAX call
        cart_items = json.loads(cart_data)  # Load it as a Python object
    
        # Store the cart items into the database
        with get_db_connection('orders.db') as conn:
            for item in cart_items:
                conn.execute('''
                    INSERT INTO orders (user_id, product_id, quantity)
                    VALUES (?, ?, ?)
                ''', (session.get('user_id'), item['id'], item['quantity']))  # Assuming user_id is stored in session

            conn.commit()
        
        return jsonify({"status": "success", "message": "Cart updated successfully!"})

    # Fetch cart items from the database
    user_id = session.get('user_id')  # Get the logged-in user's ID from session
    cart_items = []  # Initialize the cart items list

    with get_db_connection() as conn:
        # Retrieve cart items from the orders table for the current user
        cart_items = conn.execute('''
            SELECT cart FROM users WHERE user_id = ?
        ''', (user_id,)).fetchall()
    
    print(cart_items)

    # Prepare cart items for rendering
    cart_items_list = [{'id': item['product_id'], 'quantity': item['quantity']} for item in cart_items]

    # Calculate total price - You might want to fetch product prices from the products table
    total_price = 0
    for item in cart_items_list:
        product = conn.execute('''
            SELECT Price FROM products WHERE ID = ?
        ''', (item['id'],)).fetchone()
        if product:
            total_price += product['Price'] * item['quantity']

    return render_template('cart.html', cart_items=cart_items_list, total_price=total_price)


# Route for checkout
@app.route('/checkout', methods=['POST'])
def checkout():
    # Logic to process checkout, save to orders.db
    # Fetch the cart items from session or database
    flash('Order has been placed successfully!', 'success')
    return redirect(url_for('main'))

# Route for logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)