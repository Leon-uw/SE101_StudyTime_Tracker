from flask import Flask, render_template, request, url_for, jsonify, session, redirect, flash
import json
import math
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collections import Counter, defaultdict
from dotenv import load_dotenv
load_dotenv()

# Conditional database import - use local SQLite if USE_LOCAL_DB is set
if os.getenv("USE_LOCAL_DB", "").lower() == "true":
    print("🔧 Using LOCAL SQLite database for development")
    from db_local import _connect, SUBJECTS_TABLE, USERS_TABLE, init_db
    # SQLite doesn't need ensure_position_column (already in schema)
    ensure_position_column = lambda: None
else:
    print("🌐 Using REMOTE MySQL database")
    from db import _connect, SUBJECTS_TABLE, USERS_TABLE, init_db, ensure_position_column
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required

_schema_ready = False

# Add current directory to path for imports

# Import database functions
from crud import (get_all_grades, get_all_categories, get_categories_as_dict, add_grade, update_grade,
                  delete_grade, delete_grades_bulk, recalculate_and_update_weights, add_category,
                  update_category, delete_category, get_total_weight_for_subject,
                  get_all_subjects, add_subject as crud_add_subject, delete_subject as crud_delete_subject,
                  rename_subject as crud_rename_subject,
                  get_subject_by_name,
                  create_user, verify_user, user_exists, TABLE_NAME, ensure_schema)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a-very-secret-key'


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, user_id: int, username: str):
        self.id = str(user_id)
        self.username = username

# -------------------------------
# (4) user loader
# -------------------------------
@login_manager.user_loader
def load_user(user_id: str):
    conn = _connect()
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT id, username FROM {USERS_TABLE} WHERE id = %s", (int(user_id),))
        row = cur.fetchone()
        if not row:
            return None
        return User(user_id=row[0], username=row[1])
    finally:
        try:
            cur.close()
        except:
            pass
        try:
            conn.close()
        except:
            pass


# Database-only architecture - all data comes from database (no in-memory dicts)

def recalculate_weights(username, subject, category_name):
    """Recalculate weights for a category in the database."""
    try:
        recalculate_and_update_weights(username, subject, category_name)
    except Exception as e:
        print(f"Warning: Failed to recalculate weights in database: {e}")

def calculate_summary(username, subject, include_predictions=False):
    """Calculate summary statistics for a subject (now using database)."""
    if not subject or subject == 'all':
        return None
    
    study_data = get_all_grades(username)
    # Filter by subject
    subject_items = [log for log in study_data if log['subject'] == subject]
    
    # Filter predictions if not included
    if not include_predictions:
        subject_items = [log for log in subject_items if not log.get('is_prediction', False)]
        
    if not subject_items:
        return None
        
    graded_items = [log for log in subject_items if log.get('grade') is not None]
    
    total_hours = sum(log['study_time'] for log in subject_items)
    total_weight = sum(log['weight'] for log in graded_items)
    
    weighted_grade_sum = sum(log['grade'] * log['weight'] for log in graded_items)
    average_grade = weighted_grade_sum / total_weight if total_weight > 0 else 0
    
    return {
        'total_hours': total_hours,
        'average_grade': average_grade,
        'total_weight': total_weight
    }



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

@app.context_processor
def inject_subjects():
    if not current_user.is_authenticated:
        return dict(subjects=[])
    all_subjects = get_all_subjects(current_user.username)
    unique_subjects = sorted([s['name'] for s in all_subjects])
    return dict(subjects=unique_subjects)


@app.route('/')
@login_required
def display_table():
    """Main page - All Subjects view or filtered by subject."""
    subject_filter = request.args.get('subject', 'all')
    return render_subject_view(subject_filter)

@app.route('/subject/<subject_name>')
@login_required
def display_subject(subject_name):
    """Subject-specific view."""
    # Verify subject exists
    all_subjects = get_all_subjects(current_user.username)
    unique_subjects = [s['name'] for s in all_subjects]
    if subject_name not in unique_subjects:
         return redirect(url_for('display_table'))
    
    return render_subject_view(subject_name)

def render_subject_view(filter_subject):
    """Helper to render the main view with a specific subject filter."""
    filter_category = request.args.get('category')
    username = current_user.username

    # Fetch data from database
    study_data_db = get_all_grades(username)
    weight_categories_db = get_categories_as_dict(username)

    # Get subjects from subjects table (already injected, but needed for logic)
    all_subjects = get_all_subjects(username)
    unique_subjects = sorted([s['name'] for s in all_subjects])

    # Filter data for display
    data_to_display = study_data_db
    if filter_subject and filter_subject != 'all':
        data_to_display = [log for log in study_data_db if log['subject'] == filter_subject]
        if filter_category and filter_category != 'all':
            data_to_display = [log for log in data_to_display if log['category'] == filter_category]

    # Calculate summary
    summary_data = calculate_summary(username, filter_subject)

    # Add num_assessments to categories (count from database)
    temp_weight_categories = json.loads(json.dumps(weight_categories_db))
    for subject, categories in temp_weight_categories.items():
        for category in categories:
            category['num_assessments'] = sum(
                1 for log in study_data_db
                if log['subject'] == subject and log['category'] == category['name']
            )

    # Create subject-categories mapping
    subject_categories_map = {
        s: sorted([cat['name'] for cat in temp_weight_categories.get(s, [])])
        for s in unique_subjects
    }

    # Calculate chart data - only include subjects with actual study time
    chart_data = {}
    for s in unique_subjects:
        total_hours = sum(log['study_time'] for log in study_data_db if log['subject'] == s)
        if total_hours > 0:  # Only include subjects with study time
            chart_data[s] = total_hours
            
    page_title = "All Subjects" if filter_subject == 'all' else filter_subject

    return render_template(
        'index.html',
        data=data_to_display,
        # subjects=unique_subjects, # Injected via context processor
        selected_subject=filter_subject,
        selected_category=filter_category,
        summary_data=summary_data,
        chart_labels=json.dumps(list(chart_data.keys())),
        chart_values=json.dumps(list(chart_data.values())),
        subject_categories_map_py=subject_categories_map,
        subject_categories_map_json=json.dumps(subject_categories_map),
        weight_categories_py=temp_weight_categories,
        weight_categories_json=json.dumps(weight_categories_db),
        page_title=page_title,
        username=username
    )

@app.route('/about')
@login_required
def about():
    return render_template('about.html', page_title="About")

def calculate_stats(username):
    """Aggregate study data into high-level statistics for the Stats page."""
    study_data = get_all_grades(username)
    stats = {
        'has_data': bool(study_data),
        'has_actuals': False,
        'has_grades': False,
        'overall': {
            'gpa': None,
            'total_hours': 0,
            'grade_per_hour': None,
            'assignment_count': 0
        },
        'predictions': {
            'total': 0,
            'top_subject': None
        },
        'top_hours_subjects': [],
        'best_category': None,
        'focus_subject': None,
        'efficient_subjects': [],
        'prediction_accuracy': {
            'matched': 0,
            'mean_abs_error': None,
            'accuracy': None
        },
        'strong_scores': {
            'count': 0,
            'pct': None
        },
        'needs_work': {
            'count': 0,
            'pct': None
        },
        'hours_per_assignment': None,
        'graded_scores': []
    }

    if not study_data:
        return stats

    actual_entries = [row for row in study_data if not row.get('is_prediction')]
    prediction_entries = [row for row in study_data if row.get('is_prediction')]

    stats['overall']['assignment_count'] = len(actual_entries)
    stats['predictions']['total'] = len(prediction_entries)

    # Prediction habits
    prediction_counts = Counter(row['subject'] for row in prediction_entries if row.get('subject'))
    if prediction_counts:
        top_pred_subject, pred_count = prediction_counts.most_common(1)[0]
        stats['predictions']['top_subject'] = {
            'subject': top_pred_subject,
            'count': pred_count
        }

    if not actual_entries:
        return stats

    stats['has_actuals'] = True

    subject_hours = defaultdict(float)
    subject_weighted_sum = defaultdict(float)
    subject_weight_total = defaultdict(float)
    subject_grades = defaultdict(list)
    category_totals = defaultdict(lambda: {'weighted_sum': 0.0, 'weight_sum': 0.0, 'grades': []})

    overall_weighted_sum = 0.0
    overall_weight_total = 0.0
    overall_grades = []

    for entry in actual_entries:
        subject = entry.get('subject')
        if not subject:
            continue

        hours = float(entry.get('study_time') or 0)
        subject_hours[subject] += hours

        grade = entry.get('grade')
        if grade is None:
            continue

        grade = float(grade)
        weight = float(entry.get('weight') or 0)
        subject_grades[subject].append(grade)

        if weight > 0:
            weighted_grade = grade * weight
            subject_weighted_sum[subject] += weighted_grade
            subject_weight_total[subject] += weight
            overall_weighted_sum += weighted_grade
            overall_weight_total += weight

        overall_grades.append(grade)

        category = entry.get('category') or 'Uncategorized'
        category_stats = category_totals[(subject, category)]
        category_stats['grades'].append(grade)
        if weight > 0:
            category_stats['weighted_sum'] += grade * weight
            category_stats['weight_sum'] += weight

    total_hours = sum(subject_hours.values())
    stats['overall']['total_hours'] = total_hours

    # Strong/weak result rates
    graded_entries = [e for e in actual_entries if e.get('grade') is not None]
    if graded_entries:
        strong_count = sum(1 for e in graded_entries if float(e['grade']) >= 90)
        needs_work_count = sum(1 for e in graded_entries if float(e['grade']) < 70)
        total_graded = len(graded_entries)
        stats['strong_scores'] = {
            'count': strong_count,
            'pct': (strong_count / total_graded) * 100 if total_graded else None
        }
        stats['needs_work'] = {
            'count': needs_work_count,
            'pct': (needs_work_count / total_graded) * 100 if total_graded else None
        }
        stats['graded_scores'] = [float(e['grade']) for e in graded_entries]

    if stats['overall']['assignment_count'] > 0:
        stats['hours_per_assignment'] = total_hours / stats['overall']['assignment_count']

    if overall_weight_total > 0:
        overall_avg = overall_weighted_sum / overall_weight_total
    elif overall_grades:
        overall_avg = sum(overall_grades) / len(overall_grades)
    else:
        overall_avg = None

    stats['has_grades'] = overall_avg is not None
    stats['overall']['gpa'] = overall_avg
    if overall_avg is not None and total_hours > 0:
        stats['overall']['grade_per_hour'] = overall_avg / total_hours

    # Helper to calculate subject average
    def subject_average(subject):
        if subject_weight_total[subject] > 0:
            return subject_weighted_sum[subject] / subject_weight_total[subject]
        if subject_grades[subject]:
            return sum(subject_grades[subject]) / len(subject_grades[subject])
        return None

    subjects_seen = set(subject_hours.keys()) | set(subject_grades.keys())
    subject_averages = {subj: subject_average(subj) for subj in subjects_seen}

    # Top studied subjects
    stats['top_hours_subjects'] = [
        {
            'subject': subj,
            'hours': subject_hours[subj],
            'average_grade': subject_averages.get(subj)
        }
        for subj in sorted(subject_hours, key=subject_hours.get, reverse=True)
        if subject_hours[subj] > 0
    ][:3]

    # Best performing category across all subjects
    best_category = None
    for (subject, category), values in category_totals.items():
        if not values['grades']:
            continue
        if values['weight_sum'] > 0:
            avg_grade = values['weighted_sum'] / values['weight_sum']
        else:
            avg_grade = sum(values['grades']) / len(values['grades'])

        if best_category is None or avg_grade > best_category['average']:
            best_category = {
                'subject': subject,
                'category': category,
                'average': avg_grade,
                'samples': len(values['grades'])
            }
    stats['best_category'] = best_category

    # Subject that needs attention (lowest average grade)
    focus_candidate = None
    for subject, avg_grade in subject_averages.items():
        if avg_grade is None:
            continue
        candidate = {
            'subject': subject,
            'average': avg_grade,
            'hours': subject_hours.get(subject, 0),
            'assignments': len(subject_grades[subject])
        }
        if focus_candidate is None or avg_grade < focus_candidate['average']:
            focus_candidate = candidate
    stats['focus_subject'] = focus_candidate

    # Efficiency = average grade per study hour (normalized to avoid divide by zero)
    efficient_subjects = []
    for subject, avg_grade in subject_averages.items():
        hours = subject_hours.get(subject, 0)
        if avg_grade is None or hours <= 0:
            continue
        efficiency_score = avg_grade / max(hours, 1)
        efficient_subjects.append({
            'subject': subject,
            'efficiency': efficiency_score,
            'average_grade': avg_grade,
            'hours': hours
        })
    stats['efficient_subjects'] = sorted(efficient_subjects, key=lambda x: x['efficiency'], reverse=True)[:3]

    # Prediction accuracy: compare predictions to matching actuals by subject + assignment name
    actual_grade_map = defaultdict(list)
    for entry in graded_entries:
        subject = entry.get('subject')
        assignment = (entry.get('assignment_name') or '').strip().lower()
        if subject and assignment:
            actual_grade_map[(subject, assignment)].append(float(entry['grade']))

    errors = []
    for pred in prediction_entries:
        subject = pred.get('subject')
        assignment = (pred.get('assignment_name') or '').strip().lower()
        if not subject or not assignment:
            continue
        if pred.get('grade') is None:
            continue
        key = (subject, assignment)
        if key not in actual_grade_map:
            continue
        actual_avg = sum(actual_grade_map[key]) / len(actual_grade_map[key])
        error = abs(float(pred['grade']) - actual_avg)
        errors.append(error)

    if errors:
        mae = sum(errors) / len(errors)
        # Accuracy as "how close on average" capped between 0 and 100
        accuracy = max(0, min(100, 100 - mae))
        stats['prediction_accuracy'] = {
            'matched': len(errors),
            'mean_abs_error': mae,
            'accuracy': accuracy
        }

        # --- add raw rows so charts can filter by subject ---
    # All graded items as {subject, score}
    stats["all_grades"] = [
        {"subject": e.get("subject"), "score": float(e["grade"])}
        for e in actual_entries
        if e.get("grade") is not None
    ]

    # All study logs (actuals) as {subject, hours}
    stats["all_study_logs"] = [
        {"subject": e.get("subject"), "hours": float(e.get("study_time") or 0)}
        for e in actual_entries
    ]

    return stats

@app.route('/stats')
@login_required
def stats():                      # <-- was: def stats(username):
    # get the username from the logged-in user
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    username = current_user.username

    stats_data = calculate_stats(username)   # pass username into the function

    # sidebar subjects for this user
    conn = _connect(); cur = conn.cursor()
    try:
        cur.execute(f"SELECT name FROM {SUBJECTS_TABLE} WHERE username = %s ORDER BY name", (username,))
        subjects = [r[0] for r in cur.fetchall()]
    finally:
        try: cur.close()
        except: pass
        try: conn.close()
        except: pass

    return render_template('stats.html',
                           page_title="Statistics",
                           stats=stats_data,
                           subjects=subjects)

def process_form_data(form):
    print(f"DEBUG: process_form_data form={form}")
    is_prediction = form.get('is_prediction') == 'true'
    
    # Relax validation for predictions
    if not is_prediction:
        required_fields = ['category', 'assignment_name', 'study_time']
        if not all([form.get(key) for key in required_fields]): return None, "Category, Assignment, and Time are required."
    else:
        # For predictions, only category is required
        if not form.get('category'):
             return None, "Category is required for prediction."

    subject = form.get('subject') or form.get('current_filter')
    if not subject or subject == 'all': return None, "A valid subject is required."
    
    try:
        grade_str = form.get('grade')
        study_time_str = form.get('study_time')
        assignment_name = form.get('assignment_name', '').strip()

        # Parse study_time with better error handling
        try:
            study_time = float(study_time_str) if study_time_str and study_time_str.strip() else 0.0
        except (ValueError, TypeError) as e:
            return None, f"Invalid study time value: '{study_time_str}'"

        # Parse grade with better error handling
        try:
            grade = float(grade_str) if grade_str and grade_str.strip() else None
        except (ValueError, TypeError) as e:
            return None, f"Invalid grade value: '{grade_str}'"

        # For predictions, default to 'Prediction' if assignment_name is empty
        if is_prediction and not assignment_name:
            assignment_name = 'Prediction'

        # Parse weight from form data
        try:
            weight = float(form.get('weight', 0)) if form.get('weight') else 0.0
        except (ValueError, TypeError):
            weight = 0.0

        data = {
            "subject": subject,
            "category": form.get('category'),
            "study_time": study_time,
            "assignment_name": assignment_name,
            "grade": grade,
            "weight": weight,
            "is_prediction": is_prediction
        }
        return data, None
    except Exception as e:
        return None, f"Error processing form data: {str(e)}"

@app.route('/add', methods=['POST'])
@login_required
def add_log():
    print('\n=== ADD LOG DEBUG ===')
    print('Form data:', dict(request.form))
    log_data, error = process_form_data(request.form)
    print('Processed log_data:', log_data)
    if error:
        print('ERROR:', error)
        return jsonify({'status': 'error', 'message': error}), 400
    
    username = current_user.username

    # Write to database
    try:
        db_id = add_grade(
            username=username,
            subject=log_data['subject'],
            category=log_data['category'],
            study_time=log_data['study_time'],
            assignment_name=log_data['assignment_name'],
            grade=log_data['grade'],
            weight=log_data['weight'],  # Use the calculated weight from frontend
            is_prediction=log_data['is_prediction']
        )
        print(f'Saved to database with weight: {log_data["weight"]}')
        log_data['id'] = db_id  # Use database-generated ID
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to add assignment: {str(e)}'}), 500

    recalculate_weights(username, log_data['subject'], log_data['category'])
    print('Weights recalculated')

    summary = calculate_summary(username, request.form.get('current_filter'))

    # Fetch fresh data from database
    assignments_to_return = get_all_grades(username)
    print(f'Fetched {len(assignments_to_return)} assignments from database')
    print('First 3 assignments:', assignments_to_return[:3] if len(assignments_to_return) >= 3 else assignments_to_return)
    print('Last 3 assignments:', assignments_to_return[-3:] if len(assignments_to_return) >= 3 else assignments_to_return)

    current_subject_filter = request.form.get('current_filter')
    if current_subject_filter and current_subject_filter != 'all':
        assignments_to_return = [log for log in assignments_to_return if log['subject'] == current_subject_filter]
        print(f'Filtered to {len(assignments_to_return)} assignments for subject: {current_subject_filter}')

    # Find the newly added prediction and log its weight
    new_prediction = next((a for a in assignments_to_return if a['id'] == log_data['id']), None)
    if new_prediction:
        print(f'New prediction weight after recalculation: {new_prediction["weight"]}')

    message = 'Prediction added!' if log_data['is_prediction'] else 'Assignment added!'
    return jsonify({'status': 'success', 'message': message, 'log': log_data, 'summary': summary, 'updated_assignments': assignments_to_return})

@app.route('/update/<int:log_id>', methods=['POST'])
@login_required
def update_log(log_id):
    username = current_user.username
    # PHASE 5 FIX: Check database instead of in-memory dict
    all_assignments = get_all_grades(username)
    old_log = next((log for log in all_assignments if log['id'] == log_id), None)

    if not old_log:
        return jsonify({'status': 'error', 'message': 'Assignment not found.'}), 404

    old_subject = old_log['subject']
    old_category = old_log['category']

    updated_data, error = process_form_data(request.form)
    if error: return jsonify({'status': 'error', 'message': error}), 400
    updated_data['id'] = log_id

    # Update database
    try:
        rows_affected = update_grade(
            username=username,
            grade_id=log_id,
            subject=updated_data['subject'],
            category=updated_data['category'],
            study_time=updated_data['study_time'],
            assignment_name=updated_data['assignment_name'],
            grade=updated_data['grade'],
            weight=0,  # Weight will be recalculated
            is_prediction=updated_data['is_prediction']
        )
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to update assignment: {str(e)}'}), 500

    if old_subject != updated_data['subject'] or old_category != updated_data['category']:
        recalculate_weights(username, old_subject, old_category)
    recalculate_weights(username, updated_data['subject'], updated_data['category'])

    # Fetch fresh data from database instead of using in-memory dict
    assignments_to_return = get_all_grades(username)
    current_subject_filter = request.form.get('current_filter')
    summary = calculate_summary(username, current_subject_filter)
    if current_subject_filter and current_subject_filter != 'all':
        assignments_to_return = [log for log in assignments_to_return if log['subject'] == current_subject_filter]

    return jsonify({'status': 'success', 'message': 'Assignment updated!', 'log': updated_data, 'summary': summary, 'updated_assignments': assignments_to_return})

@app.route('/delete/<int:log_id>', methods=['POST'])
@login_required
def delete_log(log_id):
    current_filter = request.args.get('current_filter')
    username = current_user.username

    # PHASE 5 FIX: Check database instead of in-memory dict
    all_assignments = get_all_grades(username)
    log_to_delete = next((log for log in all_assignments if log['id'] == log_id), None)

    if not log_to_delete:
        return jsonify({'status': 'error', 'message': 'Assignment not found.'}), 404

    subject, category = log_to_delete['subject'], log_to_delete['category']
    is_prediction = log_to_delete.get('is_prediction', False)

    # Delete from database
    try:
        delete_grade(username, log_id)
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to delete assignment: {str(e)}'}), 500

    recalculate_weights(username, subject, category)
    summary = calculate_summary(username, current_filter)

    # Fetch fresh data from database
    assignments_to_return = get_all_grades(username)
    if current_filter and current_filter != 'all':
        assignments_to_return = [log for log in assignments_to_return if log['subject'] == current_filter]

    message = 'Prediction deleted!' if is_prediction else 'Assignment deleted!'
    return jsonify({'status': 'success', 'message': message, 'summary': summary, 'updated_assignments': assignments_to_return})

@app.route('/convert_prediction', methods=['POST'])
@login_required
def convert_prediction():
    """Convert a prediction to a regular assignment."""
    assignment_id = request.form.get('assignment_id')
    current_filter = request.form.get('current_filter')
    username = current_user.username
    
    if not assignment_id:
        return jsonify({'status': 'error', 'message': 'Assignment ID is required.'}), 400
    
    try:
        assignment_id = int(assignment_id)
    except ValueError:
        return jsonify({'status': 'error', 'message': 'Invalid assignment ID.'}), 400
    
    # Get the assignment from database
    all_assignments = get_all_grades(username)
    assignment = next((a for a in all_assignments if a['id'] == assignment_id), None)
    
    if not assignment:
        return jsonify({'status': 'error', 'message': 'Assignment not found.'}), 404
    
    if not assignment.get('is_prediction'):
        return jsonify({'status': 'error', 'message': 'This is not a prediction.'}), 400
    
    # Check if study time is provided
    if not assignment.get('study_time') or assignment['study_time'] <= 0:
        return jsonify({'status': 'error', 'message': 'Study time must be provided before converting.'}), 400
    
    # Convert to assignment by setting is_prediction to False and clearing the predicted grade
    try:
        update_grade(
            username=username,
            grade_id=assignment_id,
            subject=assignment['subject'],
            category=assignment['category'],
            study_time=assignment['study_time'],
            assignment_name=assignment['assignment_name'],
            grade=None,  # Clear the grade - it was predicted
            weight=assignment['weight'],
            is_prediction=False
        )
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to convert prediction: {str(e)}'}), 500
    
    # Fetch fresh data from database
    assignments_to_return = get_all_grades(username)
    summary = calculate_summary(username, current_filter)
    if current_filter and current_filter != 'all':
        assignments_to_return = [log for log in assignments_to_return if log['subject'] == current_filter]
    
    return jsonify({
        'status': 'success',
        'message': 'Prediction converted to assignment!',
        'summary': summary,
        'updated_assignments': assignments_to_return
    })

@app.route('/delete_multiple', methods=['POST'])
@login_required
def delete_multiple():
    """Delete multiple assignments at once."""
    current_filter = request.args.get('current_filter')
    ids_to_delete = request.json.get('ids', [])
    username = current_user.username

    if not ids_to_delete:
        return jsonify({'status': 'error', 'message': 'No assignments selected.'}), 400

    # Get assignments that will be deleted to track subjects/categories for weight recalc
    all_assignments = get_all_grades(username)
    assignments_to_delete = [a for a in all_assignments if a['id'] in ids_to_delete]
    subjects_to_recalc = set((a['subject'], a['category']) for a in assignments_to_delete)

    # Delete from database (bulk operation)
    try:
        deleted_count = delete_grades_bulk(username, ids_to_delete)
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to delete assignments: {str(e)}'}), 500

    # Fetch fresh data from database instead of using in-memory dict
    assignments_to_return = get_all_grades(username)
    # Recalculate weights for affected subjects/categories
    for subject, category in subjects_to_recalc:
        recalculate_weights(username, subject, category)

    # Calculate summary
    summary = calculate_summary(username, current_filter)

    # Fetch updated assignments from database
    assignments_to_return = get_all_grades(username)
    if current_filter and current_filter != 'all':
        assignments_to_return = [log for log in assignments_to_return if log['subject'] == current_filter]

    return jsonify({
        'status': 'success',
        'message': f'{deleted_count} assignment(s) deleted!',
        'summary': summary,
        'updated_assignments': assignments_to_return
    })

@app.route('/category/add', methods=['POST'])
@login_required
def add_category_route():
    subject = request.form.get('subject')
    username = current_user.username
    if not subject or subject == 'all':
        return jsonify({'status': 'error', 'message': 'A valid subject must be selected.'}), 400

    try:
        category_name = request.form.get('name')
        new_weight = int(request.form.get('total_weight'))
        default_name = request.form.get('default_name', '')

        if not category_name or new_weight is None:
            return jsonify({'status': 'error', 'message': 'Category Name and Total Weight are required.'}), 400

        # Check total weight from database
        current_total_weight = get_total_weight_for_subject(username, subject)
        if current_total_weight + new_weight > 100:
            return jsonify({'status': 'error', 'message': f'Adding {new_weight}% would exceed 100% for this subject.'}), 400

        # Add to database
        new_id = add_category(username, subject, category_name, new_weight, default_name)
        new_category = {"id": new_id, "name": category_name, "total_weight": new_weight, "default_name": default_name}

        return jsonify({'status': 'success', 'message': 'Category added!', 'category': new_category, 'subject': subject})
    except (ValueError, TypeError):
        return jsonify({'status': 'error', 'message': 'Invalid data. Weight must be a number.'}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to add category: {str(e)}'}), 500

@app.route('/category/update/<int:cat_id>', methods=['POST'])
@login_required
def update_category_route(cat_id):
    subject = request.form.get('subject')
    username = current_user.username
    if not subject:
        return jsonify({'status': 'error', 'message': 'Subject not found.'}), 404

    try:
        category_name = request.form.get('name')
        new_weight = int(request.form.get('total_weight'))
        default_name = request.form.get('default_name', '')

        if not category_name or new_weight is None:
            return jsonify({'status': 'error', 'message': 'Category Name and Total Weight are required.'}), 400

        # Check total weight from database (excluding current category)
        current_total_weight = get_total_weight_for_subject(username, subject, exclude_category_id=cat_id)
        if current_total_weight + new_weight > 100:
            return jsonify({'status': 'error', 'message': f'Updating to {new_weight}% would exceed 100% for this subject.'}), 400

        # Update in database
        rows_affected = update_category(username, cat_id, subject, category_name, new_weight, default_name)

        if rows_affected == 0:
            return jsonify({'status': 'error', 'message': 'Category not found.'}), 404

        updated_category = {"id": cat_id, "name": category_name, "total_weight": new_weight, "default_name": default_name}
        return jsonify({'status': 'success', 'message': 'Category updated!', 'category': updated_category, 'subject': subject})
    except (ValueError, TypeError):
        return jsonify({'status': 'error', 'message': 'Invalid data. Weight must be a number.'}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to update category: {str(e)}'}), 500

@app.route('/category/delete/<int:cat_id>', methods=['POST'])
@login_required
def delete_category_route(cat_id):
    username = current_user.username
    try:
        # Delete from database
        rows_affected = delete_category(username, cat_id)

        if rows_affected == 0:
            return jsonify({'status': 'error', 'message': 'Category not found.'}), 404

        return jsonify({'status': 'success', 'message': 'Category definition deleted!'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to delete category: {str(e)}'}), 500

@app.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('display_table'))

    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = (request.form.get('password') or '').strip()

        if verify_user(username, password):
            conn = _connect(); cur = conn.cursor()
            try:
                cur.execute(f"SELECT id, username FROM {USERS_TABLE} WHERE username=%s", (username,))
                row = cur.fetchone()
                if not row:
                    flash('Account problem. Please contact support.', 'error')
                    return render_template('login.html')
                user = User(user_id=row[0], username=row[1])
                login_user(user, remember=True)
                flash(f"Hello, {username}!", "greeting")
            finally:
                cur.close(); conn.close()

            nxt = request.args.get('next')
            return redirect(nxt or url_for('display_table'))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('login.html')



@app.route('/logout')
def logout():
    logout_user()
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
        elif user_exists(username):
            flash("Username already exists.", "error")
        elif password != confirm:
            flash("Passwords do not match.", "error")
        else:
            try:
                create_user(username, password)
                flash("Account created successfully! Please log in.", "success")
                return redirect(url_for('login'))
            except Exception as e:
                flash(f"Registration failed: {str(e)}", "error")
                
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
    
    # Validate negative inputs
    if (hours and float(hours) < 0) or (target_grade and float(target_grade) < 0):
        return jsonify({
            'status': 'error',
            'message': 'Values cannot be negative.'
        }), 400

    # --- 1. Filter Data Sets ---
    # Fetch from database
    username = current_user.username
    all_grades = get_all_grades(username)
    graded_data = [log for log in all_grades if log.get('grade') is not None]

    all_data = graded_data
    subject_data = [log for log in all_data if log['subject'] == subject]
    category_data = [log for log in subject_data if log['category'] == category]
    
    n_all = len(all_data)
    n_subject = len(subject_data)
    n_category = len(category_data)
    
    # Check for minimum data required
    # if n_all < 2:
    #     return jsonify({
    #         'status': 'error',
    #         'message': 'Not enough historical data. Need at least 2 graded assignments total.'
    #     }), 400

    # --- 2. Estimate k for each scope ---
    def get_k_and_data(data):
        if len(data) < 1:
            return 0.3, [], [], []
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

@app.route('/add_subject', methods=['POST'])
@login_required
def add_subject():
    subject_name = request.form.get('subject_name', '').strip()
    username = current_user.username

    if not subject_name:
        return jsonify({'status': 'error', 'message': 'Subject name cannot be empty.'}), 400

    # Check if subject already exists
    existing_subject = get_subject_by_name(username, subject_name)
    if existing_subject:
        return jsonify({'status': 'error', 'message': 'Subject already exists.'}), 400

    # Add subject to database
    try:
        subject_id = crud_add_subject(username, subject_name)
        return jsonify({'status': 'success', 'subject': subject_name, 'id': subject_id})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to add subject: {str(e)}'}), 500

@app.route('/delete_subject', methods=['POST'])
@login_required
def delete_subject():
    subject_name = request.form.get('subject_name', '').strip()
    username = current_user.username

    if not subject_name:
        return jsonify({'status': 'error', 'message': 'Subject name cannot be empty.'}), 400

    # Get subject by name, then delete by ID (cascade deletes assignments/categories)
    try:
        subject = get_subject_by_name(username, subject_name)
        if not subject:
            return jsonify({'status': 'error', 'message': f'Subject "{subject_name}" not found.'}), 404

        rows_deleted = crud_delete_subject(username, subject['id'])
        if rows_deleted > 0:
            return jsonify({'status': 'success', 'message': f'Subject "{subject_name}" deleted successfully.'})
        else:
            return jsonify({'status': 'error', 'message': f'Failed to delete subject "{subject_name}".'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to delete subject: {str(e)}'}), 500

@app.route('/rename_subject', methods=['POST'])
@login_required
def rename_subject_route():
    old_name = request.form.get('old_name')
    new_name = request.form.get('new_name')
    username = current_user.username

    if not old_name or not new_name:
        return jsonify({'status': 'error', 'message': 'Both old and new subject names are required.'}), 400

    new_name = new_name.strip()
    if not new_name:
        return jsonify({'status': 'error', 'message': 'New subject name cannot be empty.'}), 400

    try:
        crud_rename_subject(username, old_name, new_name)
        return jsonify({'status': 'success', 'message': f'Subject renamed to {new_name}', 'new_name': new_name})
    except ValueError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Database error: {str(e)}'}), 500

@app.route('/predict_subject', methods=['POST'])
@login_required
def predict_subject():
    """
    Predict overall grade or required study time for an entire subject.
    """
    subject = request.form.get('subject')
    target_grade_str = request.form.get('target_grade')
    study_time_str = request.form.get('study_time')
    username = current_user.username
    
    if not subject:
        return jsonify({'status': 'error', 'message': 'Subject is required.'}), 400

    use_predictions = request.form.get('use_predictions') == 'true'

    # Use existing summary calculation for efficiency and consistency
    summary = calculate_summary(username, subject, include_predictions=use_predictions)
    if not summary:
         return jsonify({'status': 'error', 'message': 'Subject data not found.'}), 404

    current_grade = summary['average_grade']
    current_weight = summary['total_weight']
    remaining_weight = 100 - current_weight
    
    # If course is complete (or near complete), we can't really predict much
    if remaining_weight <= 0.01:
         return jsonify({
            'status': 'success',
            'message': 'Course is 100% complete.',
            'current_grade': round(current_grade, 2),
            'remaining_weight': 0,
            'prediction': None
        })

    # Fetch data for k estimation
    all_grades = get_all_grades(username)
    subject_data = [log for log in all_grades if log['subject'] == subject]
    
    # IMPORTANT: For k estimation, we ONLY want actual past performance, NOT predictions
    # So we explicitly filter out predictions even if use_predictions is True for the summary
    graded_items = [log for log in subject_data if log.get('grade') is not None and not log.get('is_prediction')]

    # Estimate k for the subject
    def get_k(data):
        if len(data) < 2: return 0.3 # Default
        hours = [log['study_time'] for log in data]
        grades = [log['grade'] for log in data]
        weights = [log['weight'] / 100 for log in data]
        return estimate_k(hours, grades, weights)

    if len(graded_items) >= 2:
        k = get_k(graded_items)
    else:
        # Fallback to all data (excluding predictions)
        all_graded = [log for log in all_grades if log.get('grade') is not None and not log.get('is_prediction')]
        k = get_k(all_graded)

    response_data = {
        'status': 'success',
        'current_grade': round(current_grade, 2),
        'remaining_weight': round(remaining_weight, 2),
        'k_estimated': k
    }

    # CASE 1: Target Grade -> Required Time
    if target_grade_str and target_grade_str.strip():
        try:
            target_overall = float(target_grade_str)
            if target_overall < 0:
                return jsonify({'status': 'error', 'message': 'Target grade cannot be negative.'}), 400
            
            # Calculate what average is needed on the remaining weight
            # target_overall = (current_grade * current_weight + future_avg * remaining_weight) / 100
            # future_avg * remaining_weight = target_overall * 100 - current_grade * current_weight
            
            weighted_grade_sum = current_grade * current_weight
            required_future_avg = (target_overall * 100 - weighted_grade_sum) / remaining_weight
            
            response_data['average_grade_needed'] = round(required_future_avg, 2)
            
            if required_future_avg < 0:
                 response_data['message'] = "You're already above this target!"
                 response_data['predicted_additional_time'] = 0
            elif required_future_avg > 100: 
                 response_data['message'] = "Target unreachable (requires > 100% on remaining work)."
                 response_data['predicted_additional_time'] = None
            else:
                # Calculate time needed for this average on the remaining weight
                hours_needed = required_hours(required_future_avg, remaining_weight/100, k)
                
                if hours_needed == float('inf'):
                    response_data['message'] = "Target unreachable with current learning efficiency."
                    response_data['predicted_additional_time'] = None
                else:
                    response_data['predicted_additional_time'] = round(hours_needed, 1)
                    
        except ValueError:
            return jsonify({'status': 'error', 'message': 'Invalid target grade.'}), 400

    # CASE 2: Study Time -> Predicted Overall Grade
    elif study_time_str and study_time_str.strip():
        try:
            future_hours = float(study_time_str)
            if future_hours < 0:
                return jsonify({'status': 'error', 'message': 'Study time cannot be negative.'}), 400
            
            # Predict grade for the remaining weight based on time
            predicted_future_avg = predict_grade(future_hours, remaining_weight/100, k)
            
            # Calculate overall grade
            weighted_grade_sum = current_grade * current_weight
            predicted_overall = (weighted_grade_sum + predicted_future_avg * remaining_weight) / 100
            
            response_data['predicted_overall_grade'] = round(predicted_overall, 2)
            response_data['average_grade_needed'] = round(predicted_future_avg, 2)
            
        except ValueError:
             return jsonify({'status': 'error', 'message': 'Invalid study time.'}), 400
             
    else:
        # Just return status info if no inputs
        pass

    return jsonify(response_data)

@app.post("/api/assignments/reorder")
@login_required
def reorder_assignments():
    """
    Body: { "order": [<id1>, <id2>, ...] }  // top-to-bottom row order
    Updates Position=0..n-1 for *this user's* assignments.
    """
    data = request.get_json(silent=True) or {}
    ids = data.get("order") or []
    if not isinstance(ids, list) or not ids:
        return jsonify({"status": "ok", "updated": 0}), 200

    # sanitize -> ints only
    try:
        ids = [int(x) for x in ids]
    except Exception:
        return jsonify({"status": "error", "message": "invalid ids"}), 400

    username = current_user.username

    conn = _connect()
    cur = conn.cursor()
    try:
        # ---------- (1) Optional ownership check ----------
        # IMPORTANT: build explicit placeholders for IN (...)
        in_placeholders = ",".join(["%s"] * len(ids))
        q = f"""
            SELECT id
            FROM {TABLE_NAME}
            WHERE username=%s AND id IN ({in_placeholders})
        """
        cur.execute(q, (username, *ids))
        owned = {row[0] for row in cur.fetchall()}
        if len(owned) != len(set(ids)):
            return jsonify({"status": "error",
                            "message": "contains ids not owned by user"}), 400

        # ---------- (2) Build CASE fragment ----------
        # CASE id WHEN <id> THEN <pos> ...
        case_frag = " ".join(["WHEN %s THEN %s"] * len(ids))
        params = []
        for pos, _id in enumerate(ids):
            params.extend([_id, pos])   # id, position

        # ---------- (3) UPDATE with IN (...) placeholders ----------
        sql = f"""
            UPDATE {TABLE_NAME}
            SET Position = CASE id {case_frag} END
            WHERE username=%s AND id IN ({in_placeholders})
        """
        params.extend([username, *ids])

        cur.execute(sql, params)
        conn.commit()
        return jsonify({"status": "ok", "updated": cur.rowcount}), 200

    except Exception as e:
        conn.rollback()
        # log for server console; keeps response terse
        print("Reorder error:", e)
        return jsonify({"status": "error", "message": "server error"}), 500
    finally:
        cur.close()
        conn.close()






# --- Bootstrap DB once (Flask 3.x compatible) ---
_bootstrapped = False

@app.before_request
def _bootstrap_db_once():
    global _bootstrapped
    if _bootstrapped:
        return
    try:
        init_db()                 # creates DB/tables if missing
        ensure_position_column()  # adds Position + index, backfills
    except Exception as e:
        app.logger.exception("DB bootstrap failed: %s", e)
    _bootstrapped = True

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
