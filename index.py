from flask import Flask, render_template, request, redirect, url_for, flash, session, render_template, send_from_directory
import sqlite3
import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'userUploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


app = Flask(__name__)
app.secret_key = 'your_secret_key' #for flash messages
app.config['UPLOAD_FOLDER'] = 'userUploads'

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#connets to users.db
def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row  # Allows us to access columns by name (e.g., row['username'])
    return conn


#======================ROUTES====================================================
# Route for the Home page
@app.route('/')
def home():
    return render_template('homePage.html')

# Route for the Login page (currently '/about')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get the submitted username and password
        username = request.form['username']
        password = request.form['password']
        
        # Check if username exists and the password matches
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        #checkes if the entered password is correct password
        if user and user['password'] == password:
            session['username'] = username
            return redirect(url_for('user'))
        else:
            flash("Invalid credentials. Please try again.", "error")

        # Render the login page again with the flash message
        return render_template('loginPage.html')

    return render_template('loginPage.html')

# Route for the createAccount page
@app.route('/createAccount', methods=['GET', 'POST'])
def createAccount():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirmpassword']
        
        # Check if the passwords match
        if password != confirm_password:
            flash("Passwords do not match. Please try again.", "error")
            return render_template('createAccount.html')
        
        # Check if username already exists
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user:
            flash("Username already exists. Please choose a different one.", "error")
            return render_template('createAccount.html')
        
        # If no match, insert new user into the database
        conn = get_db_connection()
        conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
        conn.close()


        return redirect(url_for('login'))
    
    return render_template('createAccount.html')


    username = request.args.get('username')
    return render_template('createAccount.html')

# Route for the Search page
@app.route('/search')
def search():
    conn = get_db_connection()
    listings = conn.execute('SELECT * FROM images').fetchall()
    conn.close()
    print(listings)  # Add this to check the data in the console
    return render_template('searchPage.html',listings = listings)

# Route for the Users page
@app.route('/user')
def user():
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))

    return render_template('userPage.html', username=username)
    

# Route for the Home page
@app.route('/cart')
def cart():
    return render_template('cartPage.html')

@app.route('/createListing', methods=['GET', 'Post'])
def createListing():
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))

    if request.method == 'POST':
        image = request.files['image']
        address = request.form['address']

        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(filepath)

            # Save to DB (relative path)
            conn = get_db_connection()
            conn.execute("INSERT INTO images (image_path, address, owner) VALUES (?, ?, ?)",
                        (filepath, address, username))
            conn.commit()
            conn.close()

            flash("Listing submitted successfully!", "success")
            return redirect(url_for('user', username=username))
        else:
            flash("Invalid file type", "error")

    return render_template('createListing.html', username=username)


@app.route('/userUploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


#=============END OF ROUTES=====================================================

if __name__ == '__main__':
    app.run(debug=True)