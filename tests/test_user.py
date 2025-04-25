import pytest
from index import app, get_db_connection

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def clear_test_user():
    conn = get_db_connection()
    conn.execute("DELETE FROM users WHERE username = 'testuser'")
    conn.commit()
    conn.close()

def setup_test_user():
    clear_test_user()  # Ensure the user is deleted before setting up the test
    conn = get_db_connection()
    conn.execute("""
        INSERT INTO users (username, password)
        VALUES (?, ?)""", ('testuser', 'testpass'))
    conn.commit()
    conn.close()

def test_user_redirect_when_not_logged_in(client):
    response = client.get('/user')
    assert response.status_code == 302  # Should redirect to home page
    assert b'Redirecting' in response.data

def test_user_page_when_logged_in(client):
    setup_test_user()  # Make sure the test user is set up
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'

    response = client.get('/user')
    assert response.status_code == 200  # Should render user page
    assert b'testuser' in response.data  # Make sure username appears in the response
