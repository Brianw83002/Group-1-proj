
import pytest
from index import app, get_db_connection

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test'
    with app.test_client() as client:
        yield client

def delete_test_user(username):
    """Helper to ensure test username doesn't exist before/after test."""
    conn = get_db_connection()
    conn.execute("DELETE FROM users WHERE username = ?", (username,))
    conn.commit()
    conn.close()

def test_create_account_page_get(client):
    response = client.get('/createAccount')
    assert response.status_code == 200
    assert b"Create Account" in response.data or b"Username" in response.data

def test_create_account_password_mismatch(client):
    response = client.post('/createAccount', data={
        'username': 'testuser1',
        'password': 'pass123',
        'confirmpassword': 'pass456'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Passwords do not match" in response.data

def test_create_account_duplicate_username(client):
    # Create user first
    delete_test_user('testuser2')
    conn = get_db_connection()
    conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('testuser2', 'pass123'))
    conn.commit()
    conn.close()

    # Try to create the same user again
    response = client.post('/createAccount', data={
        'username': 'testuser2',
        'password': 'pass123',
        'confirmpassword': 'pass123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Username already exists" in response.data

    delete_test_user('testuser2')

def test_create_account_success(client):
    delete_test_user('newuser')

    response = client.post('/createAccount', data={
        'username': 'newuser',
        'password': 'securepass',
        'confirmpassword': 'securepass'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Username" in response.data or b"Login" in response.data  # Depends on what login page shows

    # Confirm user was added to DB
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", ('newuser',)).fetchone()
    conn.close()
    assert user is not None

    delete_test_user('newuser')
