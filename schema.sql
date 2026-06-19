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
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    default_leave_balance REAL NOT NULL DEFAULT 25, -- Base leave balance for all employees,
    default_sick_leave_balance REAL NOT NULL DEFAULT 5, -- Base sick leave balance for all employees
    employee_position TEXT NOT NULL,  /* Team Lead, Developer, Designer, etc.
    Would ideally be stored in a lookup table, but assignment limits to 4 tables maximum. */
    FOREIGN KEY (fk_team_id) REFERENCES Team(pk_team_id) ON DELETE SET NULL
);

-- Employee Stats Table
CREATE TABLE EmployeeStats (
    pk_stat_id INTEGER PRIMARY KEY AUTOINCREMENT, -- Unique ID for each stat entry, allows seeing the history of stats
    fk_employee_id INTEGER NOT NULL,
    attendance REAL NOT NULL,
    productivity REAL NOT NULL,
    performance REAL NOT NULL,
    date_recorded TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (fk_employee_id) REFERENCES Employees(pk_employee_id) ON DELETE CASCADE -- Ensures that if an employee is deleted, their stats are also deleted
);

-- Employee Leave Table
CREATE TABLE EmployeeLeave (
    pk_leave_id INTEGER PRIMARY KEY AUTOINCREMENT, -- Unique ID for each leave request, allows multiple leave requests per employee
    fk_employee_id INTEGER NOT NULL,
    leave_type TEXT NOT NULL, /* Sick Leave, Annual Leave, etc.
    Would ideally be stored in a lookup table, but assignment limits to 4 tables maximum. */
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    date_requested TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL, /* Pending, Approved, etc.
    Would ideally be stored in a lookup table, but assignment limits to 4 tables maximum. */
    comment_employee TEXT, /* Any comments added by employee upon requesting */
    comment_admin TEXT, /* Any comments added by admin/manager upon status decision */
    FOREIGN KEY (fk_employee_id) REFERENCES Employees(pk_employee_id) ON DELETE CASCADE -- Ensures that if an employee is deleted, their leave requests are also deleted
);

-- Users Table
CREATE TABLE Users (
    pk_user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    fk_employee_id INTEGER NOT NULL UNIQUE, -- Foreign key to Employees table, ensures each user is linked to an employee.
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL, -- Hashed password for security
    forgot_password BOOLEAN NOT NULL DEFAULT 0, -- Flag to indicate if the user has requested a password reset
    admin BOOLEAN NOT NULL DEFAULT 0,
    FOREIGN KEY (fk_employee_id) REFERENCES Employees(pk_employee_id) ON DELETE CASCADE -- Ensures that if an employee is deleted, their account is also deleted.
);


-- Insert sample data into Employees table
INSERT INTO Employees (first_name, last_name, employee_position, default_leave_balance)
VALUES
('Admin', 'Admin', 'Administrator', 30.0),
('Ryleigh', 'Frost', 'Employee', 20.0),
('Claire', 'Bridges', 'Employee', 14.25),
('Kenyon', 'Buckley', 'Employee', 16.0),
('Memphis', 'Grant', 'Employee', 25.0),
('James', 'Petersen', 'Employee', 30.0),
('Ahmad', 'Gilbert', 'Employee', 20.5),
('Krystal', 'Rosario', 'Employee', 22.5),
('Regan', 'Wiley', 'Employee', 22.0),
('Tatum', 'Fitzgerald', 'Employee', 25.0),
('Kale', 'Herman', 'Employee', 9.75);

-- EmployeeStats Table
INSERT INTO EmployeeStats (fk_employee_id, attendance, productivity, performance)
VALUES
(1, 90.5, 75.2, 8.5),
(2, 89.0, 65.2, 8.5),
(3, 98.5, 80.0, 6.5),
(4, 100.0, 75.9, 6.6),
(5, 78.0, 82.0, 7.8),
(6, 87.0, 75.0, 5.7),
(7, 98.25, 42.5, 8.9),
(8, 90.5, 55.0, 5.7),
(9, 90.5, 84.25, 9.1),
(10, 99.0, 71.0, 8.7),
(11, 87.6, 75.4, 6.7);

-- EmployeeLeave Table (only for those with leave requests)
INSERT INTO EmployeeLeave (fk_employee_id, leave_type, start_date, end_date, status)
VALUES
(2, 'Annual Leave', '2025-06-01', '2025-06-05', 'Approved'),
(6, 'Annual Leave', '2025-07-05', '2025-07-10', 'Rejected'),
(6, 'Annual Leave', '2025-07-05', '2025-07-10', 'Pending'),
(6, 'Annual Leave', '2025-08-01', '2025-08-08', 'Approved'),
(10, 'Annual Leave', '2025-07-15', '2025-07-20', 'Pending'),
(3, 'Sick Leave', '2025-06-10', '2025-06-12', 'Approved'),
(4, 'Sick Leave', '2025-07-12', '2025-07-14', 'Pending'),
(7, 'Sick Leave', '2025-08-10', '2025-08-12', 'Approved'),
(8, 'Sick Leave', '2025-07-18', '2025-07-20', 'Rejected'),
(9, 'Sick Leave', '2025-07-18', '2025-07-20', 'Pending');