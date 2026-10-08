# Campus Complaint & Maintenance Management System

A web-based Python Flask project that allows students to report campus maintenance problems and allows administrators to manage, prioritize and resolve complaints.

## Features

### Student
- Registration and login
- Submit a complaint
- Select complaint category
- Add description
- View submitted complaints
- Track complaint status
- View complaint history

### Admin
- Admin login
- View all complaints
- Filter by category and status
- Change priority: Low, Medium, High
- Update status: Pending, In Progress, Resolved
- View complaint history

## Technology Stack

- Frontend: HTML, CSS, JavaScript
- Backend: Python + Flask
- Database: MySQL
- Version Control: Git + GitHub

## Project Structure

```text
campus_complaint_system/
├── app.py
├── config.py
├── requirements.txt
├── database/
│   └── schema.sql
├── templates/
├── static/
│   ├── css/
│   └── js/
├── .env.example
├── .gitignore
└── README.md
```

## Requirements

- Python 3.10 or newer recommended
- MySQL 8.x or XAMPP
- VS Code recommended
- Git

## Setup on Windows

### 1. Open the project

Open this folder in VS Code.

### 2. Create virtual environment

```bash
python -m venv venv
```

Activate it:

```bash
venv\Scripts\activate
```

### 3. Install packages

```bash
pip install -r requirements.txt
```

### 4. Start MySQL

If using XAMPP, start MySQL from the XAMPP Control Panel.

### 5. Create the database

Open phpMyAdmin or MySQL command line and run:

```sql
SOURCE path/to/database/schema.sql;
```

Alternatively, open `database/schema.sql` in phpMyAdmin and execute it.

### 6. Check database configuration

Open `config.py`.

Default XAMPP configuration:

```python
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "campus_complaint"
}
```

If your MySQL root user has a password, change it.

### 7. Run Flask

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

## Admin Login

The SQL file contains a demonstration administrator account.

Email:

```text
admin@campus.local
```

Password:

```text
admin123
```

For a real deployment, create/change the administrator password and secret key.

## Student Login

Students can register from the Register page and then log in.

## GitHub

Initialize Git:

```bash
git init
git add .
git commit -m "Initial Campus Complaint Management System"
```

Create a new repository on GitHub and connect it:

```bash
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/campus-complaint-system.git
git push -u origin main
```

Do not upload:
- `venv/`
- `.env`
- passwords
- database dumps containing private user information

The included `.gitignore` handles common local files.

## Future Improvements

- Image upload for complaint evidence
- Email notifications
- Admin user management
- Search by complaint ID
- Pagination
- Dashboard charts
- Deployment to a cloud platform
- Environment variables for production secrets
