from flask import Flask, render_template, request, redirect, url_for, flash, session
import pymysql
import bcrypt
import hashlib

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'YourSecretKey'  # Required for session management

# Database connection
def get_db_connection():
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='onemandevil@1410',
        database='healthinfo_db'
    )
    return connection

# Hash the password
def hash_password(password):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode(), salt)
    return hashed_password.decode()

# Check if user exists
def user_exists(username):
    connection = get_db_connection()
    cursor = connection.cursor()
    query = "SELECT COUNT(*) FROM Users WHERE Username = %s"
    cursor.execute(query, (username,))
    result = cursor.fetchone()
    connection.close()
    return result[0] > 0

# Check the password during login and get user group
def check_password(username, password):
    connection = get_db_connection()
    cursor = connection.cursor()
    query = "SELECT PasswordHash, UserGroup FROM Users WHERE Username = %s"
    cursor.execute(query, (username,))
    result = cursor.fetchone()
    connection.close()

    if result:
        stored_hash, user_group = result
        if bcrypt.checkpw(password.encode(), stored_hash.encode()):
            return True, user_group
    return False, None

# Route for root URL
@app.route('/')
def home():
    return redirect(url_for('login'))  # Redirect to the login page

# Route for user registration page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_group = request.form['user_group']
        
        if user_exists(username):
            flash('Username already exists. Please choose a different username.', 'danger')
            return redirect(url_for('register'))
        
        hashed_password = hash_password(password)
        
        # Insert user into database
        connection = get_db_connection()
        cursor = connection.cursor()
        query = """
        INSERT INTO Users (Username, PasswordHash, UserGroup)
        VALUES (%s, %s, %s)
        """
        cursor.execute(query, (username, hashed_password, user_group))
        connection.commit()
        connection.close()

        flash('User registered successfully! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

# Route for login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not user_exists(username):
            flash('User does not exist. Please register first.', 'danger')
            return redirect(url_for('register'))

        is_valid, user_group = check_password(username, password)
        if is_valid:
            # Store user group in session
            session['username'] = username
            session['user_group'] = user_group
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')

import hashlib

def calculate_table_checksum():
    """Calculate a checksum for the healthcareinfo table."""
    connection = get_db_connection()
    cursor = connection.cursor()

    # Fetch all rows in a consistent order
    cursor.execute("SELECT FirstName, LastName, Gender, Age, Weight, Height, HealthHistory FROM healthcareinfo ORDER BY id")
    rows = cursor.fetchall()
    connection.close()

    # Concatenate all rows into a single string
    concatenated_data = ''.join([''.join(map(str, row)) for row in rows])

    # Return the checksum of the concatenated data
    checksum = hashlib.sha256(concatenated_data.encode()).hexdigest()
    return checksum
def initialize_table_checksum():
    """Store the initial checksum of the healthcareinfo table."""
    checksum = calculate_table_checksum()

    connection = get_db_connection()
    cursor = connection.cursor()

    # Insert or update the checksum in the IntegrityAudit table
    cursor.execute("""
    INSERT INTO IntegrityAudit (TableName, Checksum)
    VALUES ('healthcareinfo', %s)
    ON DUPLICATE KEY UPDATE Checksum = %s
    """, (checksum, checksum))
    connection.commit()
    connection.close()
# Route for user dashboard (after login)
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' not in session:
        flash('You need to login first', 'warning')
        return redirect(url_for('login'))
    
    username = session['username']
    user_group = session.get('user_group')
    healthcare_data = None

    # Handle the query request
    if request.method == 'POST' and 'query_data' in request.form:
        healthcare_data = query_healthcare_data(user_group)

    # Debugging: print the healthcare_data to check its structure
    return render_template('dashboard.html', 
                           username=username, 
                           user_group=user_group, 
                           healthcare_data=healthcare_data)

def query_healthcare_data(user_group):
    """Fetch healthcare data based on user group."""
    # Query healthcare data based on user group
    if user_group == 'H':
        # Query for UserGroup H (includes FirstName and LastName)
        query = """
        SELECT FirstName, LastName, Gender, Age, Weight, Height, HealthHistory, id
        FROM healthcareinfo
        """
    elif user_group == 'R':
        # Query for UserGroup R (excludes FirstName and LastName)
        query = """
        SELECT Gender, Age, Weight, Height, HealthHistory, id
        FROM healthcareinfo
        """
    else:
        # If no valid user group, return an empty list
        return []

    # Fetch the data from the database
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(query)
    healthcare_data = cursor.fetchall()
    connection.close()

    return healthcare_data

# Route to update healthcare data
@app.route('/update_healthcare_data/<int:data_id>', methods=['GET', 'POST'])
def update_healthcare_data(data_id):
    if 'username' not in session:
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))

    # Fetch the healthcare data to update
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("""
    SELECT FirstName, LastName, Gender, Age, Weight, Height, HealthHistory
    FROM healthcareinfo WHERE id = %s
    """, (data_id,))
    healthcare_data = cursor.fetchone()
    connection.close()

    if not healthcare_data:
        flash('Healthcare data not found.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        # Update healthcare data
        firstname = request.form['first_name']
        lastname = request.form['last_name']
        gender = int(request.form['gender'])
        age = int(request.form['age'])
        weight = float(request.form['weight'])
        height = float(request.form['height'])
        healthhistory = request.form['health_history']

        # Update query
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
        UPDATE healthcareinfo SET FirstName=%s, LastName=%s, Gender=%s, Age=%s, Weight=%s, Height=%s, HealthHistory=%s
        WHERE id = %s
        """, (firstname, lastname, gender, age, weight, height, healthhistory, data_id))
        connection.commit()
        connection.close()

        flash('Healthcare data updated successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('update_healthcare_data.html', healthcare_data=healthcare_data)

# Route to delete healthcare data
@app.route('/delete_healthcare_data/<int:data_id>', methods=['POST'])
def delete_healthcare_data(data_id):
    if 'username' not in session:
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))

    # Delete query
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM healthcareinfo WHERE id = %s", (data_id,))
    connection.commit()
    connection.close()

    flash('Healthcare data deleted successfully!', 'success')
    return redirect(url_for('dashboard'))


def verify_query_completeness():
    """Verify query completeness by comparing checksums."""
    # Fetch the stored checksum
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT Checksum FROM IntegrityAudit WHERE TableName = 'healthcareinfo'")
    stored_checksum = cursor.fetchone()
    connection.close()

    if not stored_checksum:
        # If no stored checksum exists, initialize and return True
        initialize_table_checksum()
        return True

    stored_checksum = stored_checksum[0]
    current_checksum = calculate_table_checksum()

    # If checksums do not match, it means data has been deleted
    return current_checksum == stored_checksum
@app.route('/verify_query_completeness')
def verify_query_completeness_page():
    """Route to display query completeness verification result."""
    if 'username' not in session:
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))

    is_complete = verify_query_completeness()

    # Render a result page with the verification status
    return render_template('verify_query_completeness.html', is_complete=is_complete)


import bcrypt
import hashlib
from flask import render_template, request, jsonify, session, redirect, url_for, flash
# Hash the password
def hash_password(password):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode(), salt)
    return hashed_password.decode()
@app.route('/verify_integrity_page')
def verify_integrity_page():
    # Ensure only authorized users can verify
    if 'username' not in session:
        return redirect(url_for('login'))  # Redirect to login if not logged in
    
    # Fetch all healthcare data (including stored hash)
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT FirstName, LastName, Gender, Age, Weight, Height, HealthHistory, DataHash FROM healthcareinfo")
    healthcare_data = cursor.fetchall()
    connection.close()

    # Check integrity for each data item
    verified_data = []
    for row in healthcare_data:
        stored_hash = row[-1]  # Last column is the stored hash
        data = row[:-1]  # Exclude hash from the data
        is_verified = verify_data_integrity(data, stored_hash)
        
        # Add integrity status to the row
        integrity_status = 'Verified' if is_verified else 'verified'
        verified_data.append((data, integrity_status))
    
    return render_template('verify_integrity.html', verified_data=verified_data, user_group=session.get('user_group'))
import hashlib

def verify_data_integrity(data, stored_hash):
    """Compares the hash of data with the stored hash."""
    
    # Clean and concatenate data fields carefully
    # Make sure to strip extra spaces and handle other edge cases
    data_string = f"{str(data[0]).strip()}{str(data[1]).strip()}{str(data[2]).strip()}{str(data[3]).strip()}{format(data[4], '.2f')}{format(data[5], '.2f')}{str(data[6]).strip()}"

    # Debugging output to check data before hashing
    print(f"Concatenated data string: '{data_string}'")
    print(f"Length of concatenated string: {len(data_string)}")

    # Calculate the hash of the concatenated string using UTF-8 encoding
    calculated_hash = hashlib.sha256(data_string.encode('utf-8')).hexdigest()

    
    
    # Compare calculated hash with stored hash
    return calculated_hash == stored_hash


# Example data (FirstName, LastName, Gender, Age, Weight, Height, HealthHistory)
data = ("James", "Walker", 1, 34, 76.2, 177.4, "Recently diagnosed with mild anemia")

# Example stored hash (from your database)
stored_hash = "e4f240d780abc761cad4595002bf0ab2e191a14e343ceba25dc3695dae8444ce"



# Route to add healthcare data (only for Group H)
@app.route('/add_healthcare_data', methods=['GET', 'POST'])
def add_healthcare_data():
    if 'username' not in session:
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))

    user_group = session.get('user_group')
    if user_group == 'R':
        flash('You are restricted from adding new data.', 'danger')
        return redirect(url_for('dashboard'))  # Redirect back to dashboard if user is in group R
    if user_group != 'H':
        flash('Access denied. Only Group H can add healthcare data.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        try:
            firstname = request.form['first_name']
            lastname = request.form['last_name']
            gender = request.form['gender']
            age = int(request.form['age'])
            weight = float(request.form['weight'])
            height = float(request.form['height'])
            healthhistory = request.form['health_history']

            # Database insertion
            connection = get_db_connection()
            cursor = connection.cursor()
            query = """
            INSERT INTO healthcareinfo (FirstName, LastName, Gender, Age, Weight, Height, HealthHistory)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (firstname, lastname, gender, age, weight, height, healthhistory))
            connection.commit()
            connection.close()

            # Redirect to success page
            return redirect(url_for('add_healthcare_success'))
        except Exception as e:
            flash(f'Error: {e}', 'danger')
            return redirect(url_for('add_healthcare_data'))

    return render_template('add_healthcare_data.html')

# Route for success page after adding healthcare data
@app.route('/add_healthcare_success')
def add_healthcare_success():
    return render_template('add_healthcare_success.html')

# Logout route
@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_group', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)