-- Create the `user` table with area_id and assigned_vehicle_id
CREATE TABLE IF NOT EXISTS user (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT, -- Unique user ID
    first_name VARCHAR(50) NOT NULL,          -- User's first name
    middle_name VARCHAR(50),                  -- User's middle name (optional)
    last_name VARCHAR(50) NOT NULL,           -- User's last name
    email VARCHAR(100) UNIQUE NOT NULL,       -- User's email (used for login)
    password VARCHAR(255) NOT NULL,           -- Hashed password
    mobile VARCHAR(15),                       -- User's mobile number
    gender VARCHAR(10),                       -- User's gender
    age INTEGER,                              -- User's age
    address TEXT,                             -- User's address
    u_points INTEGER DEFAULT 0,               -- User's reward points
    area_id INTEGER,                          -- Foreign key to area table
    assigned_vehicle_id INTEGER,              -- Foreign key to vehicle table 
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- Timestamp for account creation
    FOREIGN KEY (area_id) REFERENCES area(area_id),
    FOREIGN KEY (assigned_vehicle_id) REFERENCES vehicle(vehicle_id)
);

-- Update the vehicle table to include area_id
CREATE TABLE IF NOT EXISTS vehicle (
    vehicle_id INTEGER PRIMARY KEY AUTOINCREMENT, -- Unique vehicle ID
    vehicle_identifier VARCHAR(50) UNIQUE NOT NULL, -- Vehicle identifier (used for login)
    password VARCHAR(255) NOT NULL,                -- Hashed password
    driver_name VARCHAR(100),                      -- Name of the assigned driver
    driver_phone VARCHAR(15),                      -- Driver's phone number
    type VARCHAR(50),                              -- Type of vehicle (e.g., truck, van)
    license_plate VARCHAR(20),                     -- License plate number
    route TEXT,                                    -- Assigned route description
    area_id INTEGER,                               -- Foreign key to area table
    status VARCHAR(20) DEFAULT 'Active',           -- Status of the vehicle
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- Timestamp for vehicle registration
    FOREIGN KEY (area_id) REFERENCES area(area_id)
);

-- Create the `reward` table
CREATE TABLE IF NOT EXISTS reward (
    reward_id INTEGER PRIMARY KEY AUTOINCREMENT, -- Unique reward ID
    user_id INTEGER NOT NULL,                    -- Foreign key to the `user` table
    points INTEGER NOT NULL,                     -- Reward points
    status VARCHAR(20) DEFAULT 'Pending',        -- Status of the reward (e.g., Pending, Approved)
    r_date DATETIME DEFAULT CURRENT_TIMESTAMP,   -- Date of reward issuance
    waste_id INTEGER REFERENCES waste(waste_id), -- Foreign key to the `waste` table
    FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE
);

-- Create the `waste` table
CREATE TABLE IF NOT EXISTS waste (
    waste_id INTEGER PRIMARY KEY AUTOINCREMENT, -- Unique waste ID
    user_id INTEGER NOT NULL,                   -- Foreign key to the `user` table
    vehicle_id INTEGER NOT NULL,                -- Foreign key to the `vehicle` table
    bio_wt FLOAT NOT NULL,                      -- Weight of biodegradable waste
    non_bio_wt FLOAT NOT NULL,                  -- Weight of non-biodegradable waste
    c_date_time DATETIME DEFAULT CURRENT_TIMESTAMP, -- Collection date and time
    notes TEXT,                     -- Additional notes (optional)
    waste_tag VARCHAR(50),                      -- Tag for waste quality (e.g., "Segregated Properly")
    reward_status VARCHAR(20) DEFAULT 'Pending', -- Status of reward (Pending/Given)
    reward_points INTEGER DEFAULT 0,             -- Points awarded for this collection
    FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE,
    FOREIGN KEY (vehicle_id) REFERENCES vehicle(vehicle_id) ON DELETE CASCADE
);

-- Create the `area` table
CREATE TABLE IF NOT EXISTS area (
    area_id INTEGER PRIMARY KEY AUTOINCREMENT, -- Unique area ID
    name VARCHAR(100) NOT NULL,                -- Name of the area
    longitude FLOAT NOT NULL,                  -- Longitude of the area
    latitude FLOAT NOT NULL                    -- Latitude of the area
);

-- Create the `complaint` table
CREATE TABLE IF NOT EXISTS complaint (
    complaint_id INTEGER PRIMARY KEY AUTOINCREMENT, -- Unique complaint ID
    user_id INTEGER NOT NULL,                       -- Foreign key to the `user` table
    area_id INTEGER NOT NULL,                       -- Foreign key to the `area` table
    image TEXT,                                     -- Image related to the complaint (optional)
    message TEXT NOT NULL,                          -- Complaint message
    status VARCHAR(20) DEFAULT 'Pending',           -- Status of the complaint (e.g., Pending, Resolved)
    comp_date DATETIME DEFAULT CURRENT_TIMESTAMP,   -- Complaint submission date
    resolved_date DATETIME,                         -- Date when the complaint was resolved
    FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE,
    FOREIGN KEY (area_id) REFERENCES area(area_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS admin (
    admin_id INTEGER PRIMARY KEY AUTOINCREMENT, -- Unique admin ID
    username VARCHAR(50) UNIQUE NOT NULL,       -- Admin's username
    password VARCHAR(255) NOT NULL,             -- Hashed password
    name VARCHAR(100) NOT NULL                  -- Admin's name
);

-- Insert areas in Bangalore
INSERT INTO area (name, longitude, latitude) VALUES 
    ('Koramangala', 77.6209, 12.9352),
    ('Indiranagar', 77.6410, 12.9784),
    ('Whitefield', 77.7480, 12.9698),
    ('Jayanagar', 77.5934, 12.9299),
    ('Electronic City', 77.6701, 12.8399);

insert into admin values(1, 
'admin', 
'scrypt:32768:8:1$hKmYC1cNKpbb12CS$4726579de9fe983bf7f95d4061a14dac8f218c1f05cbe14958bb5a039c448186c377098bdeba37a5c42332db51bd03b625a138f0d2d6ea3e1efa47b19e2f8cf8', 
'admin');