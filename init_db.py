import sqlite3

# Connect to SQLite database (it will create the database file if it doesn't exist)
conn = sqlite3.connect('users.db')
c = conn.cursor()

# Create users table if it doesn't already exist
c.execute('''CREATE TABLE IF NOT EXISTS users (
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL)''')

# Create a userupload table
c.execute('''CREATE TABLE IF NOT EXISTS user_uploads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_path TEXT NOT NULL,
                address TEXT NOT NULL,
                owner TEXT NOT NULL,
                price REAL NOT NULL DEFAULT 0.0)''')

# Create cart table
c.execute('''CREATE TABLE IF NOT EXISTS cart (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                image_id INTEGER NOT NULL,
                FOREIGN KEY (username) REFERENCES users(username),
                FOREIGN KEY (image_id) REFERENCES images(id))''')

try:
    c.execute("ALTER TABLE cart ADD COLUMN start_date TEXT")
except sqlite3.OperationalError:
    print("start_date column already exists.")
try:
    c.execute("ALTER TABLE cart ADD COLUMN end_date TEXT")
except sqlite3.OperationalError:
    print("end_date column already exists.")

# Add this to your DB setup script
c.execute('''
    CREATE TABLE IF NOT EXISTS unavailable_dates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        upload_id INTEGER NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        FOREIGN KEY (upload_id) REFERENCES user_uploads(id)
    )
''')

# Commit changes and close connection
conn.commit()   
conn.close()

print("Database setup complete!")