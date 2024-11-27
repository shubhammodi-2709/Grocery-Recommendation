import sqlite3
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key for session management

# Initialize the SQLite database connection
def get_db_connection():
    conn = sqlite3.connect('users.db')  # Database for users and authentication
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name
    return conn

# Checkout route: Handle the user's checkout request
@app.route('/checkout', methods=['POST'])
def checkout():
    if 'username' not in session:
        return jsonify({'error': 'User not logged in'}), 401

    order_data = request.json
    username = session['username']  # Identify the logged-in user

    conn = get_db_connection()
    cursor = conn.cursor()

    for item in order_data:
        cursor.execute('INSERT INTO orders (username, product_id, quantity) VALUES (?, ?, ?)',
                       (username, item['productId'], item['quantity']))

    conn.commit()
    conn.close()
    return jsonify({'message': 'Order placed successfully!'}), 200

# Recommendation route: Fetch product recommendations based on cart items
@app.route('/get_recommendations', methods=['POST'])
def get_recommendations():
    if 'username' not in session:
        return jsonify({'error': 'User not logged in'}), 401

    product_ids = request.json.get('productIds', [])
    if not product_ids:
        return jsonify({'error': 'No product IDs provided'}), 400

    # Generate recommendations using a ML model or predefined logic
    conn = sqlite3.connect('orders.db')  # Connect to the orders database
    cursor = conn.cursor()

    # Fetch products based on IDs and generate recommendations
    placeholder = ', '.join('?' for _ in product_ids)
    cursor.execute(f'SELECT id, name, price FROM products WHERE id IN ({placeholder})', product_ids)
    products = cursor.fetchall()
    conn.close()

    recommendations = [{'id': product['id'], 'name': product['name'], 'price': product['price']} for product in products]
    return jsonify({'recommendations': recommendations})

# Verify user route: Handle login verification
@app.route('/verify_user', methods=['POST'])
def verify_user():
    username = request.json.get('username')
    password = request.json.get('password')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        session['username'] = username  # Store the user in the session
        return jsonify({'message': 'User verified successfully!'}), 200
    else:
        return jsonify({'message': 'Invalid username or password.'}), 401

if __name__ == '__main__':
    app.run(debug=True)
