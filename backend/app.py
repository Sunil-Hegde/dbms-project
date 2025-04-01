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
    
    # Get total waste given by user
    cursor.execute("""
        SELECT COALESCE(SUM(bio_wt + non_bio_wt), 0)
        FROM waste
        WHERE user_id = ?
    """, (user_id,))
    
    total_waste = cursor.fetchone()[0] or 0
    
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
        assigned_vehicle=assigned_vehicle,
        total_waste=total_waste,
        areas=areas,
        complaints=complaints,
        has_selected_area=has_selected_area
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
        areas=areas
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

if __name__ == '__main__':
    init_db()  
    app.run(debug=True)