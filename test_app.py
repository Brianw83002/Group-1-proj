import unittest
import os
from index import app  # Assuming your Flask app is in a file called app.py
from flask import jsonify, current_app
import sqlite3

class FlaskTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Set up the test database here or mock the database
        pass

    @classmethod
    def tearDownClass(cls):
        # Clean up the database here
        pass

    def setUp(self):
        # Set up the testing client
        self.client = app.test_client()

    def tearDown(self):
        # Clean up after each test
        pass



#====================================================================================================


    def test_home(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_about_us(self):
        response = self.client.get('/aboutUs')
        self.assertEqual(response.status_code, 200)

    def test_login_page(self):
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)

    def test_create_account(self):
        response = self.client.get('/createAccount')
        self.assertEqual(response.status_code, 200)

    def test_search(self):
        response = self.client.get('/search')
        self.assertEqual(response.status_code, 200)

    def test_user(self):
        # Simulate a logged-in user by setting a session variable
        with self.client.session_transaction() as session:
            session['username'] = 'testuser'
        # Make a GET request to the /user route
        response = self.client.get('/user')
        # Check if the status code is 200, meaning the page loads successfully
        self.assertEqual(response.status_code, 200)
        
    def test_cart(self):
        # Simulate a logged-in user by setting a session variable
        with self.client.session_transaction() as session:
            session['username'] = 'testuser'
        response = self.client.get('/cart')
        self.assertEqual(response.status_code, 200)

    def test_create_listing(self):
        # Simulate a logged-in user by setting a session variable
        with self.client.session_transaction() as session:
            session['username'] = 'testuser'

        response = self.client.get('/createListing')
        self.assertEqual(response.status_code, 200)

    def test_edit_listing(self):
        # Simulate a logged-in user by setting a session variable
        with self.client.session_transaction() as session:
            session['username'] = 'testuser'
        response = self.client.get('/editListing')
        self.assertEqual(response.status_code, 200)

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

    # Additional tests can be added for POST requests, form handling, etc.

if __name__ == "__main__":
    unittest.main()
