from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key for session management

# Function to establish a database connection
def get_db_connection():
    conn = sqlite3.connect('users.db')  # Connect to the users database
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries for easier access
    return conn

# Signup route: Handles user registration
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username'].strip()  # Get and sanitize username
        password = request.form['password'].strip()  # Get and sanitize password

        if not username or not password:
            flash('Username and password cannot be empty.', 'error')
            return render_template('signup.html')

        conn = get_db_connection()
        # Check if the username already exists
        existing_user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

        if existing_user:
            flash('Username already exists. Please choose a different one.', 'error')
            conn.close()
            return render_template('signup.html')

        # Insert the new user into the database
        conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
        conn.close()
        flash('Signup successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')  # Render the signup page for GET requests

# Login route: Handles user authentication
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()  # Get and sanitize username
        password = request.form['password'].strip()  # Get and sanitize password

        if not username or not password:
            flash('Username and password cannot be empty.', 'error')
            return render_template('login.html')

        conn = get_db_connection()
        # Fetch the user from the database
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user is None:
            flash('Username does not exist. Please sign up.', 'error')
            return redirect(url_for('signup'))
        elif user['password'] != password:
            flash('Incorrect password. Please try again.', 'error')
            return render_template('login.html')
        else:
            session['username'] = username  # Store username in session
            flash(f'Welcome back, {username}!', 'success')
            return redirect(url_for('main'))

    return render_template('login.html')  # Render the login page for GET requests

# Logout route: Ends the user session
@app.route('/logout')
def logout():
    if 'username' in session:
        session.pop('username', None)  # Remove the username from the session
        flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

# Main route: Displays the main page if the user is logged in
@app.route('/main')
def main():
    if 'username' in session:  # Check if the user is logged in
        return render_template('main.html', username=session['username'])  # Pass the username to the template
    flash('Please log in to access the main page.', 'error')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
