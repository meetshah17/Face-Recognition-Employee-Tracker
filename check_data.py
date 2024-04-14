import sqlite3

# Connect to the database
conn = sqlite3.connect('attendance.db')
c = conn.cursor()

# Execute a SELECT query
c.execute("SELECT * FROM attendance")
print(c.fetchall())

# Close the connection
conn.close()
