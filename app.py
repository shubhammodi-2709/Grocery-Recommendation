from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import sqlite3
import pandas as pd
import json
import secrets

from Init_model import ProductRecommender
from database_helper.db_init import create_tables

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
DATABASE = 'data.db'

# Helper function to connect to SQLite database
def get_db_connection(DATABASE=DATABASE):
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/', methods=['GET'])
def home():
    # Redirect to login if user is not authenticated
    if 'user_id' in session:
        return redirect(url_for('main'))
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        # Check user credentials
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

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists. Please choose another one.', 'error')
        finally:
            conn.close()

    return render_template('signup.html')

@app.route('/main', methods=['GET'])
def main():
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to access the main page.', 'error')
        return redirect(url_for('login'))

    # Initialize the recommender system
    data_path = "GroceryProducts.csv"  # Path to product dataset
    model_path = "kmeans_model.pkl"    # Path to trained model
    recommender = ProductRecommender(data_path, model_path, n_clusters=5)

    # Train the model if necessary
    if recommender.model is None or 'Cluster' not in recommender.data.columns:
        recommender.train_model()

    # Get the user's cart from the database
    conn = get_db_connection()
    cursor = conn.execute('SELECT cart FROM Users WHERE id = ?', (user_id,))
    user_cart_row = cursor.fetchone()
    conn.close()

    # Parse cart data
    cart = json.loads(user_cart_row['cart']) if user_cart_row and user_cart_row['cart'] else []

    # If the cart is not empty, recommend products based on the first product in the cart
    recommendations = []
    if cart:
        first_product_id = cart[0]['id']  # Get the product ID of the first item in the cart
        recommendations = recommender.recommend_products(product_id=first_product_id)

    # Load all available products
    df = pd.read_csv(data_path)
    products = df.to_dict(orient='records')

    # Match recommendations with product details
    detailed_recommendations = [
        df.loc[df['ID'] == rec['ID']].iloc[0].to_dict()
        for rec in recommendations if not df.loc[df['ID'] == rec['ID']].empty
    ]

    return render_template(
        'main.html',
        products=products,
        recommendations=detailed_recommendations[:6]  # Limit recommendations to top 6
    )

@app.route('/cart', methods=['GET'])
def cart():
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to view your cart.', 'error')
        return redirect(url_for('login'))

    with get_db_connection() as conn:
        cart_data = conn.execute('SELECT cart FROM users WHERE id = ?', (user_id,)).fetchone()
        cart_items = json.loads(cart_data['cart']) if cart_data and cart_data['cart'] else []

        # Calculate total price
        total_price = 0
        for item in cart_items:
            product = conn.execute('SELECT Price FROM products WHERE ID = ?', (item['id'],)).fetchone()
            if product:
                total_price += product['Price'] * item['quantity']

    return render_template('cart.html', cart_items=cart_items, total_price=total_price)

@app.route('/get_cart', methods=['GET'])
def get_cart():
    """Retrieve the user's cart from the database."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'status': 'error', 'message': 'User not logged in'}), 403

    with get_db_connection() as conn:
        cart_data = conn.execute('SELECT cart FROM Users WHERE id = ?', (user_id,)).fetchone()
        cart = json.loads(cart_data['cart']) if cart_data and cart_data['cart'] else []
    
    return jsonify({'status': 'success', 'cart': cart})

@app.route('/update_cart', methods=['POST'])
def update_cart():
    """Update the user's cart in the database."""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'status': 'error', 'message': 'User not logged in'}), 403

        cart_data = request.get_json().get('cart', [])
        with get_db_connection() as conn:
            conn.execute('UPDATE Users SET cart = ? WHERE id = ?', (json.dumps(cart_data), user_id))
            conn.commit()
        
        return jsonify({'status': 'success', 'message': 'Cart updated successfully'})
    except Exception as e:
        print(f"Error updating cart: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to update cart'}), 500

@app.route('/checkout', methods=['POST'])
def checkout():
    """Handle the checkout process."""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'status': 'error', 'message': 'User not logged in'}), 403

        with get_db_connection() as conn:
            cart_data = conn.execute('SELECT cart FROM Users WHERE id = ?', (user_id,)).fetchone()
            cart = json.loads(cart_data['cart']) if cart_data and cart_data['cart'] else []

            # Process orders
            for item in cart:
                conn.execute('''
                    INSERT INTO Orders (user_id, product_id, quantity)
                    VALUES (?, ?, ?)
                ''', (user_id, item['id'], item['quantity']))

            # Clear cart after checkout
            conn.execute('UPDATE Users SET cart = ? WHERE id = ?', (None, user_id))
            conn.commit()
        
        return jsonify({'status': 'success', 'message': 'Checkout successful'})
    except Exception as e:
        print(f"Error during checkout: {e}")
        return jsonify({'status': 'error', 'message': 'Checkout failed'}), 500

@app.route('/confirmation', methods=['GET'])
def confirmation():
    """Render the confirmation page after checkout."""
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to access the confirmation page.', 'error')
        return redirect(url_for('login'))

    # Retrieve the user's order details from the Orders table
    with get_db_connection() as conn:
        orders = conn.execute('''
            SELECT Orders.product_id, Orders.quantity
            FROM Orders
            WHERE Orders.user_id = ?
        ''', (user_id,)).fetchall()

    # Load product details from the CSV file
    df_products = pd.read_csv('GroceryProducts.csv')

    # Map product IDs to product details
    product_details = {}
    for order in orders:
        product_id = order['product_id']
        product = df_products[df_products['ID'] == product_id]
        if not product.empty:
            product_details[product_id] = {
                'ProductName': product['ProductName'].values[0],
                'Price': product['Price'].values[0],
                'Quantity': order['quantity'],
                'Total': product['Price'].values[0] * order['quantity']
            }
        else:
            print(f"Product with ID {product_id} not found in CSV.")


    # Calculate the total amount
    total_amount = sum(item['Total'] for item in product_details.values())

    return render_template('confirmation.html', product_details=product_details, total_amount=total_amount)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)
