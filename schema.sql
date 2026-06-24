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
 default_leave_balance REAL NOT NULL DEFAULT 200,
 default_sick_leave_balance REAL NOT NULL DEFAULT 40,
 contracted_daily_hours REAL NOT NULL DEFAULT 8,
 contracted_weekly_hours REAL NOT NULL DEFAULT 40,
 FOREIGN KEY (fk_team_id) REFERENCES Team(pk_team_id) ON DELETE SET NULL,
 FOREIGN KEY (fk_role_id) REFERENCES Roles(pk_role_id)
);

-- Employee Leave Table
CREATE TABLE EmployeeLeave (
 pk_leave_id INTEGER PRIMARY KEY AUTOINCREMENT,
 fk_employee_id INTEGER NOT NULL,
 leave_type TEXT NOT NULL CHECK(leave_type IN ('Annual Leave', 'Sick Leave', 'Time off in Lieu')),
 start_date DATE NOT NULL,
 end_date DATE NOT NULL,
 hours_requested REAL NOT NULL DEFAULT 0,
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
('admin', 'System administrator with full access across all records'),
('manager', 'Team manager with elevated permissions for their assigned team'),
('employee','Standard employee with access to their own records only');

-- Seed Employees
INSERT INTO Employees (first_name, last_name, default_leave_balance, default_sick_leave_balance, contracted_daily_hours, contracted_weekly_hours, fk_role_id)
VALUES
('Admin', 'Admin', 240, 40, 8, 40, (SELECT pk_role_id FROM Roles WHERE name = 'admin')),
('Ryleigh', 'Frost', 160, 40, 8, 40, (SELECT pk_role_id FROM Roles WHERE name = 'employee')),
('Claire', 'Bridges', 114, 40, 8, 40, (SELECT pk_role_id FROM Roles WHERE name = 'employee')),
('Kenyon', 'Buckley', 128, 40, 8, 40, (SELECT pk_role_id FROM Roles WHERE name = 'employee')),
('Memphis', 'Grant', 200, 40, 8, 40, (SELECT pk_role_id FROM Roles WHERE name = 'employee')),
('James', 'Petersen', 240, 40, 8, 40, (SELECT pk_role_id FROM Roles WHERE name = 'employee')),
('Ahmad', 'Gilbert', 164, 40, 8, 40, (SELECT pk_role_id FROM Roles WHERE name = 'employee')),
('Krystal', 'Rosario', 180, 40, 8, 40, (SELECT pk_role_id FROM Roles WHERE name = 'employee')),
('Regan', 'Wiley', 176, 40, 8, 40, (SELECT pk_role_id FROM Roles WHERE name = 'employee')),
('Tatum', 'Fitzgerald', 200, 40, 8, 40, (SELECT pk_role_id FROM Roles WHERE name = 'employee')),
('Kale', 'Herman',  78, 40, 8, 40, (SELECT pk_role_id FROM Roles WHERE name = 'employee'));

-- Seed EmployeeLeave
INSERT INTO EmployeeLeave (fk_employee_id, leave_type, start_date, end_date, hours_requested, status)
VALUES
(2, 'Annual Leave', '2025-06-01', '2025-06-05', 40, 'Approved'),
(6, 'Annual Leave', '2025-07-05', '2025-07-10', 40, 'Rejected'),
(6, 'Annual Leave', '2025-07-05', '2025-07-10', 40, 'Pending'),
(6, 'Annual Leave', '2025-08-01', '2025-08-08', 64, 'Approved'),
(10, 'Annual Leave', '2025-07-15', '2025-07-20', 40, 'Pending'),
(3, 'Sick Leave', '2025-06-10', '2025-06-12', 24, 'Approved'),
(4, 'Sick Leave', '2025-07-12', '2025-07-14', 24, 'Pending'),
(7, 'Sick Leave', '2025-08-10', '2025-08-12', 24, 'Approved'),
(8, 'Sick Leave', '2025-07-18', '2025-07-20', 24, 'Rejected'),
(9, 'Sick Leave', '2025-07-18', '2025-07-20', 24, 'Pending');
