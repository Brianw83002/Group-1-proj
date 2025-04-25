
import pytest
import json
from index import app, get_db_connection

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test'
    with app.test_client() as client:
        yield client

def setup_test_user_and_cart():
    """Insert a test user and add items to their cart."""
    # Set up test user
    conn = get_db_connection()
    conn.execute("DELETE FROM users WHERE username = 'testuser'")
    conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('testuser', 'testpass'))

    # Set up a test image in user_uploads and add it to cart
    conn.execute('''INSERT INTO user_uploads (image_path, address, owner, price, datesBooked) 
                    VALUES (?, ?, ?, ?, ?)''', 
                 ('/static/test1.jpg', '123 Test St', 'testowner', 100.0, json.dumps(['2025-04-01'])))
    conn.execute('''INSERT INTO cart (username, image_id) VALUES (?, ?)''', ('testuser', 1))
    conn.commit()
    conn.close()

def test_cart_page_get(client):
    """Test the /cart page when the user is logged in and the cart is not empty."""
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'  # Simulate logged-in user
    
    setup_test_user_and_cart()  # Setup user and add item to the cart
    
    response = client.get('/cart')
    
    # Check if the cart is populated and proper information is displayed
    assert response.status_code == 200
    assert b'123 Test St' in response.data  # Check that the address from the cart item is displayed
    assert b'100.0' in response.data  # Check that the price is displayed
    assert b'Total: 101.0' in response.data  # Total should be price + fee (1%)
    assert b'Subtotal: 100.0' in response.data  # Subtotal should be the price of the item

def test_cart_empty_when_logged_in(client):
    """Test the /cart page when the user is logged in but their cart is empty."""
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'  # Simulate logged-in user

    # Ensure the cart is empty for this user
    conn = get_db_connection()
    conn.execute("DELETE FROM cart WHERE username = 'testuser'")
    conn.commit()
    conn.close()

    response = client.get('/cart')

    # Check that an empty cart message is displayed
    assert response.status_code == 200
    assert b'Your cart is empty' in response.data  # Ensure the empty cart message is present

def test_cart_redirect_when_not_logged_in(client):
    """Test redirection when the user is not logged in."""
    response = client.get('/cart')
    assert response.status_code == 302  # Should redirect
    assert response.headers['Location'] == '/login'  # Should redirect to login page

def test_cart_with_multiple_items(client):
    """Test the /cart page when the user has multiple items in the cart."""
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'  # Simulate logged-in user

    # Set up a test user and add multiple items to their cart
    conn = get_db_connection()
    conn.execute("DELETE FROM users WHERE username = 'testuser'")
    conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('testuser', 'testpass'))
    
    # Insert multiple images and add them to the cart
    conn.execute('''INSERT INTO user_uploads (image_path, address, owner, price, datesBooked) 
                    VALUES (?, ?, ?, ?, ?)''', 
                 ('/static/test1.jpg', '123 Test St', 'testowner', 100.0, json.dumps(['2025-04-01'])))
    conn.execute('''INSERT INTO user_uploads (image_path, address, owner, price, datesBooked) 
                    VALUES (?, ?, ?, ?, ?)''', 
                 ('/static/test2.jpg', '456 Test St', 'testowner2', 150.0, json.dumps(['2025-04-02'])))
    conn.execute('''INSERT INTO cart (username, image_id) VALUES (?, ?), (?, ?)''', 
                 ('testuser', 1, 'testuser', 2))
    conn.commit()
    conn.close()

    response = client.get('/cart')

    # Check if both items are in the cart
    assert response.status_code == 200
    assert b'123 Test St' in response.data  # First item address
    assert b'456 Test St' in response.data  # Second item address
    assert b'Subtotal: 250.0' in response.data  # Subtotal should be 100 + 150 = 250
    assert b'Total: 252.5' in response.data  # Total should include fee (250 + 2.5)

def test_cart_disabled_dates(client):
    """Test if the disabled dates are correctly passed to the cart page."""
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'  # Simulate logged-in user

    # Set up a test user and add items with datesBooked
    setup_test_user_and_cart()

    response = client.get('/cart')

    # Ensure disabled dates are passed correctly
    assert b'2025-04-01' in response.data  # Disabled date should appear on the page
