from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os  

app = Flask(__name__)
app.secret_key = 'a_very_secret_key_12345'
# Database configuration (using SQLite as an example)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///WasteManagement.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

def init_db():
    db_path = 'WasteManagement.db'  
    sql_script_path = '../sql/schema.sql'  
    if os.path.exists(db_path):
        print(f"Database '{db_path}' already exists. Skipping initialization.")
        return
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    with open(sql_script_path, 'r') as sql_file:
        sql_script = sql_file.read()
        cursor.executescript(sql_script)
    conn.commit()
    conn.close()
    print(f"Database '{db_path}' initialized successfully.")

@app.route('/')
def home():
    current_year = datetime.now().year
    return render_template('index.html', current_year=current_year)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            conn = sqlite3.connect('WasteManagement.db')
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, password FROM user WHERE email = ?", (email,))
            user = cursor.fetchone()
            conn.close()
            if user and check_password_hash(user[1], password):
                session['user_id'] = user[0]  # Store user_id in session
                flash('Login successful!', 'success')
                return redirect(url_for('user_dashboard'))
            else:
                flash('Invalid email or password.', 'danger')
        except Exception as e:
            flash('An error occurred. Please try again.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Remove user_id from session
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/admin')
def admin():
    # Check if admin is logged in
    if 'admin_id' not in session:
        flash('Please log in as admin to access the dashboard.', 'danger')
        return redirect(url_for('login'))
    
    try:
        conn = sqlite3.connect('WasteManagement.db')
        cursor = conn.cursor()
        
        # Get admin name
        cursor.execute("SELECT username FROM admin WHERE admin_id = ?", (session['admin_id'],))
        admin = cursor.fetchone()
        admin_name = admin[0] if admin else "Admin"
        
        # Count users
        cursor.execute("SELECT COUNT(*) FROM user")
        user_count = cursor.fetchone()[0]
        
        # Count vehicles
        cursor.execute("SELECT COUNT(*) FROM vehicle")
        vehicle_count = cursor.fetchone()[0]
        
        # Count complaints
        cursor.execute("SELECT COUNT(*) FROM complaint")
        complaint_count = cursor.fetchone()[0]
        
        # Get total waste collected (you may need to adjust this query based on your schema)
        cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM waste_collection")
        waste_collected = cursor.fetchone()[0]
        
        # Get users data
        cursor.execute("""
            SELECT user_id, first_name || ' ' || last_name as name, email, mobile, address
            FROM user
            ORDER BY user_id
            LIMIT 10
        """)
        users = [
            {
                'user_id': row[0],
                'name': row[1],
                'email': row[2],
                'phone': row[3] or "N/A",
                'address': row[4] or "N/A"
            }
            for row in cursor.fetchall()
        ]
        
        # Get vehicles data
        cursor.execute("""
            SELECT v.vehicle_id, v.vehicle_identifier, v.type, v.status
            FROM vehicle v
            ORDER BY v.vehicle_id
            LIMIT 10
        """)
        vehicles = [
            {
                'vehicle_id': row[0],
                'type': row[2] or "Standard",
                'license_plate': row[1],
                'driver': "Assigned Driver",  # You may need to join with a driver table
                'route': "Default Route",     # You may need to join with a route table
                'status': row[3] or "Active",
                'status_class': 'active' if row[3] == 'Active' else ('pending' if row[3] == 'Pending' else 'resolved')
            }
            for row in cursor.fetchall()
        ]
        
        # Get complaints data
        cursor.execute("""
            SELECT c.complaint_id, u.first_name || ' ' || u.last_name as user_name,
                   c.message, a.name as area_name, c.comp_date, c.status
            FROM complaint c
            JOIN user u ON c.user_id = u.user_id
            JOIN area a ON c.area_id = a.area_id
            ORDER BY c.comp_date DESC
            LIMIT 10
        """)
        complaints = [
            {
                'complaint_id': row[0],
                'user_name': row[1],
                'type': "General",  # You might want to add a type field to your complaints
                'location': row[3],
                'date': row[4],
                'message': row[2],
                'status': row[5] or "Pending",
                'status_class': 'active' if row[5] == 'Resolved' else ('pending' if row[5] == 'Pending' else 'resolved')
            }
            for row in cursor.fetchall()
        ]
        
        conn.close()
        
        return render_template(
            'adminDashboard.html',
            admin_name=admin_name,
            user_count=user_count,
            vehicle_count=vehicle_count,
            complaint_count=complaint_count,
            waste_collected=waste_collected,
            users=users,
            vehicles=vehicles,
            complaints=complaints
        )
        
    except Exception as e:
        print(f"Error in admin dashboard: {e}")
        flash('An error occurred while loading the admin dashboard.', 'danger')
        return redirect(url_for('login'))

@app.route('/signup/user', methods=['GET', 'POST'])
def signup_user():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        try:
            conn = sqlite3.connect('WasteManagement.db')
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO user (first_name, last_name, email, password)
                VALUES (?, ?, ?, ?)
                """,
                (name, '', email, hashed_password)  # Assuming `last_name` is optional
            )
            conn.commit()
            conn.close()
            flash('User signup successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already exists. Please use a different email.', 'danger')
    return render_template('signup.html')

@app.route('/signup/vehicle', methods=['POST'])
def signup_vehicle():
    vehicle_id = request.form['vehicle_id']
    password = request.form['password']
    hashed_password = generate_password_hash(password)
    try:
        conn = sqlite3.connect('WasteManagement.db')
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO vehicle (vehicle_identifier, password)
            VALUES (?, ?)
            """,
            (vehicle_id, hashed_password)
        )
        conn.commit()
        conn.close()
        flash('Vehicle signup successful! Please log in.', 'success')
        return redirect(url_for('login'))
    except sqlite3.IntegrityError:
        flash('Vehicle ID already exists. Please use a different ID.', 'danger')
        return redirect(url_for('signup'))

@app.route('/signup/admin', methods=['POST'])
def signup_admin():
    username = request.form['username']
    password = request.form['password']
    hashed_password = generate_password_hash(password)
    try:
        conn = sqlite3.connect('WasteManagement.db')
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO admin (username, password)
            VALUES (?, ?)
            """,
            (username, hashed_password)
        )
        conn.commit()
        conn.close()
        flash('Admin signup successful! Please log in.', 'success')
        return redirect(url_for('login'))
    except sqlite3.IntegrityError:
        flash('Username already exists. Please use a different username.', 'danger')
        return redirect(url_for('signup'))

@app.route('/login/user', methods=['POST'])
def login_user():
    email = request.form['email']
    password = request.form['password']
    try:
        conn = sqlite3.connect('WasteManagement.db')
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, password, first_name, address FROM user WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]  # Store user_id in session
            flash('Login successful!', 'success')
            return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
            return redirect(url_for('login'))
    except Exception as e:
        flash('An error occurred. Please try again.', 'danger')
        return redirect(url_for('login'))

@app.route('/login/vehicle', methods=['POST'])
def login_vehicle():
    vehicle_identifier = request.form['vehicle_identifier']
    password = request.form['password']
    try:
        conn = sqlite3.connect('WasteManagement.db')
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM vehicle WHERE vehicle_identifier = ?", (vehicle_identifier,))
        vehicle = cursor.fetchone()
        conn.close()
        if vehicle and check_password_hash(vehicle[0], password):
            flash('Vehicle login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid Vehicle Identifier or password.', 'danger')
            return redirect(url_for('login'))
    except Exception as e:
        flash('An error occurred. Please try again.', 'danger')
        return redirect(url_for('login'))

@app.route('/login/admin', methods=['POST'])
def login_admin():
    username = request.form['username']
    password = request.form['password']
    try:
        conn = sqlite3.connect('WasteManagement.db')
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM admin WHERE username = ?", (username,))
        admin = cursor.fetchone()
        conn.close()
        if admin and check_password_hash(admin[0], password):
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin'))
        else:
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('login'))
    except Exception as e:
        flash('An error occurred. Please try again.', 'danger')
        return redirect(url_for('login'))

@app.route('/UserDashboard')
def user_dashboard():
    if 'user_id' not in session:
        flash('Please log in to access the dashboard.', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = sqlite3.connect('WasteManagement.db')
    cursor = conn.cursor()

    # Fetch user data
    cursor.execute("""
        SELECT first_name || ' ' || last_name AS full_name, address, u_points
        FROM user WHERE user_id = ?
    """, (user_id,))
    user_data = cursor.fetchone()

    # Fetch areas
    cursor.execute("SELECT area_id, name FROM area")
    areas = cursor.fetchall()

    # Fetch complaints
    cursor.execute("""
        SELECT c.message, c.status, c.comp_date, a.name AS area_name
        FROM complaint c
        JOIN area a ON c.area_id = a.area_id
        WHERE c.user_id = ?
        ORDER BY c.comp_date DESC
    """, (user_id,))
    complaints = cursor.fetchall()

    conn.close()

    if user_data:
        user_name, user_address, user_points = user_data
        return render_template(
            'userDashboard.html',
            user_name=user_name,
            user_address=user_address,
            user_points=user_points,
            areas=[{'area_id': area[0], 'name': area[1]} for area in areas],
            complaints=[
                {'message': complaint[0], 'status': complaint[1], 'comp_date': complaint[2], 'area_name': complaint[3]}
                for complaint in complaints
            ]
        )
    else:
        flash('User not found.', 'danger')
        return redirect(url_for('home'))

@app.route('/update-profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        flash('Please log in to update your profile.', 'danger')
        return redirect(url_for('login'))
        
    address = request.form['address']
    phone = request.form['phone']
    user_id = session['user_id']  # Get user_id from session
    try:
        conn = sqlite3.connect('WasteManagement.db')
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE user SET address = ?, mobile = ? WHERE user_id = ?",
            (address, phone, user_id)
        )
        conn.commit()
        conn.close()
        flash('Profile updated successfully!', 'success')
    except Exception as e:
        flash('An error occurred while updating your profile.', 'danger')
    return redirect(url_for('user_dashboard'))

@app.route('/submit-complaint', methods=['POST'])
def submit_complaint():
    if 'user_id' not in session:
        flash('Please log in to submit a complaint.', 'danger')
        return redirect(url_for('login'))
        
    user_id = session['user_id']  # Get user_id from session
    area_id = request.form['area_id']
    message = request.form['message']
    image = request.files['image'] if 'image' in request.files else None

    # Save the image if provided
    image_path = None
    if image and image.filename != '':
        image_path = f"static/uploads/{image.filename}"
        image.save(image_path)

    try:
        conn = sqlite3.connect('WasteManagement.db')
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO complaint (user_id, area_id, message, image)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, area_id, message, image_path)
        )
        conn.commit()
        conn.close()
        flash('Complaint submitted successfully!', 'success')
    except Exception as e:
        flash('An error occurred while submitting your complaint.', 'danger')
    return redirect(url_for('user_dashboard'))

if __name__ == '__main__':
    init_db()  
    app.run(debug=True)