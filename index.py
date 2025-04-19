from flask import Flask, render_template, request, redirect, url_for, flash, session, render_template, send_from_directory
import sqlite3
import os
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.secret_key = 'your_secret_key' #for flash messages
app.config['UPLOAD_FOLDER'] = 'userUploads'


#======================ROUTES/PAGES====================================================
    # Route for the Home page
@app.route('/')
def home():
    session.pop('username', None)  # Clear the session username
    return render_template('homePage.html')

# Route for the AboutUs page
@app.route('/aboutUs')
def aboutUs():
    session.pop('username', None)  # Clear the session username
    return render_template('aboutUs.html')


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
    sort_order = request.args.get('sort')

    # sorted by price View
    if sort_order == 'asc':
        listings = conn.execute('SELECT * FROM images ORDER BY CAST(price AS INTEGER) ASC').fetchall()
    elif sort_order == 'desc':
        listings = conn.execute('SELECT * FROM images ORDER BY CAST(price AS INTEGER) DESC').fetchall()
    
    # Default view
    else:
        listings = conn.execute('SELECT * FROM images').fetchall()

    conn.close()
    print(listings)  # Add this to check the data in the console
    return render_template('searchPage.html',listings = listings)


# Route for the Users page
@app.route('/user')
def user():
    username = session.get('username')
    if not username:
        return redirect(url_for('home'))

    return render_template('userPage.html', username=username)


# Route for the cart page
@app.route('/cart')
def cart():
    return render_template('cartPage.html')


# Route for the createListing page
@app.route('/createListing', methods=['GET', 'Post'])
def createListing():
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))

    if request.method == 'POST':
        #Recieves an image 
        image = request.files['image']
        address = request.form['address']
        price = request.form['price']

        #Save the file path for the image
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(filepath)

            # Save the image_path, address, owner, and price to DB (relative path)
            conn = get_db_connection()
            conn.execute("INSERT INTO images (image_path, address, owner, price) VALUES (?, ?, ?, ?)",
                        (filepath, address, username, price))
            conn.commit()
            conn.close()

            flash("Listing submitted successfully!", "success")
            return redirect(url_for('createListing', username=username))
        else:
            flash("Invalid file type", "error")

    return render_template('createListing.html', username=username)


    # Route for the editListing page
    @app.route('/editListing')
    def editListing():
        username = session.get('username')
        if not username:
            return redirect(url_for('login'))

        conn = get_db_connection()
        listings = conn.execute("SELECT * FROM images WHERE owner = ?", (username,)).fetchall()
        conn.close()

        return render_template('editListing.html', username=username, listings=listings)

@app.route('/editListing')
def editListing():
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))

    # Fetch the listings created by the logged-in user
    conn = get_db_connection()
    listings = conn.execute("SELECT * FROM images WHERE owner = ?", (username,)).fetchall()
    conn.close()

    return render_template('editListing.html', username=username, listings=listings)
#=============END OF ROUTES/PAGES=====================================================


#=============START OF FUNCTIONS================================================
#for saving images to the folder 
@app.route('/userUploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/update_listing', methods=['POST'])
def update_listing():
    listing_id = request.form['id']
    new_address = request.form['address']
    new_price = request.form['price']

    conn = get_db_connection()
    conn.execute("UPDATE images SET address = ?, price = ? WHERE id = ?", (new_address, new_price, listing_id))
    conn.commit()
    conn.close()

    flash("Listing updated successfully!", "success")
    return redirect(url_for('editListing'))

@app.route('/delete_listing', methods=['POST'])
def delete_listing():
    listing_id = request.form['id']

    conn = get_db_connection()
    conn.execute("DELETE FROM images WHERE id = ?", (listing_id,))
    conn.commit()
    conn.close()

    flash("Listing removed successfully!", "info")
    return redirect(url_for('editListing'))

    #connets to users.db

#connects to database
def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row  # Allows us to access columns by name (e.g., row['username'])
    return conn


# checks if uploaded file has allowed extension
UPLOAD_FOLDER = 'userUploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


#=============END OF FUNCTIONS================================================


if __name__ == '__main__':
    app.run(debug=True)