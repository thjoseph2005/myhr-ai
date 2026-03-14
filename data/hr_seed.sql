PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS departments (
  department_id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  code TEXT NOT NULL UNIQUE,
  leader_employee_id INTEGER
);

CREATE TABLE IF NOT EXISTS employees (
  employee_id INTEGER PRIMARY KEY,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  department_id INTEGER NOT NULL,
  title TEXT NOT NULL,
  manager_id INTEGER,
  employment_type TEXT NOT NULL,
  location TEXT NOT NULL,
  start_date TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'active',
  FOREIGN KEY (department_id) REFERENCES departments(department_id),
  FOREIGN KEY (manager_id) REFERENCES employees(employee_id)
);

DELETE FROM employees;
DELETE FROM departments;

INSERT INTO departments (department_id, name, code, leader_employee_id) VALUES
  (1, 'Human Resources', 'HR', 100),
  (2, 'Finance', 'FIN', 200),
  (3, 'Engineering', 'ENG', 300),
  (4, 'Sales', 'SAL', 400),
  (5, 'Operations', 'OPS', 500);

INSERT INTO employees (employee_id, first_name, last_name, email, department_id, title, manager_id, employment_type, location, start_date, status) VALUES
  (100, 'Maya', 'Patel', 'maya.patel@myhr-ai.local', 1, 'VP of Human Resources', NULL, 'Full-time', 'New York, NY', '2019-03-15', 'active'),
  (101, 'Olivia', 'Chen', 'olivia.chen@myhr-ai.local', 1, 'HR Business Partner', 100, 'Full-time', 'New York, NY', '2021-06-01', 'active'),
  (102, 'Daniel', 'Brooks', 'daniel.brooks@myhr-ai.local', 1, 'Benefits Specialist', 100, 'Full-time', 'Charlotte, NC', '2022-02-14', 'active'),
  (200, 'Marcus', 'Lee', 'marcus.lee@myhr-ai.local', 2, 'Director of Finance', NULL, 'Full-time', 'New York, NY', '2018-09-10', 'active'),
  (201, 'Sophia', 'Ramirez', 'sophia.ramirez@myhr-ai.local', 2, 'Senior Financial Analyst', 200, 'Full-time', 'Chicago, IL', '2020-01-20', 'active'),
  (300, 'Nina', 'Shah', 'nina.shah@myhr-ai.local', 3, 'VP of Engineering', NULL, 'Full-time', 'San Francisco, CA', '2017-07-05', 'active'),
  (301, 'Ethan', 'Wright', 'ethan.wright@myhr-ai.local', 3, 'Engineering Manager', 300, 'Full-time', 'Austin, TX', '2019-11-18', 'active'),
  (302, 'Priya', 'Nair', 'priya.nair@myhr-ai.local', 3, 'Senior Software Engineer', 301, 'Full-time', 'Austin, TX', '2022-05-09', 'active'),
  (400, 'Jordan', 'Kim', 'jordan.kim@myhr-ai.local', 4, 'VP of Sales', NULL, 'Full-time', 'Boston, MA', '2018-04-23', 'active'),
  (401, 'Ava', 'Morrison', 'ava.morrison@myhr-ai.local', 4, 'Account Executive', 400, 'Full-time', 'Atlanta, GA', '2023-01-16', 'active'),
  (500, 'Samuel', 'Reed', 'samuel.reed@myhr-ai.local', 5, 'Director of Operations', NULL, 'Full-time', 'Dallas, TX', '2019-08-12', 'active'),
  (501, 'Grace', 'Turner', 'grace.turner@myhr-ai.local', 5, 'Operations Analyst', 500, 'Full-time', 'Dallas, TX', '2021-10-04', 'active');

UPDATE departments SET leader_employee_id = 100 WHERE department_id = 1;
UPDATE departments SET leader_employee_id = 200 WHERE department_id = 2;
UPDATE departments SET leader_employee_id = 300 WHERE department_id = 3;
UPDATE departments SET leader_employee_id = 400 WHERE department_id = 4;
UPDATE departments SET leader_employee_id = 500 WHERE department_id = 5;
