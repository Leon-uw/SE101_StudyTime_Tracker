from flask import Flask, render_template, request, redirect, url_for, flash
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a-very-secret-key'

# In-memory "database"
study_data = [
    { "id": 1, "subject": "Mathematics", "study_time": 2.5, "assignment_name": "Homework 1", "grade": 85, "weight": 10 },
    { "id": 2, "subject": "History", "study_time": 1.5, "assignment_name": "Essay", "grade": 92, "weight": 15 },
    { "id": 3, "subject": "Science", "study_time": 3.0, "assignment_name": "Lab Report", "grade": 78, "weight": 20 },
    { "id": 4, "subject": "Mathematics", "study_time": 1.0, "assignment_name": "Quiz 2", "grade": 95, "weight": 5 },
    { "id": 5, "subject": "History", "study_time": 2.0, "assignment_name": "Reading", "grade": 88, "weight": 10 }
]
next_id = 6

@app.route('/')
def display_table():
    filter_subject = request.args.get('subject')
    unique_subjects = sorted(list(set(log['subject'] for log in study_data)))
    
    data_to_display = study_data
    summary_data = None

    if filter_subject and filter_subject != 'all':
        data_to_display = [log for log in study_data if log['subject'] == filter_subject]
        if data_to_display:
            total_hours = sum(log['study_time'] for log in data_to_display)
            total_weight = sum(log['weight'] for log in data_to_display)
            weighted_grade_sum = sum(log['grade'] * log['weight'] for log in data_to_display)
            average_grade = weighted_grade_sum / total_weight if total_weight > 0 else 0
            summary_data = {'total_hours': total_hours, 'average_grade': average_grade, 'total_weight': total_weight}

    # --- NEW: Calculate data for the Pie Chart ---
    # This happens on the complete dataset, regardless of the filter.
    chart_data = {}
    for log in study_data:
        subject = log['subject']
        time = log['study_time']
        chart_data[subject] = chart_data.get(subject, 0) + time
    
    # Prepare data in a format Chart.js can use
    chart_labels = list(chart_data.keys())
    chart_values = list(chart_data.values())

    return render_template(
        'index.html', 
        data=data_to_display, 
        subjects=unique_subjects, 
        selected_subject=filter_subject,
        summary_data=summary_data,
        chart_labels=json.dumps(chart_labels),  # Use json.dumps for safety
        chart_values=json.dumps(chart_values)
    )

# The /add and /update routes do not need any changes
@app.route('/add', methods=['POST'])
def add_log():
    global next_id
    if not all([request.form.get(key) for key in ['subject', 'assignment_name', 'study_time', 'grade', 'weight']]):
        flash("Error: All fields are required.", "error")
    else:
        try:
            new_log = {
                "id": next_id, "subject": request.form.get('subject'), "study_time": float(request.form.get('study_time')),
                "assignment_name": request.form.get('assignment_name'), "grade": int(request.form.get('grade')),
                "weight": int(request.form.get('weight'))
            }
            study_data.append(new_log)
            next_id += 1
            flash("New assignment added successfully!", "success")
        except ValueError:
            flash("Error: Invalid data. Time, grade, and weight must be valid numbers.", "error")
    return redirect(url_for('display_table'))

@app.route('/update/<int:log_id>', methods=['POST'])
def update_log():
    log_to_update = next((log for log in study_data if log['id'] == log_id), None)
    if not log_to_update:
        flash("Error: Could not find assignment.", "error")
    elif not all([request.form.get(key) for key in ['subject', 'assignment_name', 'study_time', 'grade', 'weight']]):
        flash("Error: All fields are required.", "error")
    else:
        try:
            log_to_update['subject'] = request.form.get('subject')
            log_to_update['study_time'] = float(request.form.get('study_time'))
            log_to_update['assignment_name'] = request.form.get('assignment_name')
            log_to_update['grade'] = int(request.form.get('grade'))
            log_to_update['weight'] = int(request.form.get('weight'))
            flash("Assignment updated successfully!", "success")
        except ValueError:
            flash("Error: Invalid data. Time, grade, and weight must be valid numbers.", "error")
    return redirect(url_for('display_table'))

if __name__ == '__main__':
    app.run(debug=True)