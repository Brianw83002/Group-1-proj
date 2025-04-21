from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # for flash messages
app.config['UPLOAD_FOLDER'] = 'userUploads'

#======================ROUTES/PAGES====================================================
@app.route('/')
def home():
    session.pop('username', None)  # Clear the session username
    return render_template('homePage.html')

@app.route('/aboutUs')
def aboutUs():
    session.pop('username', None)  # Clear the session username
    return render_template('aboutUs.html')

# Route for the Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        if user and user['password'] == password:
            session['username'] = username
            return redirect(url_for('user'))
        else:
            flash("Invalid credentials. Please try again.", "error")
        return render_template('loginPage.html')
    return render_template('loginPage.html')

# Route for the createAccount page
@app.route('/createAccount', methods=['GET', 'POST'])
def createAccount():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirmpassword']
        if password != confirm_password:
            flash("Passwords do not match. Please try again.", "error")
            return render_template('createAccount.html')
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        if user:
            flash("Username already exists. Please choose a different one.", "error")
            return render_template('createAccount.html')
        conn = get_db_connection()
        conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
        conn.close()
        return redirect(url_for('login'))
    return render_template('createAccount.html')

# Route for the Search page
@app.route('/search')
def search():
    conn = get_db_connection()
    sort_order = request.args.get('sort')
    if sort_order == 'asc':
        listings = conn.execute('SELECT * FROM user_uploads ORDER BY CAST(price AS INTEGER) ASC').fetchall()
    elif sort_order == 'desc':
        listings = conn.execute('SELECT * FROM user_uploads ORDER BY CAST(price AS INTEGER) DESC').fetchall()
    else:
        listings = conn.execute('SELECT * FROM user_uploads').fetchall()
    conn.close()
    return render_template('searchPage.html', listings=listings)

# Route for the Users page
@app.route('/user')
def user():
    username = session.get('username')
    if not username:
        return redirect(url_for('home'))
    return render_template('userPage.html', username=username)

@app.route('/cart')
def cart():
    if 'username' not in session:
        return redirect(url_for('login'))  # Redirect to login if user not logged in
    
    username = session['username']
    conn = get_db_connection()

    # Fetch cart items from the database
    cart_items = conn.execute('''
        SELECT user_uploads.id, user_uploads.image_path, user_uploads.address, user_uploads.owner, user_uploads.price
        FROM cart
        JOIN user_uploads ON cart.image_id = user_uploads.id
        WHERE cart.username = ?
    ''', (username,)).fetchall()
    conn.close()

    # Calculate subtotal (make sure price is treated as float)
    subtotal = sum(float(item[4]) for item in cart_items)
    fee = subtotal * 0.01  # 1% AirHome fee
    total = subtotal + fee

    # Round to 2 decimal places (optional but nice)
    subtotal = round(subtotal, 2)
    fee = round(fee, 2)
    total = round(total, 2)

    return render_template('cartPage.html', 
                           username=username, 
                           cart_items=cart_items, 
                           subtotal=subtotal, 
                           fee=fee, 
                           total=total)



# Route for the createListing page
@app.route('/createListing', methods=['GET', 'POST'])
def createListing():
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))
    if request.method == 'POST':
        # Recieves an image
        image = request.files['image']
        address = request.form['address']
        price = request.form['price']
        # Save the file path for the image
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(filepath)
            conn = get_db_connection()
            conn.execute("INSERT INTO user_uploads (image_path, address, owner, price) VALUES (?, ?, ?, ?)",
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
    listings = conn.execute("SELECT * FROM user_uploads WHERE owner = ?", (username,)).fetchall()
    conn.close()
    return render_template('editListing.html', username=username, listings=listings)


#======================END OF ROUTES/PAGES====================================================


#======================FUNCTIONS====================================================
# For serving uploaded files
@app.route('/userUploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/update_listing', methods=['POST'])
def update_listing():
    listing_id = request.form['id']
    new_address = request.form['address']
    new_price = request.form['price']
    conn = get_db_connection()
    conn.execute("UPDATE user_uploads SET address = ?, price = ? WHERE id = ?", (new_address, new_price, listing_id))
    conn.commit()
    conn.close()
    flash("Listing updated successfully!", "success")
    return redirect(url_for('editListing'))

@app.route('/delete_listing', methods=['POST'])
def delete_listing():
    listing_id = request.form['id']
    conn = get_db_connection()
    conn.execute("DELETE FROM user_uploads WHERE id = ?", (listing_id,))
    conn.commit()
    conn.close()
    flash("Listing removed successfully!", "info")
    return redirect(url_for('editListing'))

# Connects to the users.db database
def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row  # Allows us to access columns by name (e.g., row['username'])
    return conn

# Route to add item to cart
@app.route('/add_to_cart/<int:image_id>', methods=['POST'])
def add_to_cart(image_id):
    if 'username' not in session:
        return redirect(url_for('home'))  # redirect if not logged in
    username = session['username']
    conn = get_db_connection()
    existing = conn.execute('SELECT * FROM cart WHERE username = ? AND image_id = ?', (username, image_id)).fetchone()
    if not existing:
        conn.execute('INSERT INTO cart (username, image_id) VALUES (?, ?)', (username, image_id))
        conn.commit()
        flash('Added to cart!')
    else:
        flash('Item already in cart.')
    conn.close()
    return redirect(url_for('search'))

# Route to remove item from cart
@app.route('/remove_from_cart/<int:image_id>', methods=['POST'])
def remove_from_cart(image_id):
    if 'username' not in session:
        return redirect(url_for('home'))
    username = session['username']
    conn = get_db_connection()
    conn.execute('DELETE FROM cart WHERE username = ? AND image_id = ?', (username, image_id))
    conn.commit()
    conn.close()
    flash('Removed from cart.')
    return redirect(url_for('cart'))

# checks if uploaded file has allowed extension
UPLOAD_FOLDER = 'userUploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#=============END OF FUNCTIONS================================================

if __name__ == '__main__':
    app.run(debug=True)
