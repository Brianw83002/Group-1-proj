import sqlite3

# Connect to SQLite database (it will create the database file if it doesn't exist)
conn = sqlite3.connect('users.db')
c = conn.cursor()

# Create users table if it doesn't already exist
c.execute('''CREATE TABLE IF NOT EXISTS users (
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL)''')

# Create table for listings with file path
c.execute('''CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_path TEXT NOT NULL,
                address TEXT NOT NULL,
                owner TEXT NOT NULL)''')

# Add the new price column if it doesn't already exist
try:
    c.execute('ALTER TABLE images ADD COLUMN price TEXT NOT NULL DEFAULT "0"')
except sqlite3.OperationalError:
    print("Column 'price' already exists or there was an error.")

# Commit changes and close connection
conn.commit()
conn.close()

print("Database setup complete!")