from flask import Flask, render_template, request, url_for, jsonify, session, redirect, flash
import json
import math
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

# --- Estimate k for exponential saturation model ---

def estimate_k(hours_list, grades_list, weights_list, max_grade=100):
    """
    Estimate learning efficiency from the relationship between study time and grades.
    Higher k = more efficient learner (gets better grades with less time)
    Lower k = needs more time to achieve grades
    
    New model: grade = max_grade * (1 - exp(-k * hours / (weight * 10)))
    Solve for k: k = -ln(1 - grade/max_grade) * (weight * 10) / hours
    """
    k_values = []
    
    for h, g, w in zip(hours_list, grades_list, weights_list):
        # Skip extreme cases
        if h <= 0 or g <= 0 or g >= (max_grade - 1):
            continue
            
        try:
            # Updated formula with weight in denominator and custom max_grade
            effective_difficulty = max(0.1, w * 10)
            k_i = -math.log(1 - g/max_grade) * effective_difficulty / h
            
            # Filter unrealistic k values
            if 0.01 < k_i < 100:
                k_values.append(k_i)
        except (ValueError, ZeroDivisionError):
            continue
    
    if not k_values:
        return 0.3  # Default moderate efficiency
    
    # Use median to reduce outlier impact
    k_values.sort()
    n = len(k_values)
    if n % 2 == 0:
        return (k_values[n//2 - 1] + k_values[n//2]) / 2
    else:
        return k_values[n//2]


def predict_grade(hours, weight, k, max_grade=100):
    """
    Predict grade based on study hours using exponential learning curve.
    
    Key insight: Grade depends on hours studied, but weight represents difficulty.
    - 0 hours = ~0% (even smart students fail without studying)
    - More hours = diminishing returns (exponential saturation)
    - Higher weight/difficulty = need more hours for same grade (weight divides)
    - max_grade sets the upper limit (100 by default, or custom if grade lock off)
    """
    if hours <= 0:
        return 0  # No study = no grade, regardless of past performance
    
    # Exponential learning curve with saturation at max_grade
    # Weight in denominator: harder assignments need more hours
    # Normalize weight to keep k values reasonable (multiply by 10)
    effective_difficulty = max(0.1, weight * 10)  # Prevent division issues
    predicted = max_grade * (1 - math.exp(-k * hours / effective_difficulty))
    
    return max(0, min(max_grade, predicted))


def required_hours(target_grade, weight, k, max_grade=100):
    """
    Calculate hours needed to reach target grade.
    Higher weight = more hours needed.
    """
    if target_grade <= 0:
        return 0
    
    # Allow up to 99.5% of max_grade before calling it impossible
    # (exponential model asymptotically approaches max_grade)
    if target_grade >= max_grade * 0.995:
        return float('inf')
    
    try:
        # Solve: target = max_grade * (1 - exp(-k * hours / (weight * 10)))
        # hours = -(weight * 10) * ln(1 - target/max_grade) / k
        effective_difficulty = max(0.1, weight * 10)
        hours = -effective_difficulty * math.log(1 - target_grade/max_grade) / k
        return max(0, hours)
    except (ValueError, ZeroDivisionError):
        return float('inf')


def calculate_confidence(data, hours_or_target, weight):
    """
    Calculate confidence score based on:
    - Number of data points
    - Similarity to past assignments
    """
    n = len(data)
    
    # Base confidence from data quantity
    base_conf = min(80, n * 15)
    
    # Bonus if we have similar examples
    past_hours = [log['study_time'] for log in data]
    avg_hours = sum(past_hours) / len(past_hours)
    
    # Reduce confidence if prediction is far from past experience
    if abs(hours_or_target - avg_hours) > avg_hours:
        base_conf *= 0.7
    
    return round(base_conf)


def find_similar_assignment(data, target_hours):
    """Find assignment with similar study time for reference"""
    if not data:
        return None
    
    # Find closest by study time
    closest = min(data, key=lambda x: abs(x['study_time'] - target_hours))
    
    # Only return if reasonably similar (within 50%)
    if abs(closest['study_time'] - target_hours) / max(target_hours, 0.1) < 0.5:
        return closest
    
    return None


def find_similar_grade(data, target_grade):
    """Find assignment with similar grade for reference"""
    if not data:
        return None
    
    # Find closest by grade
    closest = min(data, key=lambda x: abs(x['grade'] - target_grade))
    
    # Only return if reasonably similar (within 10 points)
    if abs(closest['grade'] - target_grade) < 10:
        return closest
    
    return None

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

@app.route('/predict', methods=['POST'])
@login_required
def predict():
    subject = request.form.get('subject')
    category = request.form.get('category')
    weight = float(request.form.get('weight', 0))
    hours = request.form.get('hours')
    target_grade = request.form.get('target_grade')
    grade_lock = request.form.get('grade_lock', 'true').lower() == 'true'
    max_grade = float(request.form.get('max_grade', 100)) if not grade_lock else 100
    
    # --- 1. Filter Data Sets ---
    graded_data = [log for log in study_data if log.get('grade') is not None]
    
    all_data = graded_data
    subject_data = [log for log in all_data if log['subject'] == subject]
    category_data = [log for log in subject_data if log['category'] == category]
    
    n_all = len(all_data)
    n_subject = len(subject_data)
    n_category = len(category_data)
    
    # Check for minimum data required
    if n_all < 2:
        return jsonify({
            'status': 'error',
            'message': 'Not enough historical data. Need at least 2 graded assignments total.'
        }), 400

    # --- 2. Estimate k for each scope ---
    def get_k_and_data(data):
        if len(data) < 2:
            return 0, [], [], []
        hours = [log['study_time'] for log in data]
        grades = [log['grade'] for log in data]
        weights = [log['weight'] / 100 for log in data]
        k_val = estimate_k(hours, grades, weights, max_grade)
        return k_val, hours, grades, weights

    k_all, _, _, _ = get_k_and_data(all_data)
    k_subject, _, _, _ = get_k_and_data(subject_data)
    k_category, past_hours, past_grades, past_weights = get_k_and_data(category_data)

    # --- 3. Determine Blended k using confidence-based weighting ---
    
    # Thresholds for 'full' confidence in a scope
    SUBJECT_THRESHOLD = 5
    CATEGORY_THRESHOLD = 5
    
    # Sigmoid-like weighting function (simplified for clear cut-off)
    # The weight increases linearly up to the threshold, then stays at 1.0
    
    # 3a. Category Weight (blends Category k with Subject k)
    # Weight goes from 0 (n_cat=0) to 1.0 (n_cat >= CATEGORY_THRESHOLD)
    category_weight = min(1.0, n_category / CATEGORY_THRESHOLD)
    
    if n_category >= 2:
        # Blend Category k with Subject k
        k_blended_subject = (category_weight * k_category) + ((1 - category_weight) * k_subject)
        data_source = f"{subject} - {category} (Blended with Subject)"
        filtered_data = category_data # Use most specific data for confidence/examples
    elif n_subject >= 2:
        k_blended_subject = k_subject
        data_source = f"{subject} (Pure Subject)"
        filtered_data = subject_data
    else:
        k_blended_subject = k_all
        data_source = f"All Subjects (Pure General)"
        filtered_data = all_data

    # 3b. Subject Weight (blends Subject/Category k with All k)
    # Weight goes from 0 (n_sub=0) to 1.0 (n_sub >= SUBJECT_THRESHOLD)
    subject_weight = min(1.0, n_subject / SUBJECT_THRESHOLD)
    
    if n_subject >= 2:
        # Final Blend: Blended-Subject-k with All-k
        k_final = (subject_weight * k_blended_subject) + ((1 - subject_weight) * k_all)
        data_source_detail = f"Subject Weight: {subject_weight:.0%}"
        if n_category >= 2:
             data_source_detail += f", Category Weight: {category_weight:.0%}"
    else:
        # Fallback: Only use All k
        k_final = k_all
        data_source_detail = "Only All Data (General)"
    
    k = k_final # The final blended k value
    
    # Re-extract data from the most specific scope with at least 2 points for examples and confidence
    if n_category >= 2:
        data_for_context = category_data
    elif n_subject >= 2:
        data_for_context = subject_data
    else:
        data_for_context = all_data

    # Extract data for prediction calculation (redundant check, k is final, but good practice)
    if not data_for_context:
        return jsonify({
            'status': 'error',
            'message': 'Internal error: Data context not found.'
        }), 500

    # Extract actual user data from the best available source
    past_hours = [log['study_time'] for log in data_for_context]
    past_grades = [log['grade'] for log in data_for_context]
    past_weights = [log['weight'] / 100 for log in data_for_context]
    
    # --- 4. Make Prediction (rest of the original logic) ---
    
    # Normalize weight input
    weight_decimal = weight / 100
        
    # Make prediction
    if hours and not target_grade:
        hours = float(hours)
        predicted_grade = predict_grade(hours, weight_decimal, k, max_grade)
        
        # Calculate confidence based on data points and similarity (using the best available data)
        base_confidence = calculate_confidence(data_for_context, hours, weight)
        adjusted_confidence = round(base_confidence) # Keep original confidence logic
        
        # Find similar assignments for context
        similar = find_similar_assignment(data_for_context, hours)
        
        # Show more precision for grades very close to max
        if predicted_grade >= max_grade - 1:
            grade_display = round(predicted_grade, 2)  # Show 2 decimals
        else:
            grade_display = round(predicted_grade, 1)  # Show 1 decimal
        
        response = {
            'mode': 'grade_from_hours',
            'predicted_grade': grade_display,
            'confidence': adjusted_confidence,
            'data_points': len(data_for_context),
            'data_source': data_source,
            'k_value': round(k, 3), # New: show k value
            'data_source_detail': data_source_detail, # New: show weighting
            'message': f'Based on {len(data_for_context)} assignments from {data_source}'
        }
        # ... (rest of the response generation logic for grade_from_hours)
        if predicted_grade >= max_grade - 0.5:
            response['note_about_grade'] = f"Grade is very close to maximum ({max_grade}% is theoretically unreachable)"
        
        if similar:
            response['similar_example'] = f"Previously: {similar['study_time']:.1f}h → {similar['grade']}%"
        
        return jsonify(response)
    
    elif target_grade and not hours:
        target_grade = float(target_grade)
        
        # Convert max grade to slightly less to avoid infinity
        if target_grade >= max_grade:
            target_grade = max_grade - 0.55
            adjusted_target_note = f"(adjusted from {max_grade}% to {target_grade:.2f}% for calculation)"
        else:
            adjusted_target_note = None
        
        if target_grade > max_grade:
            return jsonify({
                'status': 'error',
                'message': f'Target grade must be {max_grade}% or less'
            }), 400
        
        required = required_hours(target_grade, weight_decimal, k, max_grade)
        
        # Check if prediction is reasonable based on your past data
        max_past_hours = max(past_hours) if past_hours else 0
        avg_past_hours = sum(past_hours) / len(past_hours) if past_hours else 0
        
        if required == float('inf'):
            return jsonify({
                'status': 'error',
                'message': f'Target grade of {target_grade}% may be mathematically impossible to reach (requires infinite study time).'
            }), 400
        
        # Only warn if it's WAY beyond past experience (>3x your max)
        if required > max_past_hours * 3 and max_past_hours > 0:
            return jsonify({
                'status': 'error',
                'message': f'Target grade of {target_grade}% would require {required:.1f} hours, which is beyond your typical study pattern (your max was {max_past_hours:.1f}h). Consider a more achievable target or verify your inputs.'
            }), 400
        
        # Calculate confidence
        base_confidence = calculate_confidence(data_for_context, required, weight)
        adjusted_confidence = round(base_confidence)
        
        # Find similar grade for context
        similar = find_similar_grade(data_for_context, target_grade)
        
        response = {
            'mode': 'hours_from_grade',
            'required_hours': round(required, 1),
            'confidence': adjusted_confidence,
            'data_points': len(data_for_context),
            'data_source': data_source,
            'k_value': round(k, 3), # New: show k value
            'data_source_detail': data_source_detail, # New: show weighting
            'message': f'Based on {len(data_for_context)} assignments from {data_source}'
        }
        
        if adjusted_target_note:
            response['calculation_note'] = adjusted_target_note
        
        if similar:
            response['similar_example'] = f"Previously: {similar['study_time']:.1f}h → {similar['grade']}%"
        
        # Warning if significantly more than usual (but not an error)
        if required > avg_past_hours * 2 and avg_past_hours > 0:
            response['warning'] = f"This is significantly more than your average of {avg_past_hours:.1f}h. Make sure you have enough time!"
        
        return jsonify(response)
    
    else:
        return jsonify({
            'status': 'error',
            'message': 'Provide either hours or target grade, not both.'
        }), 400

if __name__ == '__main__':
    app.run(debug=True)