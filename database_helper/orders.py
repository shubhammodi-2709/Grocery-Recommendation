from flask import jsonify
import sqlite3
import json

# Helper function to get database connection
def get_db_connection():
    connection = sqlite3.connect('data.db')  # Adjust path as needed
    connection.row_factory = sqlite3.Row
    return connection

def add_to_cart(user_id, product_id, quantity=1):
    """Add an item to the user's cart in the database."""
    connection = get_db_connection()
    cursor = connection.cursor()
    
    # Check if the cart exists for the user
    cursor.execute('SELECT cart FROM Users WHERE id = ?', (user_id,))
    user_cart_row = cursor.fetchone()

    cart = json.loads(user_cart_row['cart']) if user_cart_row and user_cart_row['cart'] else {}
    
    # Update the cart
    if product_id in cart:
        cart[product_id] += quantity
    else:
        cart[product_id] = quantity

    # Save the updated cart back to the database
    cursor.execute('UPDATE Users SET cart = ? WHERE id = ?', (json.dumps(cart), user_id))
    connection.commit()
    connection.close()

    return jsonify({'message': 'Item added to cart!', 'cart': cart})

def remove_from_cart(user_id, product_id):
    """Remove an item from the user's cart in the database."""
    connection = get_db_connection()
    cursor = connection.cursor()
    
    # Retrieve the current cart
    cursor.execute('SELECT cart FROM Users WHERE id = ?', (user_id,))
    user_cart_row = cursor.fetchone()
    cart = json.loads(user_cart_row['cart']) if user_cart_row and user_cart_row['cart'] else {}
    
    # Remove the product from the cart
    if product_id in cart:
        del cart[product_id]

    # Save the updated cart back to the database
    cursor.execute('UPDATE Users SET cart = ? WHERE id = ?', (json.dumps(cart), user_id))
    connection.commit()
    connection.close()

    return jsonify({'message': 'Item removed from cart!', 'cart': cart})

def checkout(user_id):
    """Finalize the order and clear the user's cart."""
    connection = get_db_connection()
    cursor = connection.cursor()

    # Retrieve the current cart
    cursor.execute('SELECT cart FROM Users WHERE id = ?', (user_id,))
    user_cart_row = cursor.fetchone()
    cart = json.loads(user_cart_row['cart']) if user_cart_row and user_cart_row['cart'] else {}

    if not cart:
        connection.close()
        return jsonify({'message': 'Cart is empty!'})

    # Insert cart items into the Orders table
    for product_id, quantity in cart.items():
        cursor.execute('''
            INSERT INTO Orders (user_id, product_id, quantity)
            VALUES (?, ?, ?)
        ''', (user_id, product_id, quantity))
    
    # Clear the cart
    cursor.execute('UPDATE Users SET cart = ? WHERE id = ?', (None, user_id))
    connection.commit()
    connection.close()

    return jsonify({'message': 'Checkout successful!'})
