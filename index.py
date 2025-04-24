from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
import sqlite3
import os
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import json

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
        #gets username and password from FrontEnd
        username = request.form['username']
        password = request.form['password']
        print(f''' 
                User entered:
                Username: {username}
                Password: {password}''')

        #connects to a database and gets a matching username and password associated with it
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        # if there is a username matching one in the database AND
        if(user):
            print(f''' 
                Username exists
                in Database:
                Username: {user['username']}
                Password: {user['password']}
                ''')

            # its password matches the one entered it will redirect to user's page 
            if(user['password'] == password):
                print("     Passwords match, redirecting to user page")
                session['username'] = username
                return redirect(url_for('user'))

        # if not return to login
        else:
            print("         user not found, redirecting to login")
            flash("Invalid credentials. Please try again.", "error")
    return render_template('loginPage.html')


# Route for the createAccount page
@app.route('/createAccount', methods=['GET', 'POST'])
def createAccount():
    if request.method == 'POST':

        #get user inputs
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirmpassword']
        print(f''' 
                User entered:
                Username: {username}
                Password: {password}
                confirm : {confirm_password}
                ''')

        if password != confirm_password:
            flash("Passwords do not match. Please try again.", "error")
            print("password not equal to confirm_password")
            return render_template('createAccount.html')

        #if both passwords match check if username exists in database
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        #if user exists in db, prompt user to try again
        if user:
            print("user found in database")
            flash("Username already exists. Please choose a different one.", "error")
            return render_template('createAccount.html')
        
        #Add to data base
        conn = get_db_connection()
        conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()

        # Check if in database
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if user:
            print(f'''User successfully added:
        Username: {user['username']}
        Password: {user['password']}''')
        else:
            print("User not found after insertion.")
        #close connection to db and go to login
        conn.close()
        return redirect(url_for('login'))

    return render_template('createAccount.html')

# Route for the Search page
@app.route('/search')
def search():  
    conn = get_db_connection()

    #if The user wants to sort by Price
    sort_order = request.args.get('sort')
    if sort_order == 'asc':
        listings = conn.execute('SELECT * FROM user_uploads ORDER BY CAST(price AS INTEGER) ASC').fetchall()
    elif sort_order == 'desc':
        listings = conn.execute('SELECT * FROM user_uploads ORDER BY CAST(price AS INTEGER) DESC').fetchall()
    else:
        listings = conn.execute('SELECT * FROM user_uploads').fetchall()
    
    # Check if user has an item in cart, if so the page will say empty 
    cart_has_item = False
    if 'username' in session:
        cart_count = conn.execute(
            'SELECT COUNT(*) FROM cart WHERE username = ?',
            (session['username'],)
        ).fetchone()[0]
        cart_has_item = cart_count > 0
    
    conn.close()
    return render_template('searchPage.html', listings=listings, cart_has_item=cart_has_item)

    print()
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
        SELECT user_uploads.id, user_uploads.image_path, user_uploads.address, 
               user_uploads.owner, user_uploads.price, user_uploads.datesBooked
        FROM cart
        JOIN user_uploads ON cart.image_id = user_uploads.id
        WHERE cart.username = ?
    ''', (username,)).fetchall()
    conn.close()

    # Extract all the datesBooked from cart items and convert to a flat list
    disabled_dates = []
    for item in cart_items:
        if item[5]:  # If datesBooked is not None
            disabled_dates.extend(json.loads(item[5]))  # Parse JSON and add to list

    # Remove duplicates
    disabled_dates = list(set(disabled_dates))

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
                           total=total,
                           disabled_dates=disabled_dates)

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
            print(filepath)
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


@app.route('/viewBooking')
def viewBookings():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    conn = get_db_connection()
    
    # Fetch all bookings made by this user
    bookings = conn.execute('''
        SELECT bookings.id as booking_id, user_uploads.id as listing_id, 
               user_uploads.image_path, user_uploads.address, 
               user_uploads.owner, user_uploads.price, 
               bookings.start_date, bookings.end_date
        FROM bookings
        JOIN user_uploads ON bookings.listing_id = user_uploads.id
        WHERE bookings.username = ?
    ''', (username,)).fetchall()
    
    conn.close()
    
    # Process bookings (same as before)
    processed_bookings = []
    for booking in bookings:
        start = datetime.strptime(booking['start_date'], '%Y-%m-%d')
        end = datetime.strptime(booking['end_date'], '%Y-%m-%d')
        nights = 1 + (end - start).days
        total = nights * booking['price']
        fee = total * 0.01
        total = fee + nights * booking['price']
        
        processed_bookings.append({
            **dict(booking),
            'nights': nights,
            'total': total,
            'fee': fee
        })
    
    return render_template('viewBooking.html', bookings=processed_bookings)
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

    # Get the image path before deleting
    cur = conn.execute("SELECT image_path FROM user_uploads WHERE id = ?", (listing_id,))
    row = cur.fetchone()

    if row:
        image_path = row['image_path']

        # Delete the listing
        conn.execute("DELETE FROM user_uploads WHERE id = ?", (listing_id,))
        conn.commit()
        conn.close()

        print(image_path)
        # Delete the image file from disk
        if os.path.exists(image_path):
            os.remove(image_path)

        flash("Listing and image removed successfully!", "info")
    else:
        conn.close()
        flash("Listing not found.", "error")

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
        return redirect(url_for('home'))
    
    username = session['username']
    conn = get_db_connection()
    
    # Check if user already has an item in cart
    cart_count = conn.execute('SELECT COUNT(*) FROM cart WHERE username = ?', (username,)).fetchone()[0]
    
    if cart_count >= 1:
        flash('Your cart is full. You can only have one item at a time.', 'error')
        conn.close()
        return redirect(url_for('search'))
    
    # Add item to cart
    conn.execute('INSERT INTO cart (username, image_id) VALUES (?, ?)', (username, image_id))
    conn.commit()
    conn.close()
    
    flash('Item added to cart!', 'success')
    return redirect(url_for('search'))

# Route to remove item from cart
@app.route('/remove_from_cart/<int:image_id>', methods=['POST'])
def remove_from_cart(image_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    conn = get_db_connection()

    # Remove the image from the cart
    conn.execute('DELETE FROM cart WHERE username = ? AND image_id = ?', (username, image_id))
    conn.commit()
    conn.close()

    flash('Item removed from cart!', 'success')
    return redirect(url_for('cart'))

# checks if uploaded file has allowed extension
UPLOAD_FOLDER = 'userUploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/checkout', methods=['POST'])
def checkout():
    if 'username' not in session:
        return redirect(url_for('login'))  # Redirect to login if user not logged in

    start_date = request.form['start_date']
    end_date = request.form['end_date']
    image_id = request.form['image_id']  # Get the image_id from the form
    
    # Validate dates
    if not start_date or not end_date:
        flash('Please select both start and end dates', 'error')
        return redirect(url_for('cart'))
    flash('Booking confirmed for dates: {} to {}'.format(start_date, end_date), 'success')

    # Connect to the correct database
    conn = get_db_connection()

    # Insert into bookings table
    conn.execute('''
        INSERT INTO bookings (username, listing_id, start_date, end_date)
        VALUES (?, ?, ?, ?)
    ''', (session['username'], image_id, start_date, end_date))

    # Clear the entire cart for this user
    conn.execute('DELETE FROM cart WHERE username = ?', (session['username'],))
    
    conn.commit()
    flash('Booking confirmed! Your cart has been cleared.', 'success')


    # Generate a list of all dates from start_date to end_date
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        dates_booked = []
        current_date = start_date
        while current_date <= end_date:
            dates_booked.append(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)

    except ValueError:
        flash('Invalid date format', 'error')
        return redirect(url_for('cart'))
    
    try:
        # Fetch the current datesBooked for the image
        row = conn.execute('SELECT datesBooked FROM user_uploads WHERE id = ?', (image_id,)).fetchone()

        if row:
            # Parse the current datesBooked list (stored as a JSON string)
            current_dates_booked = json.loads(row[0]) if row[0] else []

            # Merge the current dates with the new dates (avoid duplicates by converting to a set)
            updated_dates = list(set(current_dates_booked + dates_booked))

            # Update the row with the new datesBooked list
            conn.execute('UPDATE user_uploads SET datesBooked = ? WHERE id = ?', 
                      (json.dumps(updated_dates), image_id))
            conn.commit()

    except Exception as e:
        conn.rollback()
        flash('Error updating booking dates', 'error')
        print(f"Error: {e}")
    finally:
        conn.close()

    return redirect(url_for('cart'))


@app.route('/cancel_booking', methods=['POST'])
def cancel_booking():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    booking_id = request.form.get('booking_id')
    listing_id = request.form.get('listing_id')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    
    conn = get_db_connection()
    try:
        # 1. Delete from bookings table
        conn.execute('DELETE FROM bookings WHERE id = ? AND username = ?', 
                   (booking_id, session['username']))
        
        # 2. Remove dates from user_uploads.datesBooked
        # Generate dates to remove
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        dates_to_remove = []
        current_date = start
        while current_date <= end:
            dates_to_remove.append(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)
        
        # Get current booked dates
        row = conn.execute('SELECT datesBooked FROM user_uploads WHERE id = ?', 
                         (listing_id,)).fetchone()
        
        if row and row['datesBooked']:
            current_dates = json.loads(row['datesBooked'])
            # Remove cancelled dates
            updated_dates = [d for d in current_dates if d not in dates_to_remove]
            # Update the database
            conn.execute('UPDATE user_uploads SET datesBooked = ? WHERE id = ?',
                       (json.dumps(updated_dates), listing_id))
        
        conn.commit()
        flash('Booking successfully cancelled', 'success')
    except Exception as e:
        conn.rollback()
        flash('Failed to cancel booking', 'error')
        print(f"Error cancelling booking: {e}")
    finally:
        conn.close()
    
    return redirect(url_for('viewBookings'))

#=============END OF FUNCTIONS================================================

if __name__ == '__main__':
    app.run(debug=True)
