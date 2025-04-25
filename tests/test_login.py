
import pytest
from index import app, get_db_connection

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test'
    with app.test_client() as client:
        yield client

def setup_test_user():
    """Insert a test user into the database."""
    conn = get_db_connection()
    conn.execute("DELETE FROM users WHERE username = 'testuser'")
    conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('testuser', 'testpass'))
    conn.commit()
    conn.close()

def test_login_page_get(client):
    response = client.get('/login')
    assert response.status_code == 200
    assert b"Username:" in response.data
    assert b"Password" in response.data

def test_login_valid_user(client):
    setup_test_user()
    response = client.post('/login', data={'username': 'testuser', 'password': 'testpass'}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Welcome" in response.data or b"user" in response.data.lower()

def test_login_invalid_password(client):
    setup_test_user()
    response = client.post('/login', data={'username': 'testuser', 'password': 'wrongpass'}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Invalid credentials" in response.data

def test_login_nonexistent_user(client):
    response = client.post('/login', data={'username': 'nouser', 'password': 'nopass'}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Invalid credentials" in response.data
