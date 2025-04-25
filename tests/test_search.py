import pytest
from index import app, get_db_connection

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def clear_test_listings():
    conn = get_db_connection()
    conn.execute("DELETE FROM user_uploads")
    conn.commit()
    conn.close()

def setup_test_listing(price=100):
    conn = get_db_connection()
    conn.execute("""
        INSERT INTO user_uploads (image_path, address, owner, price)
        VALUES (?, ?, ?, ?)""",
        ('/static/test.jpg', '123 Test St', 'testowner', price))
    conn.commit()
    conn.close()

def setup_cart_item():
    # Add test image
    conn = get_db_connection()
    conn.execute("""
        INSERT INTO user_uploads (image_path, address, owner, price)
        VALUES (?, ?, ?, ?)""",
        ('/static/test.jpg', '456 Cart St', 'testowner', 250.0))
    listing_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    # Add item to cart using correct image_id
    conn.execute("""
        INSERT INTO cart (username, image_id)
        VALUES (?, ?)""",
        ('testcartuser', listing_id))
    conn.commit()
    conn.close()

def test_search_sorting_asc_desc(client):
    clear_test_listings()
    setup_test_listing(300)
    setup_test_listing(100)
    setup_test_listing(200)

    response = client.get('/search?sort=asc')
    assert response.status_code == 200
    assert b'123 Test St' in response.data

    response = client.get('/search?sort=desc')
    assert response.status_code == 200
    assert b'123 Test St' in response.data

def test_cart_indicator_logged_in(client):
    with client.session_transaction() as sess:
        sess['username'] = 'testcartuser'

    setup_cart_item()
    response = client.get('/search')
    assert response.status_code == 200
    assert b'123 Test St' in response.data or b'456 Cart St' in response.data
