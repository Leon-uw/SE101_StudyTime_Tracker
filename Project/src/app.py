'''from flask import Flask, render_template, request, url_for, jsonify, session, redirect, flash
import json

users = {
    "alice": "1234",
    "bob": "password",
    "admin": "admin"
}

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a-very-secret-key'

# In-memory "database"
study_data = [
    { "id": 1, "subject": "Mathematics", "study_time": 2.5, "assignment_name": "Homework 1", "grade": 85, "weight": 10 },
    { "id": 2, "subject": "History", "study_time": 1.5, "assignment_name": "Essay", "grade": 92, "weight": 15 },
    { "id": 3, "subject": "Science", "study_time": 3.0, "assignment_name": "Lab Report", "grade": 78, "weight": 20 },
    { "id": 4, "subject": "Mathematics", "study_time": 1.0, "assignment_name": "Quiz 2", "grade": 95, "weight": 5 },
    { "id": 5, "subject": "Science", "study_time": 2.5, "assignment_name": "Project Proposal", "grade": None, "weight": 15 }
]
next_id = 6

def calculate_summary(subject):
    """A reusable helper function for calculating summaries for a given subject."""
    if not subject or subject == 'all':
        return None

    subject_items = [log for log in study_data if log['subject'] == subject]
    
    if not subject_items:
        return None

    graded_items = [log for log in subject_items if log.get('grade') is not None]
    total_hours = sum(log['study_time'] for log in subject_items)
    total_weight = sum(log['weight'] for log in graded_items)
    weighted_grade_sum = sum(log['grade'] * log['weight'] for log in graded_items)
    average_grade = weighted_grade_sum / total_weight if total_weight > 0 else 0
    
    return {'total_hours': total_hours, 'average_grade': average_grade, 'total_weight': total_weight}

@app.route('/')
def display_table():
    if 'user' not in session:
        return redirect(url_for('login'))
    filter_subject = request.args.get('subject')
    unique_subjects = sorted(list(set(log['subject'] for log in study_data)))
    data_to_display = study_data
    
    if filter_subject and filter_subject != 'all':
        data_to_display = [log for log in study_data if log['subject'] == filter_subject]

    summary_data = calculate_summary(filter_subject)

    chart_data = {s: sum(log['study_time'] for log in study_data if log['subject'] == s) for s in unique_subjects}
    chart_labels = list(chart_data.keys())
    chart_values = list(chart_data.values())
    return render_template('index.html', data=data_to_display, subjects=unique_subjects, selected_subject=filter_subject, summary_data=summary_data, chart_labels=json.dumps(chart_labels), chart_values=json.dumps(chart_values))

def process_form_data(form):
    required_fields = ['assignment_name', 'study_time', 'weight']
    if not all([form.get(key) for key in required_fields]):
        return None, "Assignment, Time, and Weight are required."
    
    subject = form.get('subject') or form.get('current_filter')
    if not subject or subject == 'all':
        return None, "A valid subject is required."
        
    try:
        grade_str = form.get('grade')
        data = {
            "subject": subject,
            "study_time": float(form.get('study_time')),
            "assignment_name": form.get('assignment_name'),
            "grade": int(grade_str) if grade_str and grade_str.strip() else None,
            "weight": int(form.get('weight'))
        }
        return data, None
    except ValueError:
        return None, "Invalid data. Time, grade, and weight must be valid numbers."

@app.route('/add', methods=['POST'])
def add_log():
    global next_id
    log_data, error = process_form_data(request.form)
    if error:
        return jsonify({'status': 'error', 'message': error}), 400
    
    log_data['id'] = next_id
    study_data.append(log_data)
    next_id += 1
    
    current_filter = request.form.get('current_filter')
    summary = calculate_summary(current_filter)
    
    return jsonify({'status': 'success', 'message': 'Assignment added!', 'log': log_data, 'summary': summary})

@app.route('/update/<int:log_id>', methods=['POST'])
def update_log(log_id):
    update_index = next((i for i, log in enumerate(study_data) if log['id'] == log_id), -1)
    if update_index == -1:
        return jsonify({'status': 'error', 'message': 'Assignment not found.'}), 404
        
    updated_data, error = process_form_data(request.form)
    if error:
        return jsonify({'status': 'error', 'message': error}), 400

    updated_data['id'] = log_id
    study_data[update_index] = updated_data
    
    current_filter = request.form.get('current_filter')
    summary = calculate_summary(current_filter)

    return jsonify({'status': 'success', 'message': 'Assignment updated!', 'log': updated_data, 'summary': summary})

@app.route('/delete/<int:log_id>', methods=['POST'])
def delete_log(log_id):
    current_filter = request.args.get('current_filter') 
    
    log_to_delete = next((log for log in study_data if log['id'] == log_id), None)
    if log_to_delete:
        study_data.remove(log_to_delete)
        summary = calculate_summary(current_filter)
        return jsonify({'status': 'success', 'message': 'Assignment deleted!', 'summary': summary})
        
    return jsonify({'status': 'error', 'message': 'Assignment not found.'}), 404

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username in users and users[username] == password:
            session['user'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('display_table'))
        else:
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Logged out successfully!', 'info')
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password').strip()
        confirm = request.form.get('confirm_password').strip()

        # Validation
        if not username or not password:
            flash("Username and password are required.", "error")
            return redirect(url_for('register'))
        if username in users:
            flash("Username already exists.", "error")
            return redirect(url_for('register'))
        if password != confirm:
            flash("Passwords do not match.", "error")
            return redirect(url_for('register'))

        # Save locally in the in-memory dictionary
        users[username] = password
        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)'''
from flask import Flask, render_template, request, url_for, jsonify, session, redirect, flash
import json
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file in current directory
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Add current directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import init_db, DB_USER
from crud import get_all_grades, add_grade, update_grade

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a-very-secret-key'

# Initialize database when app starts
init_db()

def calculate_summary(subject):
    """A reusable helper function for calculating summaries for a given subject."""
    study_data = get_all_grades()  # Get data from MySQL
    
    if not subject or subject == 'all':
        return None

    subject_items = [log for log in study_data if log['Subject'] == subject]
    
    if not subject_items:
        return None

    graded_items = [log for log in subject_items if log.get('Grade') is not None]
    total_hours = sum(log['StudyTime'] for log in subject_items)
    total_weight = sum(log['Weight'] for log in graded_items)
    weighted_grade_sum = sum(log['Grade'] * log['Weight'] for log in graded_items)
    average_grade = weighted_grade_sum / total_weight if total_weight > 0 else 0
    
    return {'total_hours': total_hours, 'average_grade': average_grade, 'total_weight': total_weight}

@app.route('/')
def display_table():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    study_data = get_all_grades()  # Get data from MySQL
    filter_subject = request.args.get('subject')
    unique_subjects = sorted(list(set(log['Subject'] for log in study_data)))
    data_to_display = study_data
    
    if filter_subject and filter_subject != 'all':
        data_to_display = [log for log in study_data if log['Subject'] == filter_subject]

    summary_data = calculate_summary(filter_subject)

    chart_data = {s: sum(log['StudyTime'] for log in study_data if log['Subject'] == s) for s in unique_subjects}
    chart_labels = list(chart_data.keys())
    chart_values = list(chart_data.values())
    return render_template('index.html', data=data_to_display, subjects=unique_subjects, selected_subject=filter_subject, summary_data=summary_data, chart_labels=json.dumps(chart_labels), chart_values=json.dumps(chart_values))

def process_form_data(form):
    required_fields = ['assignment_name', 'study_time', 'weight']
    if not all([form.get(key) for key in required_fields]):
        return None, "Assignment, Time, and Weight are required."
    
    subject = form.get('subject') or form.get('current_filter')
    if not subject or subject == 'all':
        return None, "A valid subject is required."
        
    try:
        grade_str = form.get('grade')
        data = {
            "subject": subject,
            "study_time": float(form.get('study_time')),
            "assignment_name": form.get('assignment_name'),
            "grade": int(grade_str) if grade_str and grade_str.strip() else None,
            "weight": int(form.get('weight'))
        }
        return data, None
    except ValueError:
        return None, "Invalid data. Time, grade, and weight must be valid numbers."

@app.route('/add', methods=['POST'])
def add_log():
    log_data, error = process_form_data(request.form)
    if error:
        return jsonify({'status': 'error', 'message': error}), 400
    
    # Add to MySQL database
    grade_id = add_grade(
        log_data['subject'], 
        log_data['study_time'], 
        log_data['assignment_name'], 
        log_data['grade'], 
        log_data['weight']
    )
    log_data['id'] = grade_id
    
    current_filter = request.form.get('current_filter')
    summary = calculate_summary(current_filter)
    
    return jsonify({'status': 'success', 'message': 'Assignment added!', 'log': log_data, 'summary': summary})

@app.route('/update/<int:log_id>', methods=['POST'])
def update_log(log_id):
    updated_data, error = process_form_data(request.form)
    if error:
        return jsonify({'status': 'error', 'message': error}), 400

    # Update in MySQL database
    rows_affected = update_grade(
        log_id,
        updated_data['subject'],
        updated_data['study_time'],
        updated_data['assignment_name'],
        updated_data['grade'],
        updated_data['weight']
    )
    
    if rows_affected == 0:
        return jsonify({'status': 'error', 'message': 'Assignment not found.'}), 404
    
    updated_data['id'] = log_id
    current_filter = request.form.get('current_filter')
    summary = calculate_summary(current_filter)

    return jsonify({'status': 'success', 'message': 'Assignment updated!', 'log': updated_data, 'summary': summary})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Simple authentication - just check if it matches .env DB_USER
        if username == DB_USER:
            session['user'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('display_table'))
        else:
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Logged out successfully!', 'info')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    # For now, just redirect to login since we're using .env credentials
    flash("Please use your database credentials to log in.", "info")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
