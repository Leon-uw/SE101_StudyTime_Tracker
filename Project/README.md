# Snowmark Grade Tracker

A comprehensive grade tracking and prediction application built with Flask. Snowmark helps students manage their academic performance by tracking grades, organizing assignments by subject and category, and predicting future grades based on study time.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## Features

- **User Authentication** - Secure registration and login with password hashing
- **Subject Management** - Create, rename, retire/unretire, and delete subjects
- **Category Organization** - Organize assessments into weighted categories (Exams, Homework, etc.)
- **Grade Tracking** - Log assessments with grades, study time, and weights
- **Grade Predictions** - ML-powered predictions based on study history
- **Multi-User Isolation** - Complete data separation between users
- **Responsive Design** - Works on desktop and mobile devices

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Local Development Setup](#local-development-setup)
- [Environment Variables](#environment-variables)
- [Database Setup](#database-setup)
- [Running the Application](#running-the-application)
- [Running Tests](#running-tests)
- [Deployment](#deployment)
- [Project Structure](#project-structure)
- [API Endpoints](#api-endpoints)

---

## Prerequisites

- **Python 3.9+** - [Download Python](https://www.python.org/downloads/)
- **pip** - Python package manager (included with Python)
- **MySQL Database** - Access to a MySQL server
- **Git** - For cloning the repository

---

## Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd project_team_21/Project

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r src/requirements.txt

# Set environment variables
export Userid="your_mysql_username"
export Password="your_mysql_password"
export SECRET_KEY="your-secret-key-here"

# Run the application
cd src
python3 app.py
```

The app will be available at `http://127.0.0.1:5000`

---

## Local Development Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd project_team_21/Project
```

### 2. Create a Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
# macOS/Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r src/requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the `src/` directory:

```bash
# src/.env
Userid=your_mysql_username
Password=your_mysql_password
SECRET_KEY=your-super-secret-key-change-in-production
```

Or export them directly:

```bash
export Userid="your_mysql_username"
export Password="your_mysql_password"
export SECRET_KEY="your-secret-key-here"
```

---

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `Userid` | MySQL database username | Yes | `root` |
| `Password` | MySQL database password | Yes | (empty) |
| `SECRET_KEY` | Flask session secret key | Yes | `a-very-secret-key` |
| `FLASK_ENV` | Flask environment mode | No | `development` |

---

## Database Setup

The application automatically creates the required database tables on first run. The database schema includes:

- **Users Table** - User authentication data
- **Grades Table** - Assessment records with grades, study time, weights
- **Categories Table** - Category definitions with total weights
- **Subjects Table** - Subject records with timestamps
- **User Preferences Table** - Per-subject user settings

### Database Connection

The app connects to a MySQL server. By default, it uses:
- **Host:** `riku.shoshin.uwaterloo.ca`
- **Database:** `SE101_Team_21`

To use a different database, modify `src/db.py`:

```python
DB_HOST = 'your-database-host'
DB_NAME = 'your-database-name'
```

### Manual Table Creation (Optional)

If needed, tables are created with these schemas:

```sql
-- Users table
CREATE TABLE IF NOT EXISTS {username}_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username varchar(255) NOT NULL UNIQUE,
    password_hash varchar(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Grades table
CREATE TABLE IF NOT EXISTS {username}_grades (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username varchar(255) NOT NULL,
    Subject varchar(255) NOT NULL,
    Category varchar(255) NOT NULL,
    StudyTime double NOT NULL,
    AssignmentName varchar(255) NOT NULL,
    Grade double NULL,
    Weight double NOT NULL,
    IsPrediction BOOLEAN DEFAULT FALSE,
    PredictedGrade double NULL,
    Position INT NOT NULL DEFAULT 0
);

-- Categories table
CREATE TABLE IF NOT EXISTS {username}_categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username varchar(255) NOT NULL,
    Subject varchar(255) NOT NULL,
    CategoryName varchar(255) NOT NULL,
    TotalWeight double NOT NULL,
    DefaultName varchar(255)
);

-- Subjects table
CREATE TABLE IF NOT EXISTS {username}_subjects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username varchar(255) NOT NULL,
    name varchar(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Running the Application

### Development Mode

```bash
cd src
python3 app.py
```

The server starts at `http://127.0.0.1:5000`

### Production Mode (with Gunicorn)

```bash
cd src
gunicorn app:app --bind 0.0.0.0:5000
```

---

## Running Tests

The project includes 122 automated tests covering all features.

### Run All Tests

```bash
cd Project
python3 -m pytest tests/ -v
```

### Run Specific Test File

```bash
python3 -m pytest tests/test_authentication.py -v
python3 -m pytest tests/test_predictions.py -v
```

### Run with Coverage Report

```bash
python3 -m pytest tests/ --cov=src --cov-report=html
```

### Test Files

| File | Tests | Description |
|------|-------|-------------|
| `test_authentication.py` | 15 | User auth, login, security |
| `test_subjects.py` | 18 | Subject CRUD, retire/unretire |
| `test_categories.py` | 17 | Category management, weights |
| `test_assessments.py` | 20 | Assessment CRUD, bulk ops |
| `test_predictions.py` | 27 | Grade prediction system |
| `test_integration.py` | 7 | End-to-end workflows |
| `test_edge_cases.py` | 18 | Boundary conditions |

---

## Deployment

### Vercel Deployment

The project includes Vercel configuration for serverless deployment.

1. **Install Vercel CLI:**
   ```bash
   npm install -g vercel
   ```

2. **Set Environment Variables in Vercel:**
   - `Userid` - MySQL username
   - `Password` - MySQL password
   - `SECRET_KEY` - Flask secret key

3. **Deploy:**
   ```bash
   cd Project
   vercel
   ```

### Manual Server Deployment

1. Clone the repository on your server
2. Install dependencies: `pip install -r src/requirements.txt`
3. Set environment variables
4. Run with Gunicorn:
   ```bash
   gunicorn src.app:app --bind 0.0.0.0:5000 --workers 4
   ```

---

## Project Structure

```
Project/
├── README.md                 # This file
├── vercel.json              # Vercel deployment config
├── requirements.txt         # Root requirements (for Vercel)
├── docs/
│   ├── charter.md           # Project charter
│   ├── requirements.md      # Requirements document
│   ├── test_plan.md         # Test planning
│   ├── test_report.md       # Test results report
│   └── user_stories_use_cases_domain_model.md
├── src/
│   ├── app.py               # Main Flask application
│   ├── db.py                # Database connection & schema
│   ├── crud.py              # Database CRUD operations
│   ├── requirements.txt     # Python dependencies
│   ├── static/
│   │   ├── css/styles.css   # Application styles
│   │   ├── js/main.js       # Frontend JavaScript
│   │   └── images/          # Logo and images
│   └── templates/
│       ├── index.html       # Main dashboard
│       ├── landing.html     # Landing page
│       ├── login.html       # Login page
│       ├── register.html    # Registration page
│       ├── about.html       # About page
│       └── stats.html       # Statistics page
└── tests/
    ├── test_authentication.py
    ├── test_subjects.py
    ├── test_categories.py
    ├── test_assessments.py
    ├── test_predictions.py
    ├── test_integration.py
    └── test_edge_cases.py
```

---

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/login` | User login |
| GET/POST | `/register` | User registration |
| GET | `/logout` | User logout |

### Pages

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Landing page |
| GET | `/home` | Dashboard (requires auth) |
| GET | `/subject/<name>` | Subject detail page |
| GET | `/about` | About page |
| GET | `/stats` | Statistics page |

### Data Operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/add` | Add new assessment |
| POST | `/update` | Update assessment |
| POST | `/delete` | Delete assessment |
| POST | `/delete_bulk` | Bulk delete assessments |
| POST | `/add_subject` | Create new subject |
| POST | `/delete_subject` | Delete subject |
| POST | `/rename_subject` | Rename subject |
| POST | `/retire_subject` | Retire subject |
| POST | `/unretire_subject` | Unretire subject |
| POST | `/add_category` | Add category |
| POST | `/update_category` | Update category |
| POST | `/delete_category` | Delete category |

### Predictions

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/predict` | Get grade prediction |
| POST | `/predict_hours` | Get required hours for target |

### API Data

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/subjects` | Get all subjects (JSON) |
| GET | `/api/grades` | Get all grades (JSON) |
| GET | `/api/categories` | Get all categories (JSON) |

---

## Troubleshooting

### Database Connection Issues

```
Error: Access denied for user
```
- Verify `Userid` and `Password` environment variables
- Check MySQL server is running and accessible

### Module Not Found

```
ModuleNotFoundError: No module named 'flask'
```
- Ensure virtual environment is activated
- Run `pip install -r src/requirements.txt`

### Port Already in Use

```
Address already in use
```
- Kill the existing process: `lsof -i :5000` then `kill <PID>`
- Or use a different port: `python3 app.py --port 5001`

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Run tests: `python3 -m pytest tests/ -v`
5. Commit: `git commit -m "Add your feature"`
6. Push: `git push origin feature/your-feature`
7. Open a Pull Request

---

## License

This project is developed for SE101 at the University of Waterloo.

---

## Team

**Team 21** - SE101 Fall 2025

---

*Last updated: November 30, 2025*
