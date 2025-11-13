from flask import Flask, render_template, request, url_for, jsonify, session, redirect, flash
import json
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a-very-secret-key'

# In-memory user and study data
users = { "alice": "1234", "bob": "password", "admin": "admin" }
study_data = [
    { "id": 1, "subject": "Mathematics", "category": "Homework", "study_time": 2.5, "assignment_name": "Homework 1", "grade": 85, "weight": 10.0 },
    { "id": 2, "subject": "History", "category": "Essays", "study_time": 1.5, "assignment_name": "Essay on Rome", "grade": 92, "weight": 15.0 },
    { "id": 3, "subject": "Science", "category": "Labs", "study_time": 3.0, "assignment_name": "Lab Report", "grade": 78, "weight": 20.0 },
    { "id": 4, "subject": "Mathematics", "category": "Quizzes", "study_time": 1.0, "assignment_name": "Quiz 1", "grade": 95, "weight": 5.0 },
    { "id": 5, "subject": "Science", "category": "Projects", "study_time": 2.5, "assignment_name": "Project Proposal", "grade": None, "weight": 15.0 },
    { "id": 6, "subject": "Mathematics", "category": "Homework", "study_time": 2.0, "assignment_name": "Homework 2", "grade": 88, "weight": 10.0 }
]
next_id = 7
weight_categories = {
    "Mathematics": [
        {"id": 1, "name": "Homework", "total_weight": 20, "default_name": "Homework #"},
        {"id": 2, "name": "Quizzes", "total_weight": 30, "default_name": "Quiz #"},
    ],
    "History": [
        {"id": 3, "name": "Essays", "total_weight": 15, "default_name": ""},
    ]
}
next_category_id = 4

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest': return jsonify({'status': 'error', 'message': 'Authentication required'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- NEW: Function to recalculate weights for a category ---
def recalculate_weights(subject, category_name):
    category_def = next((cat for cat in weight_categories.get(subject, []) if cat['name'] == category_name), None)
    if not category_def:
        return
    
    assignments_in_category = [log for log in study_data if log['subject'] == subject and log['category'] == category_name]
    num_assessments = len(assignments_in_category)
    
    if num_assessments > 0:
        new_weight = category_def['total_weight'] / num_assessments
        for log in assignments_in_category:
            log['weight'] = new_weight

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

@app.route('/')
@login_required
def display_table():
    filter_subject = request.args.get('subject')
    filter_category = request.args.get('category')
    subjects_from_data = {log['subject'] for log in study_data}
    subjects_from_categories = set(weight_categories.keys())
    unique_subjects = sorted(list(subjects_from_data | subjects_from_categories))
    data_to_display = study_data
    if filter_subject and filter_subject != 'all':
        data_to_display = [log for log in study_data if log['subject'] == filter_subject]
        if filter_category and filter_category != 'all':
            data_to_display = [log for log in data_to_display if log['category'] == filter_category]
    summary_data = calculate_summary(filter_subject)
    
    temp_weight_categories = json.loads(json.dumps(weight_categories))
    for subject, categories in temp_weight_categories.items():
        for category in categories:
            category['num_assessments'] = sum(1 for log in study_data if log['subject'] == subject and log['category'] == category['name'])

    subject_categories_map = {s: sorted([cat['name'] for cat in temp_weight_categories.get(s, [])]) for s in unique_subjects}
    chart_data = {s: sum(log['study_time'] for log in study_data if log['subject'] == s) for s in unique_subjects if s in [d['subject'] for d in study_data]}
    
    return render_template(
        'index.html', data=data_to_display, subjects=unique_subjects, selected_subject=filter_subject,
        selected_category=filter_category, summary_data=summary_data, 
        chart_labels=json.dumps(list(chart_data.keys())), chart_values=json.dumps(list(chart_data.values())),
        subject_categories_map_py=subject_categories_map,
        subject_categories_map_json=json.dumps(subject_categories_map),
        weight_categories_py=temp_weight_categories,
        weight_categories_json=json.dumps(weight_categories)
    )

def process_form_data(form):
    required_fields = ['category', 'assignment_name', 'study_time']
    if not all([form.get(key) for key in required_fields]): return None, "Category, Assignment, and Time are required."
    subject = form.get('subject') or form.get('current_filter')
    if not subject or subject == 'all': return None, "A valid subject is required."
    try:
        grade_str = form.get('grade')
        data = { "subject": subject, "category": form.get('category'), "study_time": float(form.get('study_time')), "assignment_name": form.get('assignment_name'), "grade": int(grade_str) if grade_str and grade_str.strip() else None, "weight": 0 }
        return data, None
    except (ValueError, TypeError): return None, "Invalid data. Time and grade must be valid numbers."

@app.route('/add', methods=['POST'])
@login_required
def add_log():
    global next_id
    log_data, error = process_form_data(request.form)
    if error: return jsonify({'status': 'error', 'message': error}), 400
    log_data['id'] = next_id
    study_data.append(log_data)
    next_id += 1
    recalculate_weights(log_data['subject'], log_data['category'])
    summary = calculate_summary(request.form.get('current_filter'))
    
    current_subject_filter = request.form.get('current_filter')
    assignments_to_return = [log for log in study_data if log['subject'] == current_subject_filter]

    return jsonify({'status': 'success', 'message': 'Assignment added!', 'log': log_data, 'summary': summary, 'updated_assignments': assignments_to_return})

@app.route('/update/<int:log_id>', methods=['POST'])
@login_required
def update_log(log_id):
    update_index = next((i for i, log in enumerate(study_data) if log['id'] == log_id), -1)
    if update_index == -1: return jsonify({'status': 'error', 'message': 'Assignment not found.'}), 404
    old_log = study_data[update_index]
    old_subject = old_log['subject']
    old_category = old_log['category']
    
    updated_data, error = process_form_data(request.form)
    if error: return jsonify({'status': 'error', 'message': error}), 400
    updated_data['id'] = log_id
    study_data[update_index] = updated_data
    
    if old_subject != updated_data['subject'] or old_category != updated_data['category']:
        recalculate_weights(old_subject, old_category)
    recalculate_weights(updated_data['subject'], updated_data['category'])
    
    current_subject_filter = request.form.get('current_filter')
    summary = calculate_summary(current_subject_filter)
    assignments_to_return = [log for log in study_data if log['subject'] == current_subject_filter]

    return jsonify({'status': 'success', 'message': 'Assignment updated!', 'log': updated_data, 'summary': summary, 'updated_assignments': assignments_to_return})

@app.route('/delete/<int:log_id>', methods=['POST'])
@login_required
def delete_log(log_id):
    current_filter = request.args.get('current_filter')
    log_to_delete = next((log for log in study_data if log['id'] == log_id), None)
    if log_to_delete:
        subject, category = log_to_delete['subject'], log_to_delete['category']
        study_data.remove(log_to_delete)
        recalculate_weights(subject, category)
        summary = calculate_summary(current_filter)
        assignments_to_return = [log for log in study_data if log['subject'] == current_filter]
        return jsonify({'status': 'success', 'message': 'Assignment deleted!', 'summary': summary, 'updated_assignments': assignments_to_return})
    return jsonify({'status': 'error', 'message': 'Assignment not found.'}), 404

@app.route('/category/add', methods=['POST'])
@login_required
def add_category():
    global next_category_id
    subject = request.form.get('subject')
    if not subject or subject == 'all': return jsonify({'status': 'error', 'message': 'A valid subject must be selected.'}), 400
    try:
        new_weight = int(request.form.get('total_weight'))
        current_total_weight = sum(cat['total_weight'] for cat in weight_categories.get(subject, []))
        if current_total_weight + new_weight > 100:
            return jsonify({'status': 'error', 'message': f'Adding {new_weight}% would exceed 100% for this subject.'}), 400
        
        new_category = { "id": next_category_id, "name": request.form.get('name'), "total_weight": new_weight, "default_name": request.form.get('default_name', '') }
        if not new_category['name'] or new_category['total_weight'] is None:
             return jsonify({'status': 'error', 'message': 'Category Name and Total Weight are required.'}), 400
        
        if subject not in weight_categories: weight_categories[subject] = []
        weight_categories[subject].append(new_category)
        next_category_id += 1
        return jsonify({'status': 'success', 'message': 'Category added!', 'category': new_category, 'subject': subject})
    except (ValueError, TypeError):
        return jsonify({'status': 'error', 'message': 'Invalid data. Weight must be a number.'}), 400

@app.route('/category/update/<int:cat_id>', methods=['POST'])
@login_required
def update_category(cat_id):
    subject = request.form.get('subject')
    if not subject or subject not in weight_categories: return jsonify({'status': 'error', 'message': 'Subject not found.'}), 404
    
    cat_index = next((i for i, cat in enumerate(weight_categories[subject]) if cat['id'] == cat_id), -1)
    if cat_index == -1: return jsonify({'status': 'error', 'message': 'Category not found.'}), 404

    try:
        new_weight = int(request.form.get('total_weight'))
        current_total_weight = sum(cat['total_weight'] for i, cat in enumerate(weight_categories[subject]) if i != cat_index)
        if current_total_weight + new_weight > 100:
            return jsonify({'status': 'error', 'message': f'Updating to {new_weight}% would exceed 100% for this subject.'}), 400

        updated_category = { "id": cat_id, "name": request.form.get('name'), "total_weight": new_weight, "default_name": request.form.get('default_name', '') }
        weight_categories[subject][cat_index] = updated_category
        return jsonify({'status': 'success', 'message': 'Category updated!', 'category': updated_category, 'subject': subject})
    except (ValueError, TypeError):
        return jsonify({'status': 'error', 'message': 'Invalid data. Weight must be a number.'}), 400

@app.route('/category/delete/<int:cat_id>', methods=['POST'])
@login_required
def delete_category(cat_id):
    subject = request.args.get('current_filter')
    if not subject or subject not in weight_categories: return jsonify({'status': 'error', 'message': 'Subject not found.'}), 404
    cat_to_delete = next((cat for cat in weight_categories[subject] if cat['id'] == cat_id), None)
    if cat_to_delete:
        weight_categories[subject].remove(cat_to_delete)
        return jsonify({'status': 'success', 'message': 'Category definition deleted!'})
    return jsonify({'status': 'error', 'message': 'Category not found.'}), 404

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session: return redirect(url_for('display_table'))
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
    if 'user' in session: return redirect(url_for('display_table'))
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