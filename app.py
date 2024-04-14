# app.py
from flask import Flask, render_template, url_for, request, redirect, session
import sqlite3
from math import ceil

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Create the users table if it doesn't exist
conn = sqlite3.connect('attendance.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users
             (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, first_name TEXT, last_name TEXT, password TEXT)''')
conn.commit()
conn.close()

@app.route('/')
def index():
    if 'user_id' in session:
        conn = sqlite3.connect('attendance.db')
        c = conn.cursor()

        # Get the page number from the query string
        page = request.args.get('page', 1, type=int)

        # Set the number of items per page
        items_per_page = 10

        # Calculate the offset for the SQL query
        offset = (page - 1) * items_per_page

        # Fetch the attendance data with pagination
        c.execute("SELECT record_id, name, datetime, action FROM attendance LIMIT ? OFFSET ?", (items_per_page, offset))
        attendance_data = c.fetchall()

        # Get the total number of rows
        c.execute("SELECT COUNT(*) FROM attendance")
        total_rows = c.fetchone()[0]

        # Calculate the total number of pages
        total_pages = ceil(total_rows / items_per_page)

        conn.close()

        return render_template('index.html', attendance_data=attendance_data, page=page, total_pages=total_pages)
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Fetch the login credentials from the form
        username = request.form['username']
        password = request.form['password']

        # Check the credentials against the database
        conn = sqlite3.connect('attendance.db')
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, password))
        user = c.fetchone()
        conn.close()

        if user:
            # Store the user ID in the session
            session['user_id'] = user[0]
            return redirect(url_for('index'))
        else:
            # Display an error message
            error_message = 'Invalid username or password'
            return render_template('login.html', error_message=error_message)
    else:
        return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Fetch the registration data from the form
        username = request.form['username']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        password = request.form['password']

        # Check if the username is already taken
        conn = sqlite3.connect('attendance.db')
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username = ?", (username,))
        existing_user = c.fetchone()
        if existing_user:
            error_message = 'Username already taken'
            conn.close()
            return render_template('register.html', error_message=error_message)

        # Insert the new user into the database
        c.execute("INSERT INTO users (username, first_name, last_name, password) VALUES (?, ?, ?, ?)", (username, first_name, last_name, password))
        conn.commit()
        conn.close()

        # Store the user ID in the session
        session['user_id'] = c.lastrowid
        return redirect(url_for('index'))
    else:
        return render_template('register.html')

@app.route('/logout')
def logout():
    # Remove the user ID from the session
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/delete_record', methods=['POST'])
def delete_record():
    if 'user_id' in session:
        if request.method == 'POST':
            # Fetch the record ID from the form
            record_id = request.form['record_id']

            # Delete the record from the database
            conn = sqlite3.connect('attendance.db')
            c = conn.cursor()
            c.execute("DELETE FROM attendance WHERE record_id = ?", (record_id,))
            conn.commit()
            conn.close()

            # Redirect back to the index page
            return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
