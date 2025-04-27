import unittest
import os
from index import app, get_db_connection    # Assuming your Flask app is in a file called app.py
from flask import jsonify, current_app
import sqlite3
from datetime import datetime
from werkzeug.utils import secure_filename
import json


#===================How to run test_app.py==================================
#       need to install coverage with pip install
#       need to install pytest with pip install
#       
#       in terminal enter 
#           coverage run --omit='/usr/lib/python3/*' -m unittest discover
#       
#       to view report type
#           coverage report
#       
#       to see in html type 
#           coverage html

#       This produces an html called index.html. 
#           it can be ran in any browser



class FlaskTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Set up the test database and insert a test user
        cls.db = get_db_connection(database='users.db')
        cls.cursor = cls.db.cursor()
        
        # Create table if it doesn't exist (or use a mock DB schema)
        cls.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                password TEXT NOT NULL
            )
        """)

        cls.cursor.execute('''CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY, 
        username TEXT, 
        listing_id INTEGER, 
        start_date TEXT, 
        end_date TEXT
        )''')
    
        cls.cursor.execute('''CREATE TABLE IF NOT EXISTS cart (
            username TEXT, 
            image_id INTEGER
        )''')
    
        cls.cursor.execute('''CREATE TABLE IF NOT EXISTS user_uploads (
            id INTEGER PRIMARY KEY, 
            image_path TEXT, 
            address TEXT, 
            owner TEXT, 
            price TEXT, 
            datesBooked TEXT
        )''')
        
        cls.db.commit()

    @classmethod
    def tearDownClass(cls):
        # Clean up the database after all tests are done
        pass

    def setUp(self):
        # Set up the testing client
        self.client = app.test_client()

    def tearDown(self):
        # Clean up after each test
        pass



#===================================TEST Display Pages=================================================================

    def test_home(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_about_us(self):
        response = self.client.get('/aboutUs')
        self.assertEqual(response.status_code, 200)


#=============================TEST LOGIN=====================================
    def test_login_page(self):
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)

    def test_login_successful(self):
        # Ensure 'testuser' is created in the database before the test
        conn = get_db_connection()
        conn.execute('DELETE FROM users WHERE username = ?', ('testuser',))  # Remove any existing user
        conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', ('testuser', 'password123'))
        conn.commit()
        conn.close()

        # Simulate login with valid credentials
        response = self.client.post('/login', data=dict(
            username='testuser',
            password='password123'
        ), follow_redirects=True)
        
        # Check if the response status code is 200 (meaning successful login)
        self.assertEqual(response.status_code, 200)  # Check for a successful login (home or dashboard page)

        # Check if the session variable 'username' is set, which indicates a successful login
        with self.client.session_transaction() as session:
            self.assertEqual(session.get('username'), 'testuser')

        # Optionally, check if certain content is present on the page (e.g., a welcome message)
        self.assertIn(b"Hello, testuser!", response.data)  # Modify based on your actual content

        # Clean up: Remove 'testuser' after the test
        conn = get_db_connection()
        conn.execute('DELETE FROM users WHERE username = ?', ('testuser',))
        conn.commit()
        conn.close()

    def test_login_unsuccessful(self):
        # Simulate login with invalid credentials
        response = self.client.post('/login', data=dict(
            username='wronguser',
            password='wrongpassword'
        ), follow_redirects=True)
        
        # Check if the response status code is 200, which means the page was loaded
        # after the login failure (you might want to redirect or show an error message)
        self.assertEqual(response.status_code, 200)

        # Optionally, check for a specific error message indicating login failure
        # Adjust the message based on what your app shows for a failed login
        self.assertIn(b"Invalid credentials. Please try again.", response.data)

        # Check if the session variable 'username' is not set, which indicates a failed login
        with self.client.session_transaction() as session:
            self.assertIsNone(session.get('username'))


#=============================TEST Create Account=====================================
    def test_create_account(self):
        response = self.client.get('/createAccount')
        self.assertEqual(response.status_code, 200)

    def test_create_account_successful(self):
        # Ensure 'testuser' is removed from the database before the test
        conn = get_db_connection()
        conn.execute('DELETE FROM users WHERE username = ?', ('testuser',))  # Remove any existing testuser
        conn.commit()
        conn.close()

        # Simulate a POST request to the /createAccount route with valid credentials
        response = self.client.post('/createAccount', data=dict(
            username='testuser',
            password='password123',
            confirmpassword='password123'
        ), follow_redirects=True)
        
        # Check if the response status code is 200 (meaning the page was loaded after redirect)
        self.assertEqual(response.status_code, 200)
        
        # Manually check for redirection to the login page by checking the Location header
        self.assertIn(b'/login', response.data)

        # Check if the new user exists in the database
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', ('testuser',)).fetchone()
        conn.close()

        # Assert that the user is found in the database
        self.assertIsNotNone(user)
        self.assertEqual(user['username'], 'testuser')

        # Clean up: Remove the user from the database after the test
        conn = get_db_connection()
        conn.execute('DELETE FROM users WHERE username = ?', ('testuser',))
        conn.commit()
        conn.close()

    def test_create_account_password_mismatch(self):
        # Clean up any existing 'testuser' before running the test
        conn = get_db_connection()
        conn.execute('DELETE FROM users WHERE username = ?', ('testuser',))
        conn.commit()
        conn.close()

        # Simulate a POST request to the /createAccount route with mismatched passwords
        response = self.client.post('/createAccount', data=dict(
            username='testuser',
            password='password123',
            confirmpassword='differentpassword'
        ), follow_redirects=True)
        
        # Check if the response status code is 200 (meaning the page was loaded after error)
        self.assertEqual(response.status_code, 200)

        # Verify that the error message "Passwords do not match" is displayed
        self.assertIn(b"Passwords do not match. Please try again.", response.data)

        # Ensure the user is not added to the database
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', ('testuser',)).fetchone()
        conn.close()

        # Assert that the user does not exist in the database
        self.assertIsNone(user)

    def test_create_account_user_already_exists(self):
        # Clean up any existing 'testuser' before running the test
        conn = get_db_connection()
        conn.execute('DELETE FROM users WHERE username = ?', ('testuser',))
        conn.commit()
        conn.close()

        # Add a user manually to simulate the existing user scenario
        conn = get_db_connection()
        conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("testuser", "password123"))
        conn.commit()
        conn.close()

        # Simulate a POST request to the /createAccount route with an already existing username
        response = self.client.post('/createAccount', data=dict(
            username='testuser',
            password='password123',
            confirmpassword='password123'
        ), follow_redirects=True)
        
        # Check if the response status code is 200 (meaning the page was loaded after error)
        self.assertEqual(response.status_code, 200)

        # Verify that the error message "Username already exists" is displayed
        self.assertIn(b"Username already exists. Please choose a different one.", response.data)

        # Ensure the user is still in the database (should not be deleted after failed account creation)
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', ('testuser',)).fetchone()
        conn.close()

        # Assert that the user exists in the database
        self.assertIsNotNone(user)

        # Clean up by deleting the user after the test
        conn = get_db_connection()
        conn.execute("DELETE FROM users WHERE username = ?", ("testuser",))
        conn.commit()
        conn.close()


#============================Test Search========================================
    def test_search(self):
        response = self.client.get('/search')
        self.assertEqual(response.status_code, 200)

    def test_search_default(self):
        # Simulate a GET request to /search without any sorting
        response = self.client.get('/search')
        
        # Ensure the response status code is 200 (OK)
        self.assertEqual(response.status_code, 200)
        
        # Check that the listings are being returned (you can check that something in the listings is present)
        self.assertIn(b"Address", response.data)  # Modify based on actual content
        self.assertIn(b"Owner", response.data)
        self.assertIn(b"Price Per Day", response.data)
    
    def test_search_sort_ascending(self):
        response = self.client.get('/search?sort=asc')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Price Per Day", response.data)

    def test_search_sort_descending(self):
        response = self.client.get('/search?sort=desc')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Price Per Day", response.data)

    def test_add_to_cart(self):
        # Clean up existing cart entry for test user
        conn = get_db_connection()
        conn.execute("DELETE FROM cart WHERE username = ?", ('test_user',))
        conn.execute("DELETE FROM user_uploads WHERE id = ?", (1,))

        # Insert a test listing to be added to cart
        conn.execute('''
            INSERT INTO user_uploads (id, image_path, address, owner, price, datesBooked)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (1, 'image.jpg', '123 Test St', 'owner_user', 99.99, '[]'))
        conn.commit()
        conn.close()

        # Simulate logged-in user
        with self.client.session_transaction() as sess:
            sess['username'] = 'test_user'

        # Send POST request to add listing to cart
        response = self.client.post('/add_to_cart/1', follow_redirects=True)

        # Check that response is OK and success message is shown
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Item added to cart!', response.data)

        # Verify that item was added to cart
        conn = get_db_connection()
        result = conn.execute("SELECT * FROM cart WHERE username = ?", ('test_user',)).fetchone()
        conn.close()
        self.assertIsNotNone(result)
        self.assertEqual(result['image_id'], 1)

#============================Test USER========================================

    def test_user(self):
        # Simulate a logged-in user by setting a session variable
        with self.client.session_transaction() as session:
            session['username'] = 'testuser'
        # Make a GET request to the /user route
        response = self.client.get('/user')
        # Check if the status code is 200, meaning the page loads successfully
        self.assertEqual(response.status_code, 200)
        
    def test_user_route_redirects_without_session(self):
        # Make a request to /user with no session set
        response = self.client.get('/user', follow_redirects=False)

        # Expect a redirect (302) to the home page
        self.assertEqual(response.status_code, 302)
        self.assertIn('/', response.headers['Location'])



#============================Test CART========================================

    def test_cart(self):
        # Simulate a logged-in user by setting a session variable
        with self.client.session_transaction() as session:
            session['username'] = 'testuser'
        response = self.client.get('/cart')
        self.assertEqual(response.status_code, 200)

    def test_cart_redirects_if_user_not_logged_in(self):
        # Simulate request to /cart with no session
        response = self.client.get('/cart', follow_redirects=False)

        # It should redirect to the login page
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.headers['Location'])

    def test_remove_from_cart(self):
        # Clean up any existing data
        conn = get_db_connection()
        conn.execute("DELETE FROM cart WHERE username = ?", ('test_user',))
        conn.execute("DELETE FROM user_uploads WHERE id = ?", (1,))

        # Add a test listing to user_uploads
        conn.execute('''
            INSERT INTO user_uploads (id, image_path, address, owner, price, datesBooked)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (1, 'image.jpg', '123 Test St', 'owner_user', 50.00, '[]'))

        # Add the listing to the cart
        conn.execute('''
            INSERT INTO cart (username, image_id)
            VALUES (?, ?)
        ''', ('test_user', 1))
        conn.commit()
        conn.close()

        # Simulate logged-in user
        with self.client.session_transaction() as sess:
            sess['username'] = 'test_user'

        # Send POST request to remove the item
        response = self.client.post('/remove_from_cart/1', follow_redirects=True)

        # Check that response is OK and success message is shown
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Item removed from cart!', response.data)

        # Verify item is no longer in cart
        conn = get_db_connection()
        result = conn.execute("SELECT * FROM cart WHERE username = ?", ('test_user',)).fetchone()
        conn.close()
        self.assertIsNone(result)
#============================Test Create Listing========================================

    def test_create_listing(self):
        # Simulate a logged-in user by setting a session variable
        with self.client.session_transaction() as session:
            session['username'] = 'testuser'

        response = self.client.get('/createListing')
        self.assertEqual(response.status_code, 200)

    def test_create_listing_success(self):
        # Set up the user and simulate login session
        with self.client:
            # Add a user to the database
            username = 'testuser'
            password = 'password123'
            conn = get_db_connection()
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
            conn.close()

            # Simulate a login for the test user
            self.client.post('/login', data=dict(username=username, password=password), follow_redirects=True)

            # Create a temporary image file for the listing
            image_filename = 'test_image.jpg'
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)

            with open(image_path, 'wb') as f:
                f.write(b'Test image content')

            # Simulate a POST request to create a listing with valid inputs
            response = self.client.post('/createListing', data=dict(
                image=(open(image_path, 'rb'), image_filename),
                address='123 Test Address',
                price='100.0'
            ), follow_redirects=True)

            # Check if the response status code is 200 (page reloaded after success)
            self.assertEqual(response.status_code, 200)

            # Verify that the listing creation success message is in the response
            self.assertIn(b"Listing submitted successfully!", response.data)

            # Check if the listing is saved in the database
            conn = get_db_connection()
            listing = conn.execute('SELECT * FROM user_uploads WHERE address = ?', ('123 Test Address',)).fetchone()
            conn.close()
            
            # Ensure the listing exists in the database
            self.assertIsNotNone(listing)

            # Clean up by deleting the listing and user
            conn = get_db_connection()
            conn.execute('DELETE FROM user_uploads WHERE address = ?', ('123 Test Address',))
            conn.execute('DELETE FROM users WHERE username = ?', (username,))
            conn.commit()
            conn.close()

            # Delete the image file from the upload folder
            if os.path.exists(image_path):
                os.remove(image_path)


#============================Test Edit Listing========================================
    def test_edit_listing(self):
        # Simulate a logged-in user by setting a session variable
        with self.client.session_transaction() as session:
            session['username'] = 'testuser'
        response = self.client.get('/editListing')
        self.assertEqual(response.status_code, 200)

    def test_update_listing(self):
        # Clear any existing listing with the same ID
        conn = get_db_connection()
        conn.execute("DELETE FROM user_uploads WHERE id = ?", (1,))

        # Insert a test listing
        conn.execute('''
            INSERT INTO user_uploads (id, image_path, address, owner, price, datesBooked)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (1, 'test_image.jpg', 'Old Address', 'test_user', 100.0, '[]'))
        conn.commit()
        conn.close()

        # Simulate logged-in user
        with self.client.session_transaction() as sess:
            sess['username'] = 'test_user'

        # Send POST request to update the listing
        response = self.client.post('/update_listing', data={
            'id': 1,
            'address': 'New Address',
            'price': '150.00'
        }, follow_redirects=True)

        # Check that response is OK
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Listing updated successfully!', response.data)

        # Verify database was updated
        conn = get_db_connection()
        updated = conn.execute("SELECT address, price FROM user_uploads WHERE id = ?", (1,)).fetchone()
        conn.close()
        self.assertEqual(updated['address'], 'New Address')
        self.assertEqual(float(updated['price']), 150.00)
        
    def test_delete_listing(self):
        # Set up test image path
        test_image_path = 'test_image_to_delete.jpg'
        with open(test_image_path, 'w') as f:
            f.write('fake image content')

        # Connect to database
        conn = get_db_connection()

        # First delete any existing listing with id = 1
        conn.execute("DELETE FROM user_uploads WHERE id = ?", (1,))

        # Insert the test listing
        conn.execute('''
            INSERT INTO user_uploads (id, image_path, address, owner, price, datesBooked)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (1, test_image_path, '123 Test St', 'test_user', 100.0, '[]'))
        conn.commit()
        conn.close()

        # Simulate logged-in user
        with self.client.session_transaction() as sess:
            sess['username'] = 'test_user'

        # Send POST request to delete the listing
        response = self.client.post('/delete_listing', data={'id': 1}, follow_redirects=True)

        # Check that response is OK and includes success message
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Listing and image removed successfully!', response.data)

        # Verify the listing is removed from the database
        conn = get_db_connection()
        deleted = conn.execute("SELECT * FROM user_uploads WHERE id = ?", (1,)).fetchone()
        conn.close()
        self.assertIsNone(deleted)

        # Verify the image file was deleted
        self.assertFalse(os.path.exists(test_image_path))



#=====================CHECKOUT=====================================
    def test_checkout_user_not_logged_in(self):
        response = self.client.post('/checkout', data={
            'start_date': '2025-05-01',
            'end_date': '2025-05-05',
            'image_id': 1
        })
        self.assertEqual(response.status_code, 302)  # Expecting redirect (login page)
        self.assertEqual(response.headers['Location'], '/login')
    


#=====================Bookings=====================================
    def test_cancel_booking(self):
        # Set up: insert a user, a booking, and an image with datesBooked
        username = 'testuser'
        booking_id = 1  # Arbitrary booking ID for test
        image_id = 999  # Arbitrary image ID
        start_date = '2025-05-01'
        end_date = '2025-05-05'
       
        # Existing dates booked for the image
        initial_dates = json.dumps(['2025-04-28', '2025-04-29', '2025-04-30'])
       
        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor()


        # Cleanup any existing data for this image_id and booking_id
        cursor.execute('DELETE FROM bookings WHERE id = ? AND username = ?', (booking_id, username))
        cursor.execute('DELETE FROM user_uploads WHERE id = ?', (image_id,))
        cursor.execute('DELETE FROM users WHERE username = ?', (username,))


        # Insert the user into the users table (if not already exists)
        cursor.execute('INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)', (username, 'password123'))
       
        # Insert an image with existing datesBooked, a placeholder for image_path, address, and owner
        image_path = 'path/to/image.jpg'  # Placeholder path for image
        address = '123 Test Street, Test City, Test Country'  # Placeholder address for the image
        owner = username  # Owner of the image (test user)
        cursor.execute('INSERT INTO user_uploads (id, datesBooked, image_path, address, owner) VALUES (?, ?, ?, ?, ?)',
                    (image_id, initial_dates, image_path, address, owner))


        # Insert a booking into the bookings table for the test user
        conn.execute('''INSERT INTO bookings (username, listing_id, start_date, end_date)
                        VALUES (?, ?, ?, ?)''', (username, image_id, start_date, end_date))


        # Commit changes to the database
        conn.commit()
        conn.close()


        # Simulate login
        with self.client.session_transaction() as session:
            session['username'] = username


        # Prepare form data for cancel booking
        cancel_data = {
            'booking_id': booking_id,
            'listing_id': image_id,
            'start_date': start_date,
            'end_date': end_date
        }


        # Send POST request to cancel booking
        response = self.client.post('/cancel_booking', data=cancel_data, follow_redirects=True)


        # Confirm successful response
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Booking successfully cancelled', response.data)


        # Check that the booking was deleted from the bookings table
        conn = get_db_connection()
        booking = conn.execute('SELECT * FROM bookings WHERE id = ? AND username = ?',
                            (booking_id, username)).fetchone()
        conn.close()
        self.assertIsNone(booking)


        # Check that the datesBooked were updated in the user_uploads table
        conn = get_db_connection()
        row = conn.execute('SELECT datesBooked FROM user_uploads WHERE id = ?', (image_id,)).fetchone()
        conn.close()


        # The cancelled dates (2025-05-01, 2025-05-05) should be removed
        expected_dates = ['2025-04-28', '2025-04-29', '2025-04-30']
        updated_dates = json.loads(row['datesBooked'])
        self.assertEqual(sorted(updated_dates), sorted(expected_dates))

    def test_view_bookings(self):
            # Simulate a logged-in user by setting a session variable
            with self.client.session_transaction() as session:
                session['username'] = 'testuser'
            response = self.client.get('/viewBooking')
            self.assertEqual(response.status_code, 200)


    def test_uploaded_file(self):
        # Simulate a logged-in user by setting a session variable
        with self.client.session_transaction() as session:
            session['username'] = 'testuser'

        # Ensure the file exists in the userUploads directory
        test_filename = 'someimage.jpg'
        upload_folder = os.path.join(os.getcwd(), 'userUploads')  # Assuming relative path from cwd
        file_path = os.path.join(upload_folder, test_filename)

        # Create a mock file if it doesn't exist (optional)
        if not os.path.exists(file_path):
            os.makedirs(upload_folder, exist_ok=True)  # Ensure the folder exists
            # Create a mock file (can be an image or text file for the test)
            with open(file_path, 'w') as f:
                f.write("This is a mock image file.")  # This can be a real image file for actual tests

        # Make a GET request to the /userUploads/<filename> route
        response = self.client.get(f'/userUploads/{test_filename}')

        # Check if the status code is 200, meaning the file was found and served
        self.assertEqual(response.status_code, 200)


    

if __name__ == "__main__":
    unittest.main()
