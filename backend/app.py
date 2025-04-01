from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
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
            
            # Return with success message
            flash('User signup successful! Please log in.', 'success')
            return redirect(url_for('login'))
            
        except sqlite3.IntegrityError:
            flash('Email already exists. Please use a different email.', 'danger')
            return redirect(url_for('signup') + '?status=error&message=Email already exists. Please use a different email.')
            
        except KeyError as e:
            flash(f'Missing required field: {str(e)}', 'danger')
            return redirect(url_for('signup') + f'?status=error&message=Missing required field: {str(e)}')
            
        except Exception as e:
            flash(f'An error occurred during signup: {str(e)}', 'danger')
            return redirect(url_for('signup') + f'?status=error&message=An error occurred: {str(e)}')
            
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
            
            # Return with success message
            flash('Vehicle registered successfully! Please log in.', 'success')
            return redirect(url_for('login'))
            
        except sqlite3.IntegrityError:
            flash('Vehicle identifier already exists. Please use a different identifier.', 'danger')
            return redirect(url_for('signup') + '?status=error&message=Vehicle identifier already exists. Please use a different one.')
            
        except KeyError as e:
            flash(f'Missing required field: {str(e)}', 'danger')
            return redirect(url_for('signup') + f'?status=error&message=Missing required field: {str(e)}')
            
        except Exception as e:
            flash(f'An error occurred during registration: {str(e)}', 'danger')
            return redirect(url_for('signup') + f'?status=error&message=An error occurred: {str(e)}')
            
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
        flash('Please log in to access your dashboard.', 'danger')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    conn = sqlite3.connect('WasteManagement.db')
    cursor = conn.cursor()
    
    # Get user information
    cursor.execute("""
        SELECT u.first_name, u.last_name, u.email, u.mobile, u.address, 
               u.area_id, a.name as area_name, u.assigned_vehicle_id
        FROM user u
        LEFT JOIN area a ON u.area_id = a.area_id
        WHERE u.user_id = ?
    """, (user_id,))
    
    user_data = cursor.fetchone()
    
    # Get available areas
    cursor.execute("SELECT area_id, name, longitude, latitude FROM area")
    areas = [{'area_id': row[0], 'name': row[1], 'description': f"Location: {row[2]}, {row[3]}"} for row in cursor.fetchall()]
    
    # Get assigned vehicle info if any
    assigned_vehicle = "Not assigned yet"
    if user_data[7]:  # assigned_vehicle_id
        cursor.execute("""
            SELECT type, license_plate, driver_name
            FROM vehicle
            WHERE vehicle_id = ?
        """, (user_data[7],))
        
        vehicle_data = cursor.fetchone()
        if vehicle_data:
            assigned_vehicle = f"{vehicle_data[0] or 'Standard'} ({vehicle_data[1] or 'Not assigned'}) - Driver: {vehicle_data[2] or 'Unassigned'}"
    
    # Get total waste given by user (separate wet and dry)
    cursor.execute("""
        SELECT COALESCE(SUM(bio_wt), 0), COALESCE(SUM(non_bio_wt), 0)
        FROM waste
        WHERE user_id = ?
    """, (user_id,))
    
    waste_data = cursor.fetchone()
    total_wet_waste = waste_data[0] or 0
    total_dry_waste = waste_data[1] or 0
    total_waste = total_wet_waste + total_dry_waste
    
    # Get user complaints
    cursor.execute("""
        SELECT c.complaint_id, a.name as area_name, c.message, c.status, c.comp_date
        FROM complaint c
        JOIN area a ON c.area_id = a.area_id
        WHERE c.user_id = ?
        ORDER BY c.comp_date DESC
    """, (user_id,))
    
    complaints = [
        {
            'complaint_id': row[0],
            'area_name': row[1],
            'message': row[2],
            'status': row[3],
            'comp_date': row[4]
        }
        for row in cursor.fetchall()
    ]
    
    # Check if notes column exists in waste table
    cursor.execute("PRAGMA table_info(waste)")
    columns = cursor.fetchall()
    notes_column_exists = any(col[1] == 'notes' for col in columns)
    
    # Get waste collection history - with check for notes column
    if notes_column_exists:
        cursor.execute("""
            SELECT w.waste_id, w.c_date_time, w.bio_wt, w.non_bio_wt, v.type, v.license_plate, 
                   w.notes
            FROM waste w
            LEFT JOIN vehicle v ON w.vehicle_id = v.vehicle_id
            WHERE w.user_id = ?
            ORDER BY w.c_date_time DESC
        """, (user_id,))
    else:
        cursor.execute("""
            SELECT w.waste_id, w.c_date_time, w.bio_wt, w.non_bio_wt, v.type, v.license_plate
            FROM waste w
            LEFT JOIN vehicle v ON w.vehicle_id = v.vehicle_id
            WHERE w.user_id = ?
            ORDER BY w.c_date_time DESC
        """, (user_id,))
    
    waste_collections = []
    for row in cursor.fetchall():
        vehicle_info = f"{row[4] or 'Unknown'} ({row[5] or 'N/A'})"
        if notes_column_exists:
            waste_collections.append({
                'collection_id': row[0],
                'collection_date': row[1],
                'wet_waste_kg': row[2],
                'dry_waste_kg': row[3],
                'total_waste_kg': row[2] + row[3],
                'vehicle_id': vehicle_info,
                'notes': row[6]
            })
        else:
            waste_collections.append({
                'collection_id': row[0],
                'collection_date': row[1],
                'wet_waste_kg': row[2],
                'dry_waste_kg': row[3],
                'total_waste_kg': row[2] + row[3],
                'vehicle_id': vehicle_info,
                'notes': 'N/A'
            })
    
    # Get total points
    cursor.execute("""
        SELECT u_points FROM user WHERE user_id = ?
    """, (user_id,))
    total_points = cursor.fetchone()[0] or 0
    
    # Update waste_collections to include reward information
    if all([cursor.execute("PRAGMA table_info(waste)").fetchall(), 
           any(col[1] == 'waste_tag' for col in cursor.execute("PRAGMA table_info(waste)").fetchall()),
           any(col[1] == 'reward_status' for col in cursor.execute("PRAGMA table_info(waste)").fetchall()),
           any(col[1] == 'reward_points' for col in cursor.execute("PRAGMA table_info(waste)").fetchall())]):
        cursor.execute("""
            SELECT w.waste_id, w.c_date_time, w.bio_wt, w.non_bio_wt, v.type, v.license_plate, 
                   w.notes, w.waste_tag, w.reward_status, w.reward_points
            FROM waste w
            LEFT JOIN vehicle v ON w.vehicle_id = v.vehicle_id
            WHERE w.user_id = ?
            ORDER BY w.c_date_time DESC
        """, (user_id,))
        
        waste_collections = []
        for row in cursor.fetchall():
            vehicle_info = f"{row[4] or 'Unknown'} ({row[5] or 'N/A'})"
            waste_collections.append({
                'collection_id': row[0],
                'collection_date': row[1],
                'wet_waste_kg': row[2],
                'dry_waste_kg': row[3],
                'total_waste_kg': row[2] + row[3],
                'vehicle_id': vehicle_info,
                'notes': row[6] or 'N/A',
                'waste_tag': row[7] or 'Not Tagged',
                'reward_status': row[8] or 'Pending',
                'reward_points': row[9] or 0
            })
    else:
        # Fallback logic: Use the existing waste collection data or initialize an empty list
        waste_collections = waste_collections or [
            {
                'collection_id': None,
                'collection_date': 'N/A',
                'wet_waste_kg': 0,
                'dry_waste_kg': 0,
                'total_waste_kg': 0,
                'vehicle_id': 'N/A',
                'notes': 'N/A'
            }
        ]
    
    conn.close()
    
    # Check if user has selected an area
    has_selected_area = user_data[5] is not None
    
    return render_template(
        'userDashboard.html',
        user_name=f"{user_data[0]} {user_data[1]}",
        user_email=user_data[2],
        user_phone=user_data[3] or "Not provided",
        user_address=user_data[4] or "Not provided",
        current_area=user_data[6],  # area_name
        user_area_id=user_data[5],  # area_id
        assigned_vehicle=assigned_vehicle,
        total_waste=total_waste,
        total_wet_waste=total_wet_waste,
        total_dry_waste=total_dry_waste,
        areas=areas,
        complaints=complaints,
        waste_collections=waste_collections,
        has_selected_area=has_selected_area,
        total_points=total_points
    )

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
        SELECT u.user_id, u.first_name || ' ' || u.last_name AS name, u.email, u.mobile, 
               u.address, u.area_id, a.name as area_name
        FROM user u
        LEFT JOIN area a ON u.area_id = a.area_id
        ORDER BY u.user_id
        LIMIT 10
    """)
    users = [
        {
            'user_id': row[0],
            'name': row[1],
            'email': row[2],
            'phone': row[3] or 'N/A',
            'address': row[4] or 'N/A',
            'area_id': row[5],
            'area_name': row[6]
        }
        for row in cursor.fetchall()
    ]
    
    # Fetch vehicles for vehicle table with area name
    cursor.execute("""
        SELECT v.vehicle_id, v.type, v.license_plate, v.driver_name, 
               a.name as area_name, 'Active' AS status
        FROM vehicle v
        LEFT JOIN area a ON v.area_id = a.area_id
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
            'area_name': row[4],  # Use area_name instead of route
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
    
    # Check if notes column exists in waste table
    cursor.execute("PRAGMA table_info(waste)")
    columns = cursor.fetchall()
    notes_column_exists = any(col[1] == 'notes' for col in columns)
    
    # Fetch recent waste collections
    if notes_column_exists:
        cursor.execute("""
            SELECT w.waste_id, u.first_name || ' ' || u.last_name AS user_name, 
                w.c_date_time, w.bio_wt, w.non_bio_wt, v.vehicle_id, 
                a.name as area_name, w.notes
            FROM waste w
            JOIN user u ON w.user_id = u.user_id
            JOIN vehicle v ON w.vehicle_id = v.vehicle_id
            LEFT JOIN area a ON u.area_id = a.area_id
            ORDER BY w.c_date_time DESC
            LIMIT 10
        """)
    else:
        cursor.execute("""
            SELECT w.waste_id, u.first_name || ' ' || u.last_name AS user_name, 
                w.c_date_time, w.bio_wt, w.non_bio_wt, v.vehicle_id, 
                a.name as area_name
            FROM waste w
            JOIN user u ON w.user_id = u.user_id
            JOIN vehicle v ON w.vehicle_id = v.vehicle_id
            LEFT JOIN area a ON u.area_id = a.area_id
            ORDER BY w.c_date_time DESC
            LIMIT 10
        """)
    
    recent_collections = []
    for row in cursor.fetchall():
        if notes_column_exists:
            recent_collections.append({
                'collection_id': row[0],
                'user_name': row[1],
                'collection_date': row[2],
                'wet_waste_kg': row[3],
                'dry_waste_kg': row[4],
                'total_waste_kg': row[3] + row[4],
                'vehicle_id': row[5],
                'area_name': row[6],
                'notes': row[7]
            })
        else:
            recent_collections.append({
                'collection_id': row[0],
                'user_name': row[1],
                'collection_date': row[2],
                'wet_waste_kg': row[3],
                'dry_waste_kg': row[4],
                'total_waste_kg': row[3] + row[4],
                'vehicle_id': row[5],
                'area_name': row[6],
                'notes': 'N/A'
            })
    
    # Fetch all waste collections for the modal
    if notes_column_exists:
        cursor.execute("""
            SELECT w.waste_id, u.first_name || ' ' || u.last_name AS user_name, 
                w.c_date_time, w.bio_wt, w.non_bio_wt, v.vehicle_id, 
                a.name as area_name, w.notes
            FROM waste w
            JOIN user u ON w.user_id = u.user_id
            JOIN vehicle v ON w.vehicle_id = v.vehicle_id
            LEFT JOIN area a ON u.area_id = a.area_id
            ORDER BY w.c_date_time DESC
        """)
    else:
        cursor.execute("""
            SELECT w.waste_id, u.first_name || ' ' || u.last_name AS user_name, 
                w.c_date_time, w.bio_wt, w.non_bio_wt, v.vehicle_id, 
                a.name as area_name
            FROM waste w
            JOIN user u ON w.user_id = u.user_id
            JOIN vehicle v ON w.vehicle_id = v.vehicle_id
            LEFT JOIN area a ON u.area_id = a.area_id
            ORDER BY w.c_date_time DESC
        """)
    
    collections = []
    for row in cursor.fetchall():
        if notes_column_exists:
            collections.append({
                'collection_id': row[0],
                'user_name': row[1],
                'collection_date': row[2],
                'wet_waste_kg': row[3],
                'dry_waste_kg': row[4],
                'total_waste_kg': row[3] + row[4],
                'vehicle_id': row[5],
                'area_name': row[6],
                'notes': row[7]
            })
        else:
            collections.append({
                'collection_id': row[0],
                'user_name': row[1],
                'collection_date': row[2],
                'wet_waste_kg': row[3],
                'dry_waste_kg': row[4],
                'total_waste_kg': row[3] + row[4],
                'vehicle_id': row[5],
                'area_name': row[6],
                'notes': 'N/A'
            })
    
    # Fetch all areas for the area assignment dropdown
    cursor.execute("SELECT area_id, name FROM area")
    areas = [{'area_id': row[0], 'name': row[1]} for row in cursor.fetchall()]
    
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
        complaints=complaints,
        areas=areas,
        recent_collections=recent_collections,
        collections=collections
    )

@app.route('/admin/resolve-complaint/<int:complaint_id>', methods=['POST'])
def resolve_complaint(complaint_id):
    if 'admin_id' not in session:
        return jsonify({'success': False, 'message': 'Not authorized'})
    
    try:
        conn = sqlite3.connect('WasteManagement.db')
        cursor = conn.cursor()
        
        # Update complaint status and set resolved date
        cursor.execute("""
            UPDATE complaint 
            SET status = 'Resolved', resolved_date = CURRENT_TIMESTAMP 
            WHERE complaint_id = ?
        """, (complaint_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Complaint resolved successfully'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

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
        SELECT vehicle_id, vehicle_identifier, driver_name, driver_phone, type, 
               license_plate, route, area_id, status
        FROM vehicle WHERE vehicle_id = ?
    """, (vehicle_id,))
    vehicle_row = cursor.fetchone()
    
    if not vehicle_row:
        flash('Vehicle not found.', 'danger')
        return redirect(url_for('home'))
    
    # Create vehicle object
    vehicle = {
        'vehicle_id': vehicle_row[0],
        'vehicle_identifier': vehicle_row[1],
        'driver_name': vehicle_row[2] or 'Not assigned',
        'driver_phone': vehicle_row[3] or 'N/A',
        'type': vehicle_row[4] or 'Standard',
        'license_plate': vehicle_row[5] or 'Not assigned',
        'route': vehicle_row[6] or 'Not assigned',
        'area_id': vehicle_row[7],
        'status': vehicle_row[8] or 'Active',
        'status_class': 'collected' if vehicle_row[8] == 'Active' else 'pending'
    }
    
    # Get area name if assigned
    if vehicle['area_id']:
        cursor.execute("SELECT name FROM area WHERE area_id = ?", (vehicle['area_id'],))
        area_row = cursor.fetchone()
        vehicle['area_name'] = area_row[0] if area_row else 'Unknown Area'
    else:
        vehicle['area_name'] = 'Not Assigned'

    # Fetch assigned users
    cursor.execute("""
        SELECT u.user_id, u.first_name || ' ' || u.last_name AS name, 
               u.address, u.mobile AS phone
        FROM user u
        WHERE u.assigned_vehicle_id = ?
    """, (vehicle_id,))
    
    users_data = cursor.fetchall()
    
    # Get today's date in YYYY-MM-DD format
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Check which users have collection records for today
    assigned_users = []
    for user_row in users_data:
        # Check if user has waste collection today
        cursor.execute("""
            SELECT COUNT(*) 
            FROM waste 
            WHERE user_id = ? AND vehicle_id = ? AND date(c_date_time) = ?
        """, (user_row[0], vehicle_id, today))
        
        has_collection = cursor.fetchone()[0] > 0
        
        assigned_users.append({
            'user_id': user_row[0],
            'name': user_row[1],
            'address': user_row[2] or 'No address provided',
            'phone': user_row[3] or 'No phone provided',
            'today_collection': has_collection
        })

    # Count today's collections
    cursor.execute("""
        SELECT COUNT(*) 
        FROM waste 
        WHERE vehicle_id = ? AND date(c_date_time) = ?
    """, (vehicle_id, today))
    today_collections = cursor.fetchone()[0]

    # Get total wet waste
    cursor.execute("""
        SELECT COALESCE(SUM(bio_wt), 0)
        FROM waste
        WHERE vehicle_id = ?
    """, (vehicle_id,))
    total_wet_waste = cursor.fetchone()[0] or 0

    # Get total dry waste
    cursor.execute("""
        SELECT COALESCE(SUM(non_bio_wt), 0)
        FROM waste
        WHERE vehicle_id = ?
    """, (vehicle_id,))
    total_dry_waste = cursor.fetchone()[0] or 0

    # Check if notes column exists in waste table
    cursor.execute("PRAGMA table_info(waste)")
    columns = cursor.fetchall()
    notes_column_exists = any(col[1] == 'notes' for col in columns)

    # Get recent collections
    if notes_column_exists:
        # Use the notes column if it exists
        cursor.execute("""
            SELECT w.waste_id, u.first_name || ' ' || u.last_name AS user_name, 
                   w.bio_wt, w.non_bio_wt, w.c_date_time, w.notes
            FROM waste w
            JOIN user u ON w.user_id = u.user_id
            WHERE w.vehicle_id = ?
            ORDER BY w.c_date_time DESC
            LIMIT 10
        """, (vehicle_id,))
    else:
        # Skip the notes column if it doesn't exist
        cursor.execute("""
            SELECT w.waste_id, u.first_name || ' ' || u.last_name AS user_name, 
                   w.bio_wt, w.non_bio_wt, w.c_date_time
            FROM waste w
            JOIN user u ON w.user_id = u.user_id
            WHERE w.vehicle_id = ?
            ORDER BY w.c_date_time DESC
            LIMIT 10
        """, (vehicle_id,))
    
    recent_collections = []
    for row in cursor.fetchall():
        if notes_column_exists:
            recent_collections.append({
                'waste_id': row[0],
                'user_name': row[1],
                'wet_waste_kg': row[2],
                'dry_waste_kg': row[3],
                'total_waste_kg': row[2] + row[3],
                'collection_date': row[4],
                'notes': row[5]
            })
        else:
            recent_collections.append({
                'waste_id': row[0],
                'user_name': row[1],
                'wet_waste_kg': row[2],
                'dry_waste_kg': row[3],
                'total_waste_kg': row[2] + row[3],
                'collection_date': row[4],
                'notes': 'N/A'  # Default value when notes column doesn't exist
            })

    # Get all collection history - same approach with checking for notes column
    if notes_column_exists:
        cursor.execute("""
            SELECT w.waste_id, u.first_name || ' ' || u.last_name AS user_name, 
                   w.bio_wt, w.non_bio_wt, w.c_date_time, w.notes
            FROM waste w
            JOIN user u ON w.user_id = u.user_id
            WHERE w.vehicle_id = ?
            ORDER BY w.c_date_time DESC
        """, (vehicle_id,))
    else:
        cursor.execute("""
            SELECT w.waste_id, u.first_name || ' ' || u.last_name AS user_name, 
                   w.bio_wt, w.non_bio_wt, w.c_date_time
            FROM waste w
            JOIN user u ON w.user_id = u.user_id
            WHERE w.vehicle_id = ?
            ORDER BY w.c_date_time DESC
        """, (vehicle_id,))
    
    collection_history = []
    for row in cursor.fetchall():
        if notes_column_exists:
            collection_history.append({
                'collection_id': row[0],
                'user_name': row[1],
                'wet_waste_kg': row[2],
                'dry_waste_kg': row[3],
                'total_waste_kg': row[2] + row[3],
                'collection_date': row[4],
                'notes': row[5]
            })
        else:
            collection_history.append({
                'collection_id': row[0],
                'user_name': row[1],
                'wet_waste_kg': row[2],
                'dry_waste_kg': row[3],
                'total_waste_kg': row[2] + row[3],
                'collection_date': row[4],
                'notes': 'N/A'  # Default value when notes column doesn't exist
            })

    # Example route stops data (in a real app, this would come from a routing algorithm)
    route_stops = []
    for i, user in enumerate(assigned_users):
        if not user['today_collection']:  # Only include users who haven't had collection today
            route_stops.append({
                'user_name': user['name'],
                'address': user['address'],
                'estimated_time': f"{9 + i//2}:{(i % 2) * 30:02d}",
                'completed': False
            })

    conn.close()

    # Format today's date for display
    current_date = datetime.now().strftime('%B %d, %Y')

    return render_template(
        'vehicleDashboard.html',
        vehicle=vehicle,
        driver_name=session.get('driver_name', 'Driver'),
        assigned_users=assigned_users,
        assigned_users_count=len(assigned_users),
        today_collections=today_collections,
        total_wet_waste=total_wet_waste,
        total_dry_waste=total_dry_waste,
        recent_collections=recent_collections,
        collection_history=collection_history,
        route_stops=route_stops,
        current_date=current_date
    )

@app.route('/admin/complaint-details/<int:complaint_id>')
def get_complaint_details(complaint_id):
    if 'admin_id' not in session:
        return jsonify({'success': False, 'message': 'Not authorized'})
    
    try:
        conn = sqlite3.connect('WasteManagement.db')
        cursor = conn.cursor()
        
        # Fetch complaint details with user information
        cursor.execute("""
            SELECT c.complaint_id, c.message, c.status, c.comp_date, c.resolved_date, c.image,
                   u.first_name || ' ' || u.last_name AS user_name,
                   u.email AS user_email, u.mobile AS user_phone,
                   a.name AS location,
                   'Waste Collection' AS type
            FROM complaint c
            JOIN user u ON c.user_id = u.user_id
            JOIN area a ON c.area_id = a.area_id
            WHERE c.complaint_id = ?
        """, (complaint_id,))
        
        complaint_data = cursor.fetchone()
        conn.close()
        
        if not complaint_data:
            return jsonify({'success': False, 'message': 'Complaint not found'})
        
        # Format the complaint data
        complaint = {
            'complaint_id': complaint_data[0],
            'message': complaint_data[1],
            'status': complaint_data[2],
            'date': complaint_data[3],
            'resolved_date': complaint_data[4],
            'image': complaint_data[5],
            'user_name': complaint_data[6],
            'user_email': complaint_data[7],
            'user_phone': complaint_data[8],
            'location': complaint_data[9],
            'type': complaint_data[10]
        }
        
        return jsonify({'success': True, 'complaint': complaint})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Add this route for collection details
@app.route('/admin/collection-details/<int:collection_id>')
def get_collection_details(collection_id):
    if 'admin_id' not in session:
        return jsonify({'success': False, 'message': 'Not authorized'})
    
    try:
        conn = sqlite3.connect('WasteManagement.db')
        cursor = conn.cursor()
        
        # Fetch collection details with user information
        cursor.execute("""
            SELECT w.waste_id, w.c_date_time, w.bio_wt, w.non_bio_wt, 
                   w.notes, w.waste_tag, w.reward_status, w.reward_points,
                   u.first_name || ' ' || u.last_name AS user_name,
                   u.email AS user_email, u.mobile AS user_phone,
                   v.vehicle_id, a.name AS area_name
            FROM waste w
            JOIN user u ON w.user_id = u.user_id
            JOIN vehicle v ON w.vehicle_id = v.vehicle_id
            LEFT JOIN area a ON u.area_id = a.area_id
            WHERE w.waste_id = ?
        """, (collection_id,))
        
        collection_data = cursor.fetchone()
        conn.close()
        
        if not collection_data:
            return jsonify({'success': False, 'message': 'Collection not found'})
        
        # Format the collection data
        collection = {
            'collection_id': collection_data[0],
            'collection_date': collection_data[1],
            'wet_waste_kg': collection_data[2],
            'dry_waste_kg': collection_data[3],
            'total_waste_kg': collection_data[2] + collection_data[3],
            'notes': collection_data[4],
            'waste_tag': collection_data[5],
            'reward_status': collection_data[6] or 'Pending',
            'reward_points': collection_data[7] or 0,
            'user_name': collection_data[8],
            'user_email': collection_data[9],
            'user_phone': collection_data[10],
            'vehicle_id': collection_data[11],
            'area_name': collection_data[12],
        }
        
        return jsonify({'success': True, 'collection': collection})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Add this route to handle user area updates

@app.route('/update-user-area', methods=['POST'])
def update_user_area():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    try:
        # Get the area ID from the POST request
        data = request.json
        area_id = data.get('area_id')
        
        if not area_id:
            return jsonify({'success': False, 'message': 'No area selected'})
        
        user_id = session['user_id']
        
        # Connect to the database
        conn = sqlite3.connect('WasteManagement.db')
        cursor = conn.cursor()
        
        # Update the user's area
        cursor.execute(
            "UPDATE user SET area_id = ? WHERE user_id = ?",
            (area_id, user_id)
        )
        
        # Get the area name
        cursor.execute("SELECT name FROM area WHERE area_id = ?", (area_id,))
        area_name = cursor.fetchone()[0]
        
        # Find vehicle assigned to this area
        cursor.execute("""
            SELECT vehicle_id, type, license_plate, driver_name
            FROM vehicle
            WHERE area_id = ? AND status = 'Active'
            LIMIT 1
        """, (area_id,))
        
        vehicle_data = cursor.fetchone()
        
        if vehicle_data:
            # Assign this vehicle to the user
            cursor.execute(
                "UPDATE user SET assigned_vehicle_id = ? WHERE user_id = ?",
                (vehicle_data[0], user_id)
            )
            
            vehicle_info = f"{vehicle_data[1] or 'Standard'} ({vehicle_data[2] or 'Not assigned'}) - Driver: {vehicle_data[3] or 'Unassigned'}"
        else:
            vehicle_info = None
        
        conn.commit()
        conn.close()
        
        response_data = {
            'success': True,
            'area_name': area_name,
            'message': 'Your area has been updated.',
        }
        
        if vehicle_info:
            response_data['vehicle_info'] = vehicle_info
        else:
            response_data['message'] += ' No vehicle is currently assigned to this area. An admin will assign a vehicle soon.'
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Add these routes for vehicle assignment

@app.route('/admin/available-vehicles')
def available_vehicles():
    if 'admin_id' not in session:
        return jsonify({'success': False, 'message': 'Not authorized'})
    
    try:
        conn = sqlite3.connect('WasteManagement.db')
        cursor = conn.cursor()
        
        # Get all active vehicles
        cursor.execute("""
            SELECT vehicle_id, type, license_plate, driver_name 
            FROM vehicle 
            WHERE status = 'Active' OR status IS NULL
        """)
        
        vehicles = [
            {
                'vehicle_id': row[0],
                'type': row[1] or 'Standard',
                'license_plate': row[2] or 'Not assigned',
                'driver_name': row[3] or 'Unassigned'
            }
            for row in cursor.fetchall()
        ]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'vehicles': vehicles
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/assign-vehicle', methods=['POST'])
def assign_vehicle():
    if 'admin_id' not in session:
        return jsonify({'success': False, 'message': 'Not authorized'})
    
    try:
        data = request.json
        user_id = data.get('user_id')
        vehicle_id = data.get('vehicle_id')
        
        if not user_id or not vehicle_id:
            return jsonify({'success': False, 'message': 'Missing user ID or vehicle ID'})
        
        conn = sqlite3.connect('WasteManagement.db')
        cursor = conn.cursor()
        
        # Update the user's assigned vehicle
        cursor.execute(
            "UPDATE user SET assigned_vehicle_id = ? WHERE user_id = ?",
            (vehicle_id, user_id)
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Vehicle assigned successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Add these routes for area and vehicle assignment

@app.route('/admin/assign-area-to-vehicle', methods=['POST'])
def assign_area_to_vehicle():
    if 'admin_id' not in session:
        return jsonify({'success': False, 'message': 'Not authorized'})
    
    try:
        data = request.json
        vehicle_id = data.get('vehicle_id')
        area_id = data.get('area_id')
        
        if not vehicle_id or not area_id:
            return jsonify({'success': False, 'message': 'Missing vehicle ID or area ID'})
        
        conn = sqlite3.connect('WasteManagement.db')
        cursor = conn.cursor()
        
        # Assign area to vehicle
        cursor.execute(
            "UPDATE vehicle SET area_id = ? WHERE vehicle_id = ?",
            (area_id, vehicle_id)
        )
        
        # Get the area name
        cursor.execute("SELECT name FROM area WHERE area_id = ?", (area_id,))
        area_name = cursor.fetchone()[0]
        
        # Update route
        cursor.execute(
            "UPDATE vehicle SET route = ? WHERE vehicle_id = ?",
            (area_name, vehicle_id)
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Area assigned to vehicle successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/get-vehicles-for-area')
def get_vehicles_for_area():
    if 'admin_id' not in session:
        return jsonify({'success': False, 'message': 'Not authorized'})
    
    try:
        area_name = request.args.get('area_name', '')
        
        conn = sqlite3.connect('WasteManagement.db')
        cursor = conn.cursor()
        
        if area_name:
            # Get area ID from name
            cursor.execute("SELECT area_id FROM area WHERE name = ?", (area_name,))
            area_row = cursor.fetchone()
            
            if area_row:
                area_id = area_row[0]
                
                # Get vehicles for this area
                cursor.execute("""
                    SELECT vehicle_id, type, license_plate, driver_name
                    FROM vehicle
                    WHERE area_id = ? AND status = 'Active'
                """, (area_id,))
                
                vehicles = [
                    {
                        'vehicle_id': row[0],
                        'type': row[1],
                        'license_plate': row[2],
                        'driver_name': row[3]
                    }
                    for row in cursor.fetchall()
                ]
            else:
                # If area not found, return empty list
                vehicles = []
        else:
            # If no area specified, get all active vehicles
            cursor.execute("""
                SELECT vehicle_id, type, license_plate, driver_name
                FROM vehicle
                WHERE status = 'Active'
            """)
            
            vehicles = [
                {
                    'vehicle_id': row[0],
                    'type': row[1],
                    'license_plate': row[2],
                    'driver_name': row[3]
                }
                for row in cursor.fetchall()
            ]
        
        conn.close()
        
        return jsonify({'success': True, 'vehicles': vehicles})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/assign-vehicle-to-user', methods=['POST'])
def assign_vehicle_to_user():
    if 'admin_id' not in session:
        return jsonify({'success': False, 'message': 'Not authorized'})
    
    try:
        data = request.json
        user_id = data.get('user_id')
        vehicle_id = data.get('vehicle_id')
        
        if not user_id or not vehicle_id:
            return jsonify({'success': False, 'message': 'Missing user ID or vehicle ID'})
        
        conn = sqlite3.connect('WasteManagement.db')
        cursor = conn.cursor()
        
        # Assign vehicle to user
        cursor.execute(
            "UPDATE user SET assigned_vehicle_id = ? WHERE user_id = ?",
            (vehicle_id, user_id)
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Vehicle assigned to user successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Add this route if you haven't already

@app.route('/admin/get-areas')
def get_areas():
    if 'admin_id' not in session:
        return jsonify({'success': False, 'message': 'Not authorized'})
    
    try:
        conn = sqlite3.connect('WasteManagement.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT area_id, name FROM area")
        areas = [{'area_id': row[0], 'name': row[1]} for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({'success': True, 'areas': areas})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/get-vehicle-area/<int:vehicle_id>')
def get_vehicle_area(vehicle_id):
    if 'admin_id' not in session:
        return jsonify({'success': False, 'message': 'Not authorized'})
    
    try:
        conn = sqlite3.connect('WasteManagement.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT a.name 
            FROM area a
            JOIN vehicle v ON a.area_id = v.area_id
            WHERE v.vehicle_id = ?
        """, (vehicle_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return jsonify({'success': True, 'area_name': result[0]})
        else:
            return jsonify({'success': True, 'area_name': None})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/get-area-vehicles')
def get_area_vehicles():
    if 'admin_id' not in session:
        return jsonify({'success': False, 'message': 'Not authorized'})
    
    try:
        area_name = request.args.get('area_name', '')
        
        conn = sqlite3.connect('WasteManagement.db')
        cursor = conn.cursor()
        
        if area_name:
            # Get area ID from name
            cursor.execute("SELECT area_id FROM area WHERE name = ?", (area_name,))
            area_row = cursor.fetchone()
            
            if area_row:
                area_id = area_row[0]
                
                # Get vehicles for this area
                cursor.execute("""
                    SELECT vehicle_id, type, license_plate, driver_name
                    FROM vehicle
                    WHERE area_id = ? AND (status = 'Active' OR status IS NULL)
                """, (area_id,))
                
                vehicles = [
                    {
                        'vehicle_id': row[0],
                        'type': row[1],
                        'license_plate': row[2],
                        'driver_name': row[3]
                    }
                    for row in cursor.fetchall()
                ]
                
                return jsonify({'success': True, 'vehicles': vehicles})
            
        # Return empty if no area or area not found
        return jsonify({'success': True, 'vehicles': []})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/vehicle/record-collection', methods=['POST'])
def record_collection():
    if 'vehicle_id' not in session:
        return jsonify({'success': False, 'message': 'Not authorized'})
    
    try:
        data = request.json
        user_id = data.get('user_id')
        collection_date = data.get('collection_date')
        wet_waste_kg = float(data.get('wet_waste_kg', 0))
        dry_waste_kg = float(data.get('dry_waste_kg', 0))
        notes = data.get('notes', '')
        waste_tag = data.get('waste_tag', '')
        vehicle_id = session['vehicle_id']
        
        if not user_id or not collection_date:
            return jsonify({'success': False, 'message': 'Missing required fields'})
        
        conn = sqlite3.connect('WasteManagement.db')
        cursor = conn.cursor()
        
        # Check if new columns exist in waste table
        cursor.execute("PRAGMA table_info(waste)")
        columns = cursor.fetchall()
        waste_tag_exists = any(col[1] == 'waste_tag' for col in columns)
        reward_status_exists = any(col[1] == 'reward_status' for col in columns)
        reward_points_exists = any(col[1] == 'reward_points' for col in columns)
        notes_column_exists = any(col[1] == 'notes' for col in columns)
        
        # Construct the query based on available columns
        if all([waste_tag_exists, reward_status_exists, reward_points_exists, notes_column_exists]):
            cursor.execute(
                """
                INSERT INTO waste (user_id, vehicle_id, bio_wt, non_bio_wt, c_date_time, notes, waste_tag, reward_status, reward_points)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending', 0)
                """,
                (user_id, vehicle_id, wet_waste_kg, dry_waste_kg, collection_date, notes, waste_tag)
            )
        elif notes_column_exists:
            cursor.execute(
                """
                INSERT INTO waste (user_id, vehicle_id, bio_wt, non_bio_wt, c_date_time, notes)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, vehicle_id, wet_waste_kg, dry_waste_kg, collection_date, notes)
            )
        else:
            cursor.execute(
                """
                INSERT INTO waste (user_id, vehicle_id, bio_wt, non_bio_wt, c_date_time)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, vehicle_id, wet_waste_kg, dry_waste_kg, collection_date)
            )
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Collection recorded successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Update reward route
@app.route('/admin/update-reward', methods=['POST'])
def update_reward():
    if 'admin_id' not in session:
        return jsonify({'success': False, 'message': 'Not authorized'})
    
    try:
        data = request.json
        collection_id = data.get('collection_id')
        points = data.get('points')
        
        if not collection_id or points is None:
            return jsonify({'success': False, 'message': 'Missing required fields'})
        
        conn = sqlite3.connect('WasteManagement.db')
        cursor = conn.cursor()
        
        # Get user ID for this collection
        cursor.execute("SELECT user_id FROM waste WHERE waste_id = ?", (collection_id,))
        user_row = cursor.fetchone()
        
        if not user_row:
            conn.close()
            return jsonify({'success': False, 'message': 'Collection not found'})
        
        user_id = user_row[0]
        
        # Update the waste record
        cursor.execute(
            "UPDATE waste SET reward_status = 'Given', reward_points = ? WHERE waste_id = ?",
            (points, collection_id)
        )
        
        # Create a reward record
        cursor.execute(
            """
            INSERT INTO reward (user_id, points, status, waste_id)
            VALUES (?, ?, 'Approved', ?)
            """,
            (user_id, points, collection_id)
        )
        
        # Update user's total points
        cursor.execute(
            "UPDATE user SET u_points = u_points + ? WHERE user_id = ?",
            (points, user_id)
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': f'Reward of {points} points has been awarded'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# Reset reward route
@app.route('/admin/reset-reward', methods=['POST'])
def reset_reward():
    if 'admin_id' not in session:
        return jsonify({'success': False, 'message': 'Not authorized'})
    
    try:
        data = request.json
        collection_id = data.get('collection_id')
        
        if not collection_id:
            return jsonify({'success': False, 'message': 'Missing collection ID'})
        
        conn = sqlite3.connect('WasteManagement.db')
        cursor = conn.cursor()
        
        # Get current reward points and user ID
        cursor.execute(
            "SELECT reward_points, user_id FROM waste WHERE waste_id = ?", 
            (collection_id,)
        )
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return jsonify({'success': False, 'message': 'Collection not found'})
        
        current_points = row[0] or 0
        user_id = row[1]
        
        # Reset waste record's reward
        cursor.execute(
            "UPDATE waste SET reward_status = 'Pending', reward_points = 0 WHERE waste_id = ?",
            (collection_id,)
        )
        
        # Delete reward record(s) for this waste
        cursor.execute(
            "DELETE FROM reward WHERE waste_id = ?",
            (collection_id,)
        )
        
        # Subtract points from user's total
        cursor.execute(
            "UPDATE user SET u_points = u_points - ? WHERE user_id = ?",
            (current_points, user_id)
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Reward has been reset'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

if __name__ == '__main__':
    init_db()  
    app.run(debug=True)

