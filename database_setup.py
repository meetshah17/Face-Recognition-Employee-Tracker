import sqlite3

# Connect to SQLite database
conn = sqlite3.connect('attendance.db')
c = conn.cursor()

# Create table to store attendance data
# c.execute(''' DROP TABLE users''')

# Create the users table
c.execute('''CREATE TABLE IF NOT EXISTS users
             (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, first_name TEXT, last_name TEXT, password TEXT)''')

# Commit changes and close connection
conn.commit()
conn.close()


