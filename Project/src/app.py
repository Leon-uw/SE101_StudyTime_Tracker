from flask import Flask, render_template, request, url_for, jsonify, session, redirect, flash
import json
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a-very-secret-key'

# In-memory user and study data
users = { "alice": "1234", "bob": "password", "admin": "admin" }
study_data = [
    { "id": 1, "subject": "Mathematics", "category": "Homework", "study_time": 2.5, "assignment_name": "Homework 1", "grade": 85, "weight": 10 },
    { "id": 2, "subject": "History", "category": "Essays", "study_time": 1.5, "assignment_name": "Essay on Rome", "grade": 92, "weight": 15 },
    { "id": 3, "subject": "Science", "category": "Labs", "study_time": 3.0, "assignment_name": "Lab Report", "grade": 78, "weight": 20 },
    { "id": 4, "subject": "Mathematics", "category": "Quizzes", "study_time": 1.0, "assignment_name": "Quiz 2", "grade": 95, "weight": 5 },
    { "id": 5, "subject": "Science", "category": "Projects", "study_time": 2.5, "assignment_name": "Project Proposal", "grade": None, "weight": 15 },
    { "id": 6, "subject": "Mathematics", "category": "Homework", "study_time": 2.0, "assignment_name": "Homework 2", "grade": 88, "weight": 10 }
]
next_id = 7

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest': return jsonify({'status': 'error', 'message': 'Authentication required'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def calculate_summary(subject):
    if not subject or subject == 'all': return None
    subject_items = [log for log in study_data if log['subject'] == subject]
    if not subject_items: return None
    graded_items = [log for log in subject_items if log.get('grade') is not None]
    total_hours = sum(log['study_time'] for log in subject_items)
    total_weight = sum(log['weight'] for log in graded_items)
    weighted_grade_sum = sum(log['grade'] * log['weight'] for log in graded_items)
    average_grade = weighted_grade_sum / total_weight if total_weight > 0 else 0
    return {'total_hours': total_hours, 'average_grade': average_grade, 'total_weight': total_weight}

def process_form_data(form):
    required_fields = ['category', 'assignment_name', 'study_time', 'weight']
    if not all([form.get(key) for key in required_fields]): return None, "Category, Assignment, Time, and Weight are required."
    subject = form.get('subject') or form.get('current_filter')
    if not subject or subject == 'all': return None, "A valid subject is required."
    try:
        grade_str = form.get('grade')
        data = { "subject": subject, "category": form.get('category'), "study_time": float(form.get('study_time')), "assignment_name": form.get('assignment_name'), "grade": int(grade_str) if grade_str and grade_str.strip() else None, "weight": int(form.get('weight')) }
        return data, None
    except ValueError: return None, "Invalid data. Time, grade, and weight must be valid numbers."

@app.route('/')
@login_required
def display_table():
    filter_subject = request.args.get('subject')
    filter_category = request.args.get('category')
    
    unique_subjects = sorted(list(set(log['subject'] for log in study_data)))
    data_to_display = study_data
    
    if filter_subject and filter_subject != 'all':
        data_to_display = [log for log in study_data if log['subject'] == filter_subject]
        if filter_category and filter_category != 'all':
            data_to_display = [log for log in data_to_display if log['category'] == filter_category]

    summary_data = calculate_summary(filter_subject)
    
    subject_categories_map = {}
    for log in study_data:
        if log['subject'] not in subject_categories_map: subject_categories_map[log['subject']] = set()
        subject_categories_map[log['subject']].add(log['category'])
    for subject in subject_categories_map:
        subject_categories_map[subject] = sorted(list(subject_categories_map[subject]))
        
    chart_data = {s: sum(log['study_time'] for log in study_data if log['subject'] == s) for s in unique_subjects}
    chart_labels = list(chart_data.keys())
    chart_values = list(chart_data.values())
    
    return render_template(
        'index.html', 
        data=data_to_display, subjects=unique_subjects, selected_subject=filter_subject,
        selected_category=filter_category,
        summary_data=summary_data, chart_labels=json.dumps(chart_labels), chart_values=json.dumps(chart_values),
        # --- THIS IS THE FIX: Pass both the Python dict and the JSON string ---
        subject_categories_map_py=subject_categories_map,          # For Jinja2 template logic
        subject_categories_map_json=json.dumps(subject_categories_map) # For JavaScript
    )

@app.route('/add', methods=['POST'])
@login_required
def add_log():
    global next_id
    log_data, error = process_form_data(request.form)
    if error: return jsonify({'status': 'error', 'message': error}), 400
    log_data['id'] = next_id
    study_data.append(log_data)
    next_id += 1
    summary = calculate_summary(request.form.get('current_filter'))
    return jsonify({'status': 'success', 'message': 'Assignment added!', 'log': log_data, 'summary': summary})

@app.route('/update/<int:log_id>', methods=['POST'])
@login_required
def update_log(log_id):
    update_index = next((i for i, log in enumerate(study_data) if log['id'] == log_id), -1)
    if update_index == -1: return jsonify({'status': 'error', 'message': 'Assignment not found.'}), 404
    updated_data, error = process_form_data(request.form)
    if error: return jsonify({'status': 'error', 'message': error}), 400
    updated_data['id'] = log_id
    study_data[update_index] = updated_data
    summary = calculate_summary(request.form.get('current_filter'))
    return jsonify({'status': 'success', 'message': 'Assignment updated!', 'log': updated_data, 'summary': summary})

@app.route('/delete/<int:log_id>', methods=['POST'])
@login_required
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
            return redirect(url_for('display_table'))
        else:
            flash('Invalid username or password.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been successfully logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        confirm = request.form.get('confirm_password', '').strip()
        if not username or not password:
            flash("Username and password are required.", "error")
        elif username in users:
            flash("Username already exists.", "error")
        elif password != confirm:
            flash("Passwords do not match.", "error")
        else:
            users[username] = password
            flash("Account created successfully! Please log in.", "success")
            return redirect(url_for('login'))
    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)