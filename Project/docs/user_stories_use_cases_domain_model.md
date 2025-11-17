# User Stories

## Epic A — Account & Profile Management

### US-A1 – Register an account
As a student, I want to create an account with a secure login so that my courses, grades, and study hours are stored privately and persist across devices.

Acceptance criteria:
- From the registration page, entering a valid email, password, and confirming the password creates an account and redirects me to the main dashboard or course setup page.
- If an email is already in use, I see a clear error and my input is preserved.
- Passwords are stored hashed and are never shown in plain text after submission.
- Form validation clearly highlights missing or invalid fields.

### US-A2 – Log in and log out
As a student, I want to log in and log out so that only I can access my study data.

Acceptance criteria:
- From the login page, entering correct credentials starts a user session and shows my dashboard.
- Entering incorrect credentials shows a clear error and does not reveal whether the email or password is wrong.
- Logging out invalidates the session and redirects me to the login page.
- After logout, visiting a protected route redirects to the login page.

### US-A3 – Manage basic profile settings
As a student, I want to view and update basic profile settings such as my display name so that the app reflects my preferences.

Acceptance criteria:
- I can change my display name from a profile or settings page.
- Updates are persisted and applied to subsequent sessions.

---

## Epic B — Course & Assessment Setup

### US-B1 – Add a course
As a student, I want to add courses I am taking so that the system can track study time and grades per course.

Acceptance criteria:
- I can create a course with at least a course code and course title.
- The course appears in my course list and is selectable when entering grades or study hours.
- If I try to create a clearly duplicate course, I either get an error or the system prevents duplicates in a reasonable way.

### US-B2 – Edit or delete a course
As a student, I want to edit or delete an existing course so that I can correct mistakes or remove courses I no longer take.

Acceptance criteria:
- I can edit course code and title.
- If I delete a course, I am warned that all associated study hour entries and assessments will be removed or otherwise handled consistently.
- After deletion, the course and its data no longer appear in dashboards or recommendations.

### US-B3 – Set target grade and target study hours per course
As a student, I want to set a target final grade and optionally a target weekly study time per course so that recommendations can be tailored to my goals.

Acceptance criteria:
- For a chosen course, I can input and edit a target grade.
- I can optionally set a target weekly number of study hours for that course.
- Recommendations clearly indicate whether I am currently on track compared to my target.
- Target values are stored and used in the recommendation algorithm.

### US-B4 – Configure assessment structure and weights
As a student, I want to define assessments and their weights, such as midterm 25 percent and final 40 percent, so that the system can compute my weighted grade and the impact of upcoming assessments.

Acceptance criteria:
- I can create multiple assessments for a course with a name, category, and weight percentage.
- The system warns me if the total weight for a course deviates significantly from 100 percent.
- I can edit assessment details and delete assessments.
- Assessments appear in the grade entry view and are used to calculate course grades.

### US-B5 – Enter and update grades
As a student, I want to enter and update my grades for completed assessments so that the system can calculate my current standing per course.

Acceptance criteria:
- I can record a numeric grade for each assessment, using either percentage or score and maximum score.
- The course’s current grade is automatically computed using the defined weights.
- If I update a grade, the course grade and related recommendations update accordingly.

---

## Epic C — Study Time Input and Management

### US-C1 – Input study hours per course
As a student, I want to input how many hours I studied for a course on a given date so that the system can track my study time and compare it to recommendations.

Acceptance criteria:
- I can select a course, choose a date, and enter the number of hours studied.
- The entry is saved and immediately reflected in weekly totals and the dashboard.
- The system prevents obviously invalid values such as negative hours.

### US-C2 – View and edit study hours
As a student, I want to view, edit, and delete my previously entered study hours so that I can fix mistakes and keep the data accurate.

Acceptance criteria:
- I can list entries of study hours filtered by course and date range.
- For each entry, I can edit the date and number of hours studied.
- Deleting an entry removes it from aggregates such as weekly totals and charts.

---

## Epic D — Recommendations and Analytics

### US-D1 – See recommended weekly study hours per course
As a student, I want to see recommended weekly study hours for each course so that I know how to allocate my time.

Acceptance criteria:
- The dashboard shows a list of courses with recommended hours for the current week, hours already entered for this week, and the gap between recommended and actual hours.
- If I change my target grade, target weekly hours, or log new hours, recommendations update when I reload or refresh the relevant view.
- If a course has no data yet, the recommendation falls back to a reasonable baseline.

### US-D2 – Visualize weekly totals and trends
As a student, I want to see charts of study hours over time so I can understand my habits and trends.

Acceptance criteria:
- The dashboard includes at least one chart for weekly total hours and a chart that shows hours per course for the current week or a selected week.
- Courses can be visually distinguished in the charts.
- Charts update when study hours are added, edited, or deleted.

### US-D3 – See current grade versus target and projected outcome
As a student, I want to see my current grade and how it compares to my target, along with a simple projection, so I know if I need to adjust my effort.

Acceptance criteria:
- For each course, the system displays the current weighted grade and the target grade.
- The system shows a simple indicator such as “On track,” “At risk,” or “Behind” based on the gap between current and target.
- The assumptions behind the projection, such as how it treats remaining assessments, are documented in the user manual or a help section.

### US-D4 – Weekly summary overview
As a student, I want a weekly summary dashboard that highlights total hours, per-course hours, and recommendation gaps so I can get a quick snapshot of my situation.

Acceptance criteria:
- The weekly summary includes total hours studied this week and a breakdown of hours per course.
- For each course, the summary shows recommended hours, actual hours, and the gap.
- The summary lists courses that are significantly under the recommended hours.

---

# Use Cases

## UC1 – Register an Account

Actor: Student  
Goal: Create a new account on the platform.

Preconditions:
- The user is not logged in.
- The registration page is accessible.

Trigger:
- The user selects the sign-up option on the login or landing page.

Main Success Scenario:
1. The system displays a registration form requesting email, password, confirmed password, and optional display name.
2. The user enters the required information and submits the form.
3. The system validates the form data.
4. The system stores the new user record with a hashed password.
5. The system starts a session for the user and redirects to the initial dashboard or course setup screen.

Alternate Flows:
- Invalid input:
  - If required fields are missing or invalid, the system shows clear validation errors and preserves user input.
- Duplicate email:
  - If the email already exists, the system displays an error and offers a link to the login page.

---

## UC2 – Login and Logout

Actor: Student  
Goal: Access and later exit a personal dashboard.

Preconditions:
- The user has a registered account.

Triggers:
- Login: The user navigates to the login page.
- Logout: The user selects the logout option from the navigation bar or menu.

Main Success Scenario (Login):
1. The system displays a login form requesting email and password.
2. The user enters credentials and submits the form.
3. The system verifies the credentials against stored records.
4. If valid, the system creates an authenticated session and redirects to the dashboard.

Alternate Flow (Invalid credentials):
- If the credentials are invalid, the system shows an error message and does not create a session. The user can retry.

Main Success Scenario (Logout):
1. The user selects the logout option.
2. The system invalidates the session.
3. The system redirects the user to the login page.

---

## UC3 – Add and Configure a Course

Actor: Student  
Goal: Define a course so that study hours and grades can be associated with it.

Preconditions:
- The user is logged in.

Trigger:
- The user selects an option such as “Add Course” from the dashboard or course list page.

Main Success Scenario:
1. The system displays a course creation form with fields for course code, course title, optional credit weight, and optional instructor name.
2. The user fills in the details and submits the form.
3. The system validates required fields such as course code and title.
4. The system creates a course record linked to the user.
5. The course appears in the course list and is available for assessment and study hour input.

Alternate Flows:
- Missing required fields:
  - The system shows validation errors and allows the user to correct and resubmit.
- Clearly duplicate course:
  - The system warns the user or prevents the creation of an obvious duplicate entry.

---

## UC4 – Configure Assessments and Weights for a Course

Actor: Student  
Goal: Define assessments and weights for a selected course.

Preconditions:
- The user is logged in.
- At least one course exists.

Trigger:
- The user selects a course and opens the assessments or grading configuration view.

Main Success Scenario:
1. The system displays the current list of assessments and the total weight used so far for the course.
2. The user chooses to add a new assessment.
3. The system displays a form with fields for assessment name, category, and weight percentage, with optional due date and notes if desired.
4. The user fills in the form and submits it.
5. The system validates that the weight is a valid number.
6. The system adds the assessment to the course and updates the total weight display.

Alternate Flows:
- Weight total not equal to 100 percent:
  - The system warns the user when the total weight is far from 100 percent but still allows saving, or it enforces a stricter rule based on project decisions.
- Edit or delete assessment:
  - The user selects an assessment to edit, modifies its fields, and saves.
  - The user selects an assessment to delete, confirms the deletion, and the system removes it and updates the total weight.

---

## UC5 – Enter and Update Grades for Assessments

Actor: Student  
Goal: Record grades to compute current and projected course performance.

Preconditions:
- The user is logged in.
- Course and assessments exist.

Trigger:
- The user navigates to the grades view for a particular course.

Main Success Scenario:
1. The system displays a list of assessments for the course, with fields for grade information.
2. The user enters grade information for one or more assessments, using either percentage or score and maximum score.
3. The system validates the input.
4. The system computes the percentage for each assessment if needed and recalculates the weighted course grade based on the assessment weights.
5. The system displays the updated course grade and any indicators related to the target grade.

Alternate Flows:
- Partial data:
  - If some assessments remain without grades, the system calculates a grade based only on completed assessments and clearly indicates that some weights are still pending.

---

## UC6 – Input Study Hours

Actor: Student  
Goal: Input time spent studying a course so that the system can track study hours.

Preconditions:
- The user is logged in.
- At least one course exists.

Trigger:
- The user selects an option such as “Add Hours” or “Log Study Time” from the dashboard or course detail page.

Main Success Scenario:
1. The system displays a form with fields for course selection, date, and number of hours studied.
2. If the user initiated the flow from a specific course page, that course is preselected.
3. The user enters the date and the number of hours and submits the form.
4. The system validates that hours are positive and that the date is valid.
5. The system creates a study time entry linked to the chosen course and user.
6. Aggregated values such as weekly totals and dashboard summaries are updated to reflect the new entry.

Alternate Flows:
- Invalid hours or date:
  - The system shows validation errors and allows the user to correct and resubmit.

---

## UC7 – View Weekly Summary Dashboard

Actor: Student  
Goal: View a weekly overview of study time, recommendations, and gaps.

Preconditions:
- The user is logged in.

Trigger:
- The user navigates to the main dashboard or weekly summary view.

Main Success Scenario:
1. The system determines the current week based on a consistent definition such as Monday to Sunday.
2. The system aggregates total study hours per course for that week using the stored study time entries.
3. The system runs the recommendation algorithm to compute recommended hours for each course for the same week.
4. The system displays total hours studied this week, per-course hours, recommended hours, and the gap for each course.
5. The system shows at least one chart for weekly totals and a breakdown per course.
6. The user can switch to previous or next weeks, and the data updates accordingly.

Alternate Flows:
- No study hours entered:
  - The system displays a message indicating that no study hours have been entered yet and encourages the user to add hours.

---

## UC8 – Generate Study Time Recommendations

Actor: Student  
Goal: Obtain per-course weekly study hour recommendations tailored to grades and goals.

Preconditions:
- The user is logged in.
- Courses and targets are defined.

Trigger:
- The user loads the dashboard or explicitly requests an update of recommendations.

Main Success Scenario:
1. The system retrieves the list of courses for the user.
2. For each course, the system retrieves the target grade, any target weekly hours, the current grade, and recent study hours.
3. The system applies a heuristic to compute recommended weekly hours for each course, taking into account factors such as difference between current and target grade and total study capacity if available.
4. The system associates recommended hours with each course for the current week.
5. The dashboard displays recommended hours, actual hours, and gaps per course.

Alternate Flows:
- Missing grade data:
  - If no grades are entered for a course, the system bases the recommendation on target weekly hours or uses a baseline distribution among courses.
- Total weekly cap:
  - If the user has specified a desired total number of study hours per week, the system scales recommendations so that the sum does not exceed this cap.

---

# Domain Model

## 1. User

Attributes:
- `id` – primary key.
- `email` – unique email address.
- `password_hash` – hashed password.
- `name` – display name.
- `created_at` – timestamp when the user was created.
- `updated_at` – timestamp when the user was last updated.

Relationships:
- A user has many courses.
- A user has many study sessions, directly or through courses.
- A user has many recommendation snapshots.

---

## 2. Course

Attributes:
- `id` – primary key.
- `user_id` – foreign key referencing the owning user.
- `code` – course code such as `"MATH 135"`.
- `title` – full course title.
- `credit_weight` – numeric course credit or importance value.
- `instructor_name` – name of the instructor, if stored.
- `start_date` – start date of the course, if stored.
- `end_date` – end date of the course, if stored.
- `created_at` – timestamp when the course was created.
- `updated_at` – timestamp when the course was last updated.

Domain rules:
- Course code and title should not be empty.
- It should be difficult for a user to create obvious duplicate courses.

Relationships:
- A course has one course target.
- A course has many assessments.
- A course has many study sessions.
- A course can appear in many recommendation snapshots.

---

## 3. CourseTarget

Attributes:
- `id` – primary key.
- `course_id` – foreign key referencing the course, enforced as unique to maintain a one-to-one relationship.
- `target_final_grade` – desired final grade percentage for the course.
- `target_weekly_hours` – desired weekly study hours for the course.
- `min_weekly_hours` – minimum weekly hours the user is willing to allocate.
- `max_weekly_hours` – maximum weekly hours the user is willing to allocate.
- `created_at` – timestamp when the target record was created.
- `updated_at` – timestamp when the target record was last updated.

Relationships:
- One course target belongs to exactly one course.

---

## 4. Assessment

Attributes:
- `id` – primary key.
- `course_id` – foreign key referencing the course.
- `name` – assessment name such as `"Midterm 1"`.
- `category` – assessment category such as quiz, assignment, midterm, or final.
- `weight_percent` – percentage contribution of this assessment to the final course grade.
- `due_date` – date the assessment is due.
- `notes` – free-form text notes about the assessment if needed.
- `score_obtained` – numeric score the student received on the assessment.
- `score_max` – maximum possible score for the assessment.
- `percentage` – percentage grade for the assessment, either stored or derived from `score_obtained` and `score_max`.
- `graded_date` – date when the assessment was graded.
- `created_at` – timestamp when the assessment was created.
- `updated_at` – timestamp when the assessment was last updated.

Domain rules:
- The sum of `weight_percent` values for assessments in a course should be close to 100.
- When both `score_obtained` and `score_max` are present, `percentage` is computed as `score_obtained / score_max * 100`.
- Either `percentage` is stored directly or reliably derived from the scores.

Relationships:
- Many assessments belong to one course.

---

## 5. StudySession

Attributes:
- `id` – primary key.
- `course_id` – foreign key referencing the course.
- `user_id` – foreign key referencing the user.
- `date` – date on which the study occurred.
- `duration_hours` – number of hours studied for this session, stored as a numeric value.
- `created_at` – timestamp when the study session was created.
- `updated_at` – timestamp when the study session was last updated.

Domain rules:
- `duration_hours` must be greater than zero.
- `date` must be a valid calendar date.

Relationships:
- Many study sessions belong to one course.
- Many study sessions belong to one user.

---

## 6. RecommendationSnapshot

Attributes:
- `id` – primary key.
- `user_id` – foreign key referencing the user.
- `course_id` – foreign key referencing the course.
- `week_start_date` – date representing the start of the week for which recommendations are stored.
- `recommended_hours` – number of hours recommended for the course in that week.
- `actual_hours` – number of hours actually entered for that course in that week at the time of the snapshot.
- `created_at` – timestamp when the snapshot was created.

Relationships:
- Many recommendation snapshots belong to one user.
- Many recommendation snapshots belong to one course.

---

## Relationships Summary

- A user has many courses.
- A course belongs to one user.
- A course has one course target.
- A course has many assessments.
- A course has many study sessions.
- A user has many study sessions.
- A user and a course each have many recommendation snapshots.

---

## Derived Metrics and Core Logic

Current course grade:
- For each assessment, determine the assessment percentage using stored `percentage` or by dividing `score_obtained` by `score_max` and multiplying by 100.
- Course grade is the sum, over all assessments in the course, of `assessment_percentage * weight_percent / 100`.
- If some assessments do not yet have grades, the system calculates a grade based on completed assessments and can indicate that some weight is still pending.

Weekly study hours:
- For a given week and course, weekly hours are the sum of `duration_hours` for all study sessions whose `date` falls in that week.
- Total weekly hours across courses is the sum of weekly hours for each course.

Recommendation algorithm:
- Inputs include course targets, current grades, target weekly hours, and recent weekly hours data.
- The algorithm produces recommended weekly hours for each course, possibly respecting a maximum total weekly study time.
- The algorithm prioritizes courses where the current grade is below the target or where target weekly hours are high.

Gap analysis:
- For each course and week, gap is `recommended_hours - actual_hours`.
- This value is used to flag courses that are under-studied relative to the recommendation.