from flask import session, jsonify
import sqlite3

def add_to_cart(product_id, quantity=1):
    if 'cart' not in session:
        session['cart'] = {}
    cart = session['cart']

    if product_id in cart:
        cart[product_id] += quantity
    else:
        cart[product_id] = quantity

    session['cart'] = cart
    return jsonify({'message': 'Item added to cart!', 'cart': cart})

def remove_from_cart(product_id):
    cart = session.get('cart', {})
    if product_id in cart:
        del cart[product_id]
    session['cart'] = cart
    return jsonify({'message': 'Item removed from cart!', 'cart': cart})

def checkout(user_id):
    cart = session.get('cart', {})
    if not cart:
        return jsonify({'message': 'Cart is empty!'})

    connection = sqlite3.connect('orders.db')
    cursor = connection.cursor()

    for product_id, quantity in cart.items():
        cursor.execute('''
            INSERT INTO Orders (user_id, product_id, quantity)
            VALUES (?, ?, ?)
        ''', (user_id, product_id, quantity))

    connection.commit()
    connection.close()

    session.pop('cart', None)
    return jsonify({'message': 'Checkout successful!'})
