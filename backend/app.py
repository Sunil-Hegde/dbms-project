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
    
    try:
        if not os.path.exists(sql_script_path):
            print(f"Error: Schema file '{sql_script_path}' not found.")
            return
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        with open(sql_script_path, 'r') as sql_file:
            sql_script = sql_file.read()
        cursor.executescript(sql_script)     
        conn.commit()
    except Exception as e:
        print(f"Error initializing database: {e}")
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"Removed incomplete database file '{db_path}'.")
        return
    finally:
        if 'conn' in locals():
            conn.close()

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
    session.pop('user_id', None)
    session.pop('admin_id', None)
    session.pop('admin_name', None)
    session.pop('vehicle_id', None)
    session.pop('driver_name', None)
    session.pop('user_type', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/signup/user', methods=['GET', 'POST'])
def signup_user():
    if request.method == 'POST':
        try:
            # Get all form fields from the updated signup form
            first_name = request.form['first_name']
            middle_name = request.form.get('middle_name', '')  # Optional
            last_name = request.form['last_name']
            email = request.form['email']
            password = request.form['password']
            mobile = request.form.get('mobile', '')  # Optional
            gender = request.form.get('gender', '')  # Optional
            age = request.form.get('age', None)      # Optional
            address = request.form.get('address', '') # Optional
            
            # Convert age to integer if provided
            if age and age.strip():
                try:
                    age = int(age)
                except ValueError:
                    age = None
            else:
                age = None
                
            # Generate hashed password
            hashed_password = generate_password_hash(password)
            
            conn = sqlite3.connect('WasteManagement.db')
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO user (first_name, middle_name, last_name, email, password, 
                                 mobile, gender, age, address)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (first_name, middle_name, last_name, email, hashed_password, 
                 mobile, gender, age, address)
            )
            conn.commit()
            conn.close()
            flash('User signup successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already exists. Please use a different email.', 'danger')
        except KeyError as e:
            flash(f'Missing required field: {str(e)}', 'danger')
        except Exception as e:
            flash(f'An error occurred during signup: {str(e)}', 'danger')
    return render_template('signup.html')

@app.route('/signup/vehicle', methods=['GET', 'POST'])
def signup_vehicle():
    if request.method == 'POST':
        try:
            vehicle_identifier = request.form['vehicle_identifier']
            password = request.form['password']
            driver_name = request.form.get('driver_name', '')
            driver_phone = request.form.get('driver_phone', '')
            vehicle_type = request.form.get('type', '')
            license_plate = request.form.get('license_plate', '')
            route = request.form.get('route', '')
            
            hashed_password = generate_password_hash(password)
            
            conn = sqlite3.connect('WasteManagement.db')
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO vehicle (vehicle_identifier, password, driver_name, driver_phone, 
                                    type, license_plate, route)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (vehicle_identifier, hashed_password, driver_name, driver_phone, 
                 vehicle_type, license_plate, route)
            )
            conn.commit()
            conn.close()
            flash('Vehicle registered successfully! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Vehicle identifier already exists. Please use a different identifier.', 'danger')
        except KeyError as e:
            flash(f'Missing required field: {str(e)}', 'danger')
        except Exception as e:
            flash(f'An error occurred during registration: {str(e)}', 'danger')
    return render_template('signup.html')

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

# Add these routes after your existing login functions

@app.route('/login/admin', methods=['POST'])
def login_admin():
    username = request.form['username']
    password = request.form['password']
    
    try:
        conn = sqlite3.connect('WasteManagement.db')
        cursor = conn.cursor()
        
        # Query admin
        cursor.execute("SELECT admin_id, password, name FROM admin WHERE username = ?", (username,))
        admin = cursor.fetchone()
        conn.close()
        
        if admin and check_password_hash(admin[1], password):
            session['admin_id'] = admin[0]
            session['admin_name'] = admin[2]
            session['user_type'] = 'admin'
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('login'))
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'danger')
        return redirect(url_for('login'))

@app.route('/AdminDashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        flash('Please log in as admin to access the dashboard.', 'danger')
        return redirect(url_for('login'))

    admin_id = session['admin_id']
    conn = sqlite3.connect('WasteManagement.db')
    cursor = conn.cursor()

    # Fetch statistics for dashboard
    # Count users
    cursor.execute("SELECT COUNT(*) FROM user")
    user_count = cursor.fetchone()[0]
    
    # Count vehicles
    cursor.execute("SELECT COUNT(*) FROM vehicle")
    vehicle_count = cursor.fetchone()[0]
    
    # Count complaints
    cursor.execute("SELECT COUNT(*) FROM complaint")
    complaint_count = cursor.fetchone()[0]
    
    # Get total waste collected
    cursor.execute("SELECT COALESCE(SUM(bio_wt + non_bio_wt), 0) FROM waste")
    waste_collected = cursor.fetchone()[0] or 0
    
    # Fetch users for user table
    cursor.execute("""
        SELECT user_id, first_name || ' ' || last_name AS name, email, mobile, address
        FROM user
        ORDER BY user_id
        LIMIT 10
    """)
    users = [
        {
            'user_id': row[0],
            'name': row[1],
            'email': row[2],
            'phone': row[3] or 'N/A',
            'address': row[4] or 'N/A'
        }
        for row in cursor.fetchall()
    ]
    
    # Fetch vehicles for vehicle table
    cursor.execute("""
        SELECT v.vehicle_id, v.type, v.license_plate, v.driver_name, v.route, 'Active' AS status
        FROM vehicle v
        ORDER BY v.vehicle_id
        LIMIT 10
    """)
    vehicles = []
    for row in cursor.fetchall():
        status = row[5] or 'Active'
        status_class = 'active'
        if status.lower() == 'maintenance':
            status_class = 'pending'
        elif status.lower() == 'inactive':
            status_class = 'resolved'
            
        vehicles.append({
            'vehicle_id': row[0],
            'type': row[1] or 'Standard',
            'license_plate': row[2] or 'Not assigned',
            'driver': row[3] or 'Unassigned',
            'route': row[4] or 'Not assigned',
            'status': status,
            'status_class': status_class
        })
    
    # Fetch complaints for complaint table
    cursor.execute("""
        SELECT c.complaint_id, u.first_name || ' ' || u.last_name AS user_name, 
               'Waste Collection' AS type, a.name AS location, c.comp_date, c.status
        FROM complaint c
        JOIN user u ON c.user_id = u.user_id
        JOIN area a ON c.area_id = a.area_id
        ORDER BY c.comp_date DESC
        LIMIT 10
    """)
    complaints = []
    for row in cursor.fetchall():
        status = row[5] or 'Pending'
        status_class = 'pending'
        if status.lower() == 'resolved':
            status_class = 'resolved'
        elif status.lower() == 'active':
            status_class = 'active'
            
        complaints.append({
            'complaint_id': row[0],
            'user_name': row[1],
            'type': row[2],
            'location': row[3],
            'date': row[4],
            'status': status,
            'status_class': status_class
        })
    
    conn.close()

    return render_template(
        'adminDashboard.html',
        admin_name=session.get('admin_name', 'Admin'),
        user_count=user_count,
        vehicle_count=vehicle_count,
        complaint_count=complaint_count,
        waste_collected=waste_collected,
        users=users,
        vehicles=vehicles,
        complaints=complaints
    )

@app.route('/admin/resolve-complaint/<int:complaint_id>', methods=['POST'])
def resolve_complaint(complaint_id):
    if 'admin_id' not in session:
        return {'success': False, 'message': 'Not authorized'}
    
    try:
        conn = sqlite3.connect('WasteManagement.db')
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE complaint SET status = 'Resolved', resolved_date = CURRENT_TIMESTAMP WHERE complaint_id = ?",
            (complaint_id,)
        )
        conn.commit()
        conn.close()
        return {'success': True}
    except Exception as e:
        return {'success': False, 'message': str(e)}

@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if 'admin_id' not in session:
        return {'success': False, 'message': 'Not authorized'}
    
    try:
        conn = sqlite3.connect('WasteManagement.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        return {'success': True}
    except Exception as e:
        return {'success': False, 'message': str(e)}

@app.route('/login/vehicle', methods=['POST'])
def login_vehicle():
    vehicle_id = request.form['vehicle_id']
    password = request.form['password']
    
    try:
        conn = sqlite3.connect('WasteManagement.db')
        cursor = conn.cursor()
        cursor.execute("SELECT vehicle_id, password, driver_name FROM vehicle WHERE vehicle_identifier = ?", (vehicle_id,))
        vehicle = cursor.fetchone()
        conn.close()
        
        if vehicle and check_password_hash(vehicle[1], password):
            session['vehicle_id'] = vehicle[0]
            session['user_type'] = 'vehicle'
            session['driver_name'] = vehicle[2]
            flash('Vehicle login successful!', 'success')
            return redirect(url_for('vehicle_dashboard'))
        else:
            flash('Invalid vehicle ID or password.', 'danger')
            return redirect(url_for('login'))
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'danger')
        return redirect(url_for('login'))

@app.route('/VehicleDashboard')
def vehicle_dashboard():
    if 'vehicle_id' not in session:
        flash('Please log in to access the dashboard.', 'danger')
        return redirect(url_for('login'))

    vehicle_id = session['vehicle_id']
    conn = sqlite3.connect('WasteManagement.db')
    cursor = conn.cursor()

    # Fetch vehicle data
    cursor.execute("""
        SELECT vehicle_identifier, driver_name, driver_phone, type, license_plate, route
        FROM vehicle WHERE vehicle_id = ?
    """, (vehicle_id,))
    vehicle_data = cursor.fetchone()

    # Fetch waste collection history
    cursor.execute("""
        SELECT w.waste_id, u.first_name || ' ' || u.last_name AS user_name, 
               w.bio_wt, w.non_bio_wt, w.c_date_time
        FROM waste w
        JOIN user u ON w.user_id = u.user_id
        WHERE w.vehicle_id = ?
        ORDER BY w.c_date_time DESC
        LIMIT 20
    """, (vehicle_id,))
    collections = cursor.fetchall()

    conn.close()

    if vehicle_data:
        vehicle_identifier, driver_name, driver_phone, vehicle_type, license_plate, route = vehicle_data
        return render_template(
            'vehicleDashboard.html',
            vehicle_identifier=vehicle_identifier,
            driver_name=driver_name or 'Not assigned',
            driver_phone=driver_phone or 'N/A',
            vehicle_type=vehicle_type or 'Standard',
            license_plate=license_plate or 'Not assigned',
            route=route or 'Not assigned',
            collections=[
                {
                    'id': c[0],
                    'user': c[1],
                    'bio_waste': c[2],
                    'non_bio_waste': c[3],
                    'total_waste': c[2] + c[3],
                    'date': c[4]
                }
                for c in collections
            ]
        )
    else:
        flash('Vehicle not found.', 'danger')
        return redirect(url_for('home'))

# Add this route to handle complaint details

@app.route('/admin/complaint-details/<int:complaint_id>')
def complaint_details(complaint_id):
    if 'admin_id' not in session:
        return {'success': False, 'message': 'Not authorized'}
    
    try:
        conn = sqlite3.connect('WasteManagement.db')
        cursor = conn.cursor()
        
        # Fetch complaint with user details
        cursor.execute("""
            SELECT 
                c.complaint_id, c.message, c.status, c.comp_date, c.resolved_date, c.image,
                u.first_name || ' ' || u.last_name AS user_name, u.email AS user_email, 
                u.mobile AS user_phone,
                a.name AS location, 'Waste Collection' AS type
            FROM complaint c
            JOIN user u ON c.user_id = u.user_id
            JOIN area a ON c.area_id = a.area_id
            WHERE c.complaint_id = ?
        """, (complaint_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return {'success': False, 'message': 'Complaint not found'}
        
        complaint = {
            'complaint_id': result[0],
            'message': result[1],
            'status': result[2],
            'date': result[3],
            'resolved_date': result[4],
            'image': result[5],
            'user_name': result[6],
            'user_email': result[7],
            'user_phone': result[8],
            'location': result[9],
            'type': result[10]
        }
        
        return {'success': True, 'complaint': complaint}
    except Exception as e:
        return {'success': False, 'message': str(e)}

if __name__ == '__main__':
    init_db()  
    app.run(debug=True)