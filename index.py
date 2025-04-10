from flask import Flask, render_template, request, redirect, url_for, flash  
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key' #for flash messages

#connets to users.db
def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row  # Allows us to access columns by name (e.g., row['username'])
    return conn

# Route for the Home page
@app.route('/')
def home():
    return render_template('homePage.html')

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
            return redirect(url_for('user', username=username))
        else:
            flash("Invalid credentials. Please try again.", "error")

        # Render the login page again with the flash message
        return render_template('loginPage.html')

    return render_template('loginPage.html')

# Route for the Search page
@app.route('/search')
def search():
    return render_template('searchPage.html')

# Route for the Users page
@app.route('/user')
def user():
    username = request.args.get('username')
    return render_template('userPage.html', username=username)
    
# Route for the Users page
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

# Route for the Home page
@app.route('/cart')
def cart():
    return render_template('cartPage.html')

if __name__ == '__main__':
    app.run(debug=True)