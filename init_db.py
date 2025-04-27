#   
#   File Purpose:
#       The purpose of this file is to interact with users.db
#           such as by Creating tables, adding colums, editing 
#           tables and dropping them

#   How To Use:
#   In order to adjust the table, first add your SQL command to the 
#       already existing commands. Running the File will update 
#       users.db
#   
#   How To Run:
#       users.db should be updated and good to run(4/27/2025) thus no this file DOES NOT NEED TO BE RAN
#       
#       If changes are made the File can be run by entering in a terminal:
#           python init_db.py   or    python3 init_db.py
#
#

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
try:
    c.execute("ALTER TABLE user_uploads ADD COLUMN datesBooked TEXT DEFAULT '[]'")
except sqlite3.OperationalError:
    print("datesBooked column already exists.")

# Create cart table
c.execute('''CREATE TABLE IF NOT EXISTS cart (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                image_id INTEGER NOT NULL,
                FOREIGN KEY (username) REFERENCES users(username),
                FOREIGN KEY (image_id) REFERENCES images(id))''')


# Create bookings table 
c.execute('''
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        listing_id INTEGER NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (listing_id) REFERENCES user_uploads(id)
    )
''')


# Create unavailable dates table
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