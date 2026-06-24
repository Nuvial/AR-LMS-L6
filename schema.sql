-- Roles Table (lookup for hierarchical position)
CREATE TABLE Roles (
    pk_role_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE CHECK(name IN ('admin', 'manager', 'employee')),
    description TEXT NOT NULL
);

-- Team Table
CREATE TABLE Team (
    pk_team_id INTEGER PRIMARY KEY AUTOINCREMENT,
    fk_manager_id INTEGER DEFAULT NULL,
    name TEXT NOT NULL,
    FOREIGN KEY (fk_manager_id) REFERENCES Employees(pk_employee_id)
);

-- Employees Table
CREATE TABLE Employees (
    pk_employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
    fk_team_id INTEGER DEFAULT NULL,
    fk_role_id INTEGER NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    default_leave_balance REAL NOT NULL DEFAULT 25,
    default_sick_leave_balance REAL NOT NULL DEFAULT 5,
    employee_position TEXT NOT NULL,
    FOREIGN KEY (fk_team_id) REFERENCES Team(pk_team_id) ON DELETE SET NULL,
    FOREIGN KEY (fk_role_id) REFERENCES Roles(pk_role_id)
);

-- Employee Stats Table
CREATE TABLE EmployeeStats (
    pk_stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
    fk_employee_id INTEGER NOT NULL,
    attendance REAL NOT NULL,
    productivity REAL NOT NULL,
    performance REAL NOT NULL,
    date_recorded TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (fk_employee_id) REFERENCES Employees(pk_employee_id) ON DELETE CASCADE
);

-- Employee Leave Table
CREATE TABLE EmployeeLeave (
    pk_leave_id INTEGER PRIMARY KEY AUTOINCREMENT,
    fk_employee_id INTEGER NOT NULL,
    leave_type TEXT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    date_requested TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL,
    comment_employee TEXT,
    comment_admin TEXT,
    FOREIGN KEY (fk_employee_id) REFERENCES Employees(pk_employee_id) ON DELETE CASCADE
);

-- Users Table
CREATE TABLE Users (
    pk_user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    fk_employee_id INTEGER NOT NULL UNIQUE,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    forgot_password BOOLEAN NOT NULL DEFAULT 0,
    pending_confirmation BOOLEAN NOT NULL DEFAULT 0,
    password_reset_required BOOLEAN NOT NULL DEFAULT 0,
    FOREIGN KEY (fk_employee_id) REFERENCES Employees(pk_employee_id) ON DELETE CASCADE
);


-- Seed Roles
INSERT INTO Roles (name, description) VALUES
('admin',    'System administrator with full access across all records'),
('manager',  'Team manager with elevated permissions for their assigned team'),
('employee', 'Standard employee with access to their own records only');

-- Seed Employees
INSERT INTO Employees (first_name, last_name, employee_position, default_leave_balance, fk_role_id)
VALUES
('Admin',    'Admin',      'System Administrator', 30.0,  (SELECT pk_role_id FROM Roles WHERE name = 'admin')),
('Ryleigh',  'Frost',      'Software Engineer',    20.0,  (SELECT pk_role_id FROM Roles WHERE name = 'employee')),
('Claire',   'Bridges',    'Software Engineer',    14.25, (SELECT pk_role_id FROM Roles WHERE name = 'employee')),
('Kenyon',   'Buckley',    'UX Designer',          16.0,  (SELECT pk_role_id FROM Roles WHERE name = 'employee')),
('Memphis',  'Grant',      'QA Engineer',          25.0,  (SELECT pk_role_id FROM Roles WHERE name = 'employee')),
('James',    'Petersen',   'Software Engineer',    30.0,  (SELECT pk_role_id FROM Roles WHERE name = 'employee')),
('Ahmad',    'Gilbert',    'DevOps Engineer',      20.5,  (SELECT pk_role_id FROM Roles WHERE name = 'employee')),
('Krystal',  'Rosario',    'Product Manager',      22.5,  (SELECT pk_role_id FROM Roles WHERE name = 'employee')),
('Regan',    'Wiley',      'Software Engineer',    22.0,  (SELECT pk_role_id FROM Roles WHERE name = 'employee')),
('Tatum',    'Fitzgerald', 'Data Analyst',         25.0,  (SELECT pk_role_id FROM Roles WHERE name = 'employee')),
('Kale',     'Herman',     'Software Engineer',     9.75, (SELECT pk_role_id FROM Roles WHERE name = 'employee'));

-- Seed EmployeeStats
INSERT INTO EmployeeStats (fk_employee_id, attendance, productivity, performance)
VALUES
(1,  90.5,  75.2, 8.5),
(2,  89.0,  65.2, 8.5),
(3,  98.5,  80.0, 6.5),
(4,  100.0, 75.9, 6.6),
(5,  78.0,  82.0, 7.8),
(6,  87.0,  75.0, 5.7),
(7,  98.25, 42.5, 8.9),
(8,  90.5,  55.0, 5.7),
(9,  90.5,  84.25, 9.1),
(10, 99.0,  71.0, 8.7),
(11, 87.6,  75.4, 6.7);

-- Seed EmployeeLeave
INSERT INTO EmployeeLeave (fk_employee_id, leave_type, start_date, end_date, status)
VALUES
(2,  'Annual Leave', '2025-06-01', '2025-06-05', 'Approved'),
(6,  'Annual Leave', '2025-07-05', '2025-07-10', 'Rejected'),
(6,  'Annual Leave', '2025-07-05', '2025-07-10', 'Pending'),
(6,  'Annual Leave', '2025-08-01', '2025-08-08', 'Approved'),
(10, 'Annual Leave', '2025-07-15', '2025-07-20', 'Pending'),
(3,  'Sick Leave',   '2025-06-10', '2025-06-12', 'Approved'),
(4,  'Sick Leave',   '2025-07-12', '2025-07-14', 'Pending'),
(7,  'Sick Leave',   '2025-08-10', '2025-08-12', 'Approved'),
(8,  'Sick Leave',   '2025-07-18', '2025-07-20', 'Rejected'),
(9,  'Sick Leave',   '2025-07-18', '2025-07-20', 'Pending');
