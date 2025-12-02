




---

# Snowmark Grade Tracker - Comprehensive User Manual

## Table of Contents
1. Overview
2. Getting Started
3. Account Management
4. Core Features
5. Managing Subjects
6. Managing Categories
7. Recording Grades and Assessments
8. Grade Predictions
9. Viewing Statistics
10. Advanced Features
11. Troubleshooting

---

## Overview

### What is Snowmark?

Snowmark is a comprehensive grade tracking and prediction application designed for students who want to take control of their academic performance. Built with a modern Flask backend and responsive web interface, Snowmark helps you:

- **Track Grades**: Log all your assessments, assignments, and exam scores in one organized place
- **Organize by Subject**: Keep grades organized across multiple subjects with custom categories (Exams, Homework, Quizzes, etc.)
- **Predict Future Performance**: Use machine learning algorithms to predict what grade you might receive based on your study time and past performance
- **Monitor Progress**: View comprehensive statistics and analytics about your academic performance
- **Manage Assessments**: Edit, delete, and bulk manage your grades with ease

### Key Statistics
- **122+ Automated Tests**: Ensures reliability and correctness
- **Multi-User Support**: Complete data isolation—your grades are completely private
- **Responsive Design**: Access from desktop, tablet, or mobile devices
- **No Data Loss**: All data is securely stored in a MySQL database

### Target Users
- Students managing multiple courses
- Parents monitoring student progress
- Educators tracking class performance
- Anyone seeking insights into academic trends

---

## Getting Started

### System Requirements

Before using Snowmark, ensure you have:

- **Internet Connection**: Required to access the online application
- **Modern Web Browser**: Chrome, Firefox, Safari, or Edge (latest versions recommended)
- **JavaScript Enabled**: Required for interactive features
- **Screen Size**: Works on screens 768px and larger for optimal experience

### Accessing Snowmark

1. Open your web browser
2. Navigate to the application URL provided by your administrator
3. You will see the **Landing Page** with login and registration options

### First-Time Setup

If you're a new user:

1. Click on the **"Register"** button on the landing page
2. Enter a unique username (3-20 characters recommended)
3. Create a strong password (8+ characters with mix of letters, numbers, and symbols)
4. Click **"Create Account"**
5. You'll be redirected to the login page
6. Enter your credentials to access your dashboard

---

## Account Management

### Creating an Account

#### Registration Process

1. Navigate to the **Register** page
2. Fill in the registration form:
   - **Username**: Choose a unique identifier for your account
   - **Password**: Create a secure password
   - **Confirm Password**: Re-enter your password to verify
3. Click **"Register"** button
4. Upon successful registration, you'll receive confirmation

**Security Notes**:
- Passwords are encrypted with industry-standard hashing
- Each user's data is completely isolated from other users
- You cannot register with a username that already exists

### Logging In

1. Go to the **Login** page
2. Enter your username
3. Enter your password
4. Click **"Login"**
5. You'll be taken to your **Dashboard/Home** page

**Tip**: Your login session is maintained while you use the application. Close your browser or click **"Logout"** to end your session.

### Managing Your Account

#### Logging Out

- Click the **Logout** button (typically in the top navigation)
- You'll be redirected to the landing page
- Your data remains safely stored in the database

#### Password Management

- Passwords are not stored in plain text—they're encrypted
- If you forget your password, contact your administrator
- Passwords must be entered during registration and cannot be changed through the interface

---

## Core Features

### Dashboard Overview

When you log in, you'll see your **Dashboard** (the home page) which contains:

1. **Subject List**: All your current active subjects
2. **Quick Stats**: Overview of your grades
3. **Recent Assessments**: Your most recently added grades
4. **Navigation Menu**: Links to different sections of the app

### Main Navigation

The application includes these key sections:

| Section | Purpose |
|---------|---------|
| **Home** | Main dashboard showing all subjects and recent grades |
| **About** | Information about the application and how to use it |
| **Stats** | Detailed analytics and statistics about your performance |
| **Subject Pages** | Detailed view of each subject's grades and categories |
| **Logout** | Sign out of your account |

---

## Managing Subjects

### What Are Subjects?

Subjects represent the courses or classes you're taking (e.g., "Mathematics", "English Literature", "Biology"). Each subject:

- Has its own set of grades and assessments
- Can have multiple categories (Exams, Homework, etc.)
- Has independent statistics and predictions
- Can be active (visible in main dashboard) or retired (archived)

### Creating a New Subject

1. From your **Dashboard/Home** page
2. Look for the **"Add Subject"** button or form
3. Enter the subject name (e.g., "CS101", "Physics", "History")
4. Click **"Add Subject"** or **"Create"**
5. The new subject will appear in your subject list

**Example Subjects**:
- Mathematics
- English Literature
- Computer Science
- Biology
- Economics
- Psychology

### Viewing Subject Details

1. Click on any subject name from your dashboard
2. You'll see:
   - **All assessments** in that subject
   - **Categories** used in the subject
   - **Grade statistics** (average, total weight, etc.)
   - **Subject-specific options** (rename, retire, delete)

### Renaming a Subject

If you need to change a subject's name:

1. Go to the subject's detail page
2. Find the **"Rename Subject"** button
3. Enter the new name
4. Click **"Confirm"** or **"Save"**
5. The subject will immediately update across the application

**Note**: Renaming a subject does NOT affect your existing grades and assessments.

### Retiring a Subject

**Retiring** means archiving a subject—it won't appear on your main dashboard, but all data is preserved.

Use this when:
- A course is completed
- A subject is no longer active this semester
- You want to keep historical data but declutter your dashboard

#### How to Retire:

1. Go to the subject's detail page
2. Click **"Retire Subject"**
3. Confirm the action
4. The subject disappears from your main dashboard

#### Accessing Retired Subjects:

1. From the **Dashboard**, look for a **"View Retired Subjects"** link or tab
2. All your retired subjects appear here
3. You can still view their grades, statistics, and predictions
4. You can also **unretire** them to make them active again

### Unretiring a Subject

To bring back a retired subject:

1. Go to **"Retired Subjects"** section
2. Find the subject you want to restore
3. Click **"Unretire Subject"** or **"Restore"**
4. The subject returns to your main dashboard

### Deleting a Subject

**Warning**: Deleting a subject permanently removes it and ALL associated grades. This action cannot be undone.

To delete a subject:

1. Go to the subject's detail page
2. Click **"Delete Subject"** (usually red button)
3. Confirm the deletion in the popup
4. The subject and all its assessments are permanently removed

**Best Practice**: Retire subjects instead of deleting them to preserve historical data.

---

## Managing Categories

### What Are Categories?

Categories are the types of assessments within a subject:

**Common Examples**:
- **Exams** (weight: 40%)
- **Homework** (weight: 30%)
- **Quizzes** (weight: 15%)
- **Participation** (weight: 10%)
- **Projects** (weight: 5%)

Each category:
- Has a **weight** (percentage contribution to final grade)
- Contains multiple individual assessments
- Calculates its own average
- Contributes proportionally to the subject's overall grade

### Understanding Category Weights

Category weights determine how much each category contributes to your final grade:

**Example**:
- Exams (40%) + Homework (30%) + Quizzes (20%) + Projects (10%) = 100%

If your grades are:
- Exams: 85% (weight: 40%) = 34 points
- Homework: 90% (weight: 30%) = 27 points
- Quizzes: 80% (weight: 20%) = 16 points
- Projects: 95% (weight: 10%) = 9.5 points
- **Final Grade: 86.5%**

### Adding a Category

1. Navigate to your subject's detail page
2. Find the **"Add Category"** button
3. Enter:
   - **Category Name**: (e.g., "Exams", "Homework")
   - **Weight**: The percentage contribution (0-100)
4. Click **"Add Category"** or **"Create"**
5. The category is created and ready for assessments

### Updating a Category

To change a category's weight:

1. Go to the subject's detail page
2. Find the category you want to modify
3. Click **"Edit"** or **"Update"** next to the category
4. Change the weight value
5. Click **"Save"** or **"Update"**
6. Weights are recalculated for all related grades

**Important**: Total weights don't have to equal 100%, but typically should for accurate grade calculations.

### Deleting a Category

To remove a category from a subject:

1. Go to the subject's detail page
2. Find the category to delete
3. Click **"Delete Category"** (usually red button)
4. Confirm the action
5. The category is removed, but individual grades may be reorganized

**Note**: Some grades might be reassigned depending on how the system handles category dependencies.

---

## Recording Grades and Assessments

### What Is an Assessment?

An assessment is a single grade entry representing:
- A specific assignment, quiz, exam, or project
- The grade you received (or will receive)
- The study time invested
- Its weight within a category
- The category it belongs to

### Adding a Grade

This is the core function of Snowmark. To add a new assessment:

1. Go to your **Dashboard** or a specific **Subject** page
2. Find the **"Add Assessment"** or **"Add Grade"** button
3. Fill in the form:

   **Required Fields**:
   - **Subject**: Select which subject this belongs to
   - **Category**: Select the assessment type (Exams, Homework, etc.)
   - **Assessment Name**: What is this assessment? (e.g., "Midterm Exam", "Chapter 3 Quiz")
   - **Grade**: What grade did you receive? (0-100 or letter grade)
   - **Study Time**: How many hours did you spend preparing? (decimal numbers allowed)
   - **Weight**: How much does this assessment count? (typically 1.0, but can be 0.5, 2.0, etc.)

4. Click **"Add"**, **"Submit"**, or **"Save"**
5. The assessment appears immediately in your subject view

### Example: Adding a Math Midterm

```
Subject: Mathematics
Category: Exams
Assessment Name: Midterm Exam - Calculus
Grade: 88
Study Time: 15 (hours)
Weight: 1.0
```

### Viewing All Assessments

**In a Subject**:
1. Click on the subject name from your dashboard
2. See all assessments organized by category
3. Assessments show: Name, Grade, Weight, Study Time

**In Statistics Page**:
1. Go to the **Stats** page
2. View comprehensive grade breakdowns
3. See trends and analytics

### Editing an Assessment

If you need to update a grade you entered:

1. Navigate to the assessment (in subject view or stats)
2. Click **"Edit"**, **"Modify"**, or the pencil icon
3. Update any field:
   - Grade
   - Study Time
   - Weight
   - Assessment Name
   - Category
4. Click **"Save"** or **"Update"**
5. The assessment updates immediately

**Example**: You took a quiz in an exam and your grade was corrected from 75 to 82. Edit the grade to reflect the correction.

### Deleting an Assessment

To remove a single assessment:

1. Find the assessment you want to delete
2. Click **"Delete"** (usually red button or trash icon)
3. Confirm the deletion
4. The assessment is permanently removed
5. Statistics update automatically

### Bulk Deletion

If you need to delete multiple assessments at once:

1. Go to your subject view
2. Look for **"Bulk Delete"** or **"Select Multiple"** option
3. Check boxes next to assessments you want to delete
4. Click **"Delete Selected"** or **"Remove Bulk"**
5. Confirm the bulk deletion
6. Multiple assessments are removed at once

**Use Cases for Bulk Delete**:
- Cleaning up incorrectly entered data
- Removing all assessments from a previous semester
- Starting fresh with a subject

---

## Grade Predictions

### What Are Predictions?

Predictions use machine learning algorithms to forecast your future grade based on:

- **Historical Performance**: Your past grades in the subject
- **Study Time**: Hours you've invested in studying
- **Assessment Weights**: How different assessments are weighted
- **Category Performance**: How well you're doing in each category

The prediction system learns from your data and becomes more accurate as you add more assessments.

### How Predictions Work

The prediction algorithm:

1. Analyzes all your past grades in a subject
2. Correlates grades with study time invested
3. Accounts for category weights and importance
4. Generates a predicted grade for future assessments
5. Suggests study time needed to achieve target grades

**Example**:
If you've historically gotten ~85% in exams after 12 hours of studying, and you put in 12 hours for the next exam, the system predicts ~85% for that exam.

### Getting a Prediction

#### Method 1: Predict Next Grade

To see what grade you might get on your next assessment:

1. Go to a **Subject** page
2. Find the **"Get Prediction"** button
3. Select a **category** (Exams, Homework, etc.)
4. Click **"Predict"**
5. The system shows:
   - **Predicted Grade**: Your likely grade
   - **Confidence**: How confident the prediction is
   - **Based On**: Number of past assessments analyzed

**Interpretation**:
- Prediction of 82% means statistically you're likely to score around 82% on your next assessment in that category

#### Method 2: Predict Required Study Hours

If you want to achieve a target grade:

1. Go to a **Subject** page
2. Find **"Calculate Study Hours"** or **"Predict Hours"**
3. Enter your **target grade** (e.g., 90%)
4. Select a **category**
5. Click **"Calculate"**
6. The system shows:
   - **Required Study Hours**: How much to study to hit your target
   - **Confidence**: Reliability of the estimate

**Example**:
- You want an 90% on the next exam
- The system says: "Study 18 hours to reach 90%"
- (Based on your historical study-to-grade correlation)

### Using Predictions Strategically

**Predictions help you**:
- Allocate study time efficiently
- Set realistic grade goals
- Identify subjects needing more effort
- Track improvement over time
- Plan ahead for important assessments

**Example Study Plan**:
```
Current Grade Average: 78%
Target Grade: 85%
System Prediction: Need 8 more hours of study per assessment

Action Plan:
- Add 1-2 hours study time per week
- Focus on weak categories
- Re-test after 3-4 assessments
```

### Prediction Limitations

Predictions are more accurate when:
- You have 5+ assessments in a category
- Your study patterns are consistent
- You haven't drastically changed study habits

Predictions are less accurate when:
- You have very few assessments
- Your performance is highly variable
- You're in a new subject with no data

---

## Viewing Statistics

### Statistics Page Overview

The **Stats** page provides comprehensive analytics about your academic performance:

1. Navigate to **Stats** from the main menu
2. You'll see multiple sections of data and visualizations

### What Statistics Are Available?

#### Subject-Level Statistics

For each subject, you can see:

- **Average Grade**: Mean of all grades in the subject
- **Total Weight**: Sum of all assessment weights
- **Assessment Count**: How many grades you've entered
- **Grade Distribution**: How grades are spread across categories
- **Predicted Grade**: What your final grade will likely be
- **Category Breakdown**: Performance in each category type

#### Category-Level Statistics

For each category within a subject:

- **Category Average**: Mean grade in that category
- **Category Weight**: Percentage contribution to final grade
- **Assessment Count**: Number of items in the category
- **Grade Range**: Highest and lowest grades
- **Contribution to Final**: Points earned toward final grade

#### Study Time Analytics

- **Total Study Hours**: All hours logged across all subjects
- **Average Study Time Per Assessment**: How much you typically study
- **Study Time by Subject**: Which subjects get the most study time
- **Study Time Trends**: Are you studying more or less recently?

#### Predictive Analytics

- **Predicted Final Grades**: What you're likely to earn in each subject
- **Improvement Trends**: Are your grades improving or declining?
- **Performance Compared to Average**: How you're doing relative to your historical average
- **Required Study Hours**: To achieve target grades

### Using Statistics to Improve

**Identify Weak Areas**:
1. Look at category averages
2. Find categories below your target (e.g., "Exams: 72%")
3. Increase study time for that category
4. Track improvement in next assessment

**Optimize Study Time**:
1. Review which subjects need the most work
2. Use prediction to know how much to study
3. Monitor study hours vs. grade improvements
4. Adjust strategy if correlation is weak

**Set Goals**:
1. See current average in each subject
2. Set realistic target grades
3. Use prediction calculator
4. Plan study schedule accordingly

---

## Advanced Features

### Bulk Operations

#### Bulk Deleting Assessments

Instead of deleting one assessment at a time:

1. Go to subject view
2. Check boxes next to multiple assessments
3. Click **"Delete Selected"** or **"Bulk Delete"**
4. Confirm in popup
5. All selected assessments are removed instantly

**Advantages**:
- Faster than individual deletions
- Clean up incorrect data quickly
- Reset a subject without deleting it entirely

### Weight Recalculation

The system automatically recalculates category weights when:

- You add a new assessment
- You delete an assessment
- You modify a weight
- You change a category's weight

This ensures your final grade calculation stays accurate.

**Manual Recalculation**:
1. If needed, you can trigger recalculation from the subject page
2. Click **"Recalculate Weights"** (if available)
3. All weights update based on current assessments

### Data Organization Features

#### Sorting and Filtering

- **Sort by Grade**: See best to worst grades
- **Sort by Date Added**: Most recent assessments first
- **Sort by Study Time**: Most studied assessments first
- **Filter by Category**: Show only specific types
- **Filter by Date Range**: Grades from specific period

#### Search Functionality

- Search by assessment name
- Search by subject name
- Quick navigation to specific grades

### Responsive Design

Snowmark works seamlessly on:

- **Desktop**: Full-featured interface
- **Tablet**: Touch-friendly buttons, readable layout
- **Mobile**: Optimized for small screens

Features adapt automatically:
- Navigation changes from menu to hamburger menu on mobile
- Table layouts become card layouts on small screens
- Touch targets are appropriately sized

### Multi-Subject Management

Managing multiple subjects effectively:

1. **Dashboard Overview**: See all subjects at once
2. **Quick Stats**: Spot weak areas across subjects
3. **Comparison View**: Compare performance across subjects (if available)
4. **Time Management**: Track total study time across all subjects

---

## Troubleshooting

### Common Issues and Solutions

#### Login Issues

**Problem**: "Invalid username or password"

**Solutions**:
1. Verify CAPS LOCK is off
2. Check that username is spelled correctly
3. Ensure password matches exactly (spaces matter)
4. Verify account exists (try registering if it doesn't)
5. Contact administrator if issues persist

**Problem**: "Session expired"

**Solutions**:
1. Log in again—sessions timeout for security
2. Clear browser cookies if problems continue
3. Try a different browser
4. Ensure JavaScript is enabled

#### Data Entry Issues

**Problem**: "Cannot add assessment" or form won't submit

**Solutions**:
1. Ensure all required fields are filled (Subject, Category, Grade, etc.)
2. Check grade is a valid number (0-100)
3. Check study time is numeric (can be decimal like 2.5)
4. Check weight is numeric
5. Ensure subject and category exist before adding assessment

**Problem**: Grade shows incorrectly

**Solutions**:
1. Verify the grade value you entered
2. Check that category weights add up correctly
3. Refresh the page to see updated calculations
4. Weights recalculate automatically after changes

#### Display Issues

**Problem**: Page layout looks broken on mobile

**Solutions**:
1. Rotate device to landscape for better view
2. Zoom out (pinch zoom) to see full page
3. Upgrade to latest browser version
4. Clear browser cache (Ctrl+Shift+Del or Cmd+Shift+Del)

**Problem**: Grades not updating after changes

**Solutions**:
1. Refresh the page (Ctrl+R or Cmd+R)
2. Clear browser cache
3. Check network connection
4. Try in incognito/private browsing mode
5. Report issue if problem persists

#### Feature Issues

**Problem**: "Prediction not available"

**Solutions**:
1. Add more assessments to category (need ~5 for accuracy)
2. Check that assessments have study time entered
3. Predictions improve with more data
4. Try after adding 2-3 more assessments

**Problem**: "Cannot retire/delete subject"

**Solutions**:
1. Ensure you have assessments in the subject (system may restrict empty actions)
2. Refresh and try again
3. Check for JavaScript errors (browser console)
4. Try different browser

### Performance Optimization

If the app feels slow:

1. **Clear Cache**: Browser cache accumulates data
   - Ctrl+Shift+Del (Windows) or Cmd+Shift+Del (Mac)
   - Select "Cached images and files"
   - Click "Clear data"

2. **Disable Browser Extensions**: Some extensions slow down sites
   - Try incognito/private mode

3. **Check Connection**: Ensure stable internet
   - Close other bandwidth-heavy apps
   - Move closer to WiFi router

4. **Update Browser**: Latest versions are faster
   - Check browser settings for updates

### Getting Help

If issues persist:

1. **Check the About Page**: Contains additional help resources
2. **Review Your Input**: Double-check all data entries
3. **Try Different Browser**: Rules out browser-specific issues
4. **Contact Administrator**: For server or account issues

---

## Best Practices and Tips

### Data Entry Best Practices

**1. Consistent Naming**:
- Use standard category names (Exams, Homework, Projects, Quizzes)
- Use descriptive assessment names ("Midterm Exam", "Chapter 3 Quiz")
- Makes searching and filtering easier

**2. Timely Entry**:
- Enter grades soon after receiving them
- Better for memory accuracy
- Predictions improve with up-to-date data

**3. Study Time Accuracy**:
- Log actual hours spent studying
- Include class time if it counts toward preparation
- Be consistent in what you include

**4. Weight Assignment**:
- Most assessments have weight 1.0
- Use 2.0 for major assessments (final exam)
- Use 0.5 for minor assessments (quick quiz)
- Ensure category weights total ~100%

### Strategic Use of Features

**1. Use Predictions**:
- Check predictions regularly
- Adjust study time based on recommendations
- Track if predictions match actual results

**2. Monitor Statistics**:
- Weekly check of your performance
- Identify downward trends early
- Celebrate improvements

**3. Organize with Categories**:
- Use weight to reflect importance
- Standard breakdown: Exams 40%, Homework 30%, Quizzes 20%, Projects 10%
- Adjust based on your course requirements

**4. Manage Subjects**:
- Retire completed subjects to reduce clutter
- Keep current, active courses visible
- Archive old data for historical reference

### Maximizing Grade Potential

1. **Prediction-Based Study Planning**:
   - Calculate hours needed for target grade
   - Add buffer time (20% extra)
   - Track actual vs. predicted results

2. **Trend Analysis**:
   - Are you improving over time?
   - Do certain categories need work?
   - Adjust focus areas accordingly

3. **Goal Setting**:
   - Set semester grade goals
   - Break into subject-level goals
   - Use category breakdown to plan study

4. **Regular Review**:
   - Monthly check of progress
   - Quarterly review of predictions
   - End-of-semester analysis

---

## Privacy and Security

### Data Privacy

**Your data is completely private**:
- Data is encrypted in transit
- Passwords are hashed (never stored in plain text)
- Other users cannot access your information
- Data is stored in secure MySQL database

### Account Security

**Keep your account safe**:
1. Use strong passwords (8+ chars, mix of types)
2. Don't share your login credentials
3. Log out when using shared computers
4. Clear browser history on shared devices

### Data Backup

**Your data is protected**:
- Stored in MySQL database
- Regular backups (handled by administrator)
- No data loss unless explicitly deleted by you
- Deleted data cannot be recovered

---

## Frequently Asked Questions

**Q: Can I export my data?**
A: Contact your administrator about data export options.

**Q: What if I want to start over?**
A: You can retire all subjects and start fresh, or contact your administrator for account reset.

**Q: Are my grades visible to others?**
A: No. Your data is completely private and isolated from other users.

**Q: Can I change my username?**
A: Contact your administrator. Usernames are typically permanent identifiers.

**Q: How accurate are predictions?**
A: Accuracy improves with more data. With 5+ assessments, predictions are typically 80-90% accurate.

**Q: What's the difference between retiring and deleting?**
A: Retiring archives a subject (data preserved, not visible). Deleting removes it permanently with no recovery.

**Q: Can I have multiple accounts?**
A: Contact your administrator. Typically one account per person is recommended.

**Q: Is there a mobile app?**
A: Snowmark works on mobile via web browser (responsive design). Native apps may be available—check with administrator.

---

## Glossary of Terms

| Term | Definition |
|------|------------|
| **Assessment** | A single grade entry (quiz, exam, assignment) |
| **Category** | Type of assessment (Exams, Homework, Projects) |
| **Weight** | How much an assessment counts (1.0 = standard, 2.0 = double) |
| **Study Time** | Hours spent preparing for an assessment |
| **Prediction** | Machine learning forecast of future grades |
| **Subject** | Course or class you're taking |
| **Retire** | Archive a subject (preserve data, hide from main view) |
| **Final Grade** | Weighted average of all assessments in a subject |
| **Category Weight** | Percentage a category contributes to final grade |

---

## Support and Feedback

### Reporting Issues

Found a bug or issue?
1. Note the exact error message
2. Note what you were trying to do
3. Contact your administrator with details
4. Include screenshot if possible

### Requesting Features

Have a feature idea?
1. Contact your administrator
2. Describe the feature clearly
3. Explain how it would help your workflow
4. Provide use cases

### Getting Updates

Stay informed about:
- New features
- Performance improvements
- Bug fixes
- System maintenance

Contact your administrator for:
- Release notes
- System status
- Maintenance schedules

---

## Conclusion

Snowmark Grade Tracker is designed to help you take control of your academic performance. By consistently tracking grades, managing categories effectively, and using predictions strategically, you can:

- ✅ Understand your academic standing in real-time
- ✅ Make data-driven decisions about study time
- ✅ Set and achieve ambitious grade goals
- ✅ Track improvement over time
- ✅ Reduce academic stress through preparation

**Start small** with one subject, get comfortable with the features, then expand to all your courses. Use predictions and statistics to guide your studying, and you'll see improvements in your grades.

---

## Document Version

- **Version**: 1.0
- **Last Updated**: December 2, 2025
- **For**: Snowmark Grade Tracker Application
- **Target Audience**: Students

---

**Questions or feedback?** Contact your system administrator for support.

---


