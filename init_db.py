import sqlite3

# Connect to SQLite database (it will create the database file if it doesn't exist)
conn = sqlite3.connect('users.db')
c = conn.cursor()

# Create users table if it doesn't already exist
c.execute('''CREATE TABLE IF NOT EXISTS users (
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL)''')

# Commit changes and close connection
conn.commit()
conn.close()

print("Database setup complete!")