# Comprehensive Test Plan - Snowmark Grade Tracking Application

**Project:** SE101 Team 21 - Snowmark  
**Version:** 2.0  
**Date:** November 30, 2025

---

## Table of Contents

1. [Overview](#1-overview)
2. [Test Environment](#2-test-environment)
3. [Authentication & User Management](#3-authentication--user-management)
4. [Subject Management](#4-subject-management)
5. [Category/Weight Management](#5-categoryweight-management)
6. [Assessment Management](#6-assessment-management)
7. [Grade Prediction System](#7-grade-prediction-system)
8. [Subject Predictor](#8-subject-predictor)
9. [Statistics & Analytics](#9-statistics--analytics)
10. [User Interface Features](#10-user-interface-features)
11. [Data Integrity & Edge Cases](#11-data-integrity--edge-cases)
12. [Performance Tests](#12-performance-tests)

---

## 1. Overview

This test plan covers all major features of the Snowmark grade tracking application. Tests are organized by feature area and include both manual testing procedures and automated test coverage.

### 1.1 Test Objectives
- Verify all user-facing features work correctly
- Ensure data integrity across all operations
- Validate prediction algorithms produce sensible results
- Confirm user isolation (users can only see their own data)
- Test edge cases and error handling

### 1.2 Test Categories
- **Functional Tests:** Verify features work as expected
- **Integration Tests:** Test feature interactions
- **UI Tests:** Verify user interface behavior
- **Data Tests:** Validate data integrity and calculations

---

## 2. Test Environment

### 2.1 Setup Requirements
- **Python Version:** 3.12+
- **Database:** MySQL (local or remote)
- **Browser:** Chrome/Firefox/Safari (latest versions)
- **Testing Framework:** pytest

### 2.2 Test Accounts
| Username | Password | Purpose |
|----------|----------|---------|
| testuser1 | test123 | Primary testing |
| testuser2 | test456 | User isolation testing |
| admin | admin123 | Admin testing |

---

## 3. Authentication & User Management

### 3.1 Registration Tests

| Test ID | Test Name | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| AUTH-001 | Successful Registration | 1. Go to /register<br>2. Enter valid username/password<br>3. Click Register | Account created, redirected to login | High |
| AUTH-002 | Duplicate Username | 1. Register with existing username | Error message displayed | High |
| AUTH-003 | Empty Fields | 1. Submit form with empty fields | Validation error shown | Medium |
| AUTH-004 | Password Mismatch | 1. Enter different passwords in confirm field | Error message displayed | Medium |
| AUTH-005 | Username Too Short | 1. Enter username < 3 characters | Validation error shown | Low |

### 3.2 Login Tests

| Test ID | Test Name | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| AUTH-010 | Successful Login | 1. Go to /login<br>2. Enter valid credentials<br>3. Click Login | Redirected to /home | High |
| AUTH-011 | Invalid Password | 1. Enter valid username, wrong password | Error message, stay on login | High |
| AUTH-012 | Invalid Username | 1. Enter non-existent username | Error message, stay on login | High |
| AUTH-013 | Empty Credentials | 1. Submit empty form | Validation error | Medium |
| AUTH-014 | Session Persistence | 1. Login<br>2. Close browser<br>3. Reopen and visit /home | Still logged in (or login required based on config) | Medium |

### 3.3 Logout Tests

| Test ID | Test Name | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| AUTH-020 | Successful Logout | 1. Login<br>2. Click Logout | Session ended, redirected to login | High |
| AUTH-021 | Access After Logout | 1. Logout<br>2. Try to access /home | Redirected to login | High |

### 3.4 User Isolation Tests

| Test ID | Test Name | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| AUTH-030 | Data Isolation | 1. Login as user1, add data<br>2. Logout, login as user2 | User2 cannot see user1's data | Critical |
| AUTH-031 | API Isolation | 1. Try to access another user's data via API | Access denied or empty result | Critical |

---

## 4. Subject Management

### 4.1 Add Subject Tests

| Test ID | Test Name | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| SUBJ-001 | Add New Subject | 1. Click "Add Subject"<br>2. Enter name (e.g., "CS 101")<br>3. Save | Subject appears in sidebar | High |
| SUBJ-002 | Duplicate Subject | 1. Add subject with existing name | Error or handled gracefully | Medium |
| SUBJ-003 | Empty Subject Name | 1. Try to add subject with empty name | Validation error | Medium |
| SUBJ-004 | Special Characters | 1. Add subject with special chars (e.g., "Math & Stats") | Subject created successfully | Low |

### 4.2 Edit Subject Tests

| Test ID | Test Name | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| SUBJ-010 | Rename Subject | 1. Click edit on subject<br>2. Change name<br>3. Save | Name updated everywhere | High |
| SUBJ-011 | Rename Updates Assessments | 1. Add assessments to subject<br>2. Rename subject | Assessments show new name | High |

### 4.3 Delete Subject Tests

| Test ID | Test Name | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| SUBJ-020 | Delete Empty Subject | 1. Create subject with no assessments<br>2. Delete | Subject removed | High |
| SUBJ-021 | Delete Subject with Data | 1. Delete subject containing assessments | Warning shown, cascading delete on confirm | High |
| SUBJ-022 | Cancel Delete | 1. Click delete<br>2. Cancel confirmation | Subject remains | Medium |

### 4.4 Retire/Unretire Subject Tests

| Test ID | Test Name | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| SUBJ-030 | Retire Subject | 1. Click retire on subject | Subject moved to "Retired" section | Medium |
| SUBJ-031 | Unretire Subject | 1. Click unretire on retired subject | Subject returns to active list | Medium |
| SUBJ-032 | Retired Subject Hidden | 1. Retire subject | Subject not shown in main dropdown filters | Medium |

---

## 5. Category/Weight Management

### 5.1 Add Category Tests

| Test ID | Test Name | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| CAT-001 | Add Category | 1. Go to subject page<br>2. Add category (e.g., "Assignments", 30%) | Category appears in table | High |
| CAT-002 | Weight Validation | 1. Try to add category with weight > 100 | Validation error | Medium |
| CAT-003 | Negative Weight | 1. Try to add category with negative weight | Validation error | Medium |
| CAT-004 | Duplicate Category Name | 1. Add category with same name as existing | Error or handled | Medium |

### 5.2 Edit Category Tests

| Test ID | Test Name | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| CAT-010 | Edit Category Weight | 1. Edit category<br>2. Change weight from 30% to 40%<br>3. Save | Weight updated, recalculated | High |
| CAT-011 | Edit Category Name | 1. Edit category name | Name updated in all views | Medium |
| CAT-012 | Weight Recalculation | 1. Change category weight | Individual assessment weights recalculated | High |

### 5.3 Delete Category Tests

| Test ID | Test Name | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| CAT-020 | Delete Empty Category | 1. Delete category with no assessments | Category removed | High |
| CAT-021 | Delete Category with Assessments | 1. Delete category containing assessments | Warning shown, cascade delete | High |

### 5.4 Weight Total Indicator Tests

| Test ID | Test Name | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| CAT-030 | Weight Total = 100% | 1. Add categories totaling 100% | Green indicator | Medium |
| CAT-031 | Weight Total < 100% | 1. Add categories totaling 80% | Blue indicator showing 80% | Medium |
| CAT-032 | Weight Total > 100% | 1. Add categories totaling 120% | Red/warning indicator | Medium |

---

## 6. Assessment Management

### 6.1 Add Assessment Tests

| Test ID | Test Name | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| ASMNT-001 | Add Complete Assessment | 1. Add row with subject, category, hours, name, grade | Assessment saved, appears in table | High |
| ASMNT-002 | Add Without Grade | 1. Add assessment with no grade | Assessment saved with grade = NULL | High |
| ASMNT-003 | Weight Auto-Calculation | 1. Add assessment to category with 3 existing | Weight = category_total / 4 | High |
| ASMNT-004 | Validation - No Subject | 1. Try to add without selecting subject | Validation error | Medium |
| ASMNT-005 | Validation - No Category | 1. Try to add without selecting category | Validation error | Medium |

### 6.2 Edit Assessment Tests

| Test ID | Test Name | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| ASMNT-010 | Edit Grade | 1. Click edit<br>2. Change grade from 80 to 90<br>3. Save | Grade updated | High |
| ASMNT-011 | Edit Study Hours | 1. Edit study hours | Hours updated | Medium |
| ASMNT-012 | Edit Assignment Name | 1. Edit name | Name updated | Medium |
| ASMNT-013 | Change Category | 1. Edit assessment<br>2. Change category | Assessment moves, weights recalculated for both categories | High |
| ASMNT-014 | Clear Grade | 1. Edit assessment<br>2. Remove grade<br>3. Save | Grade becomes NULL | Medium |

### 6.3 Delete Assessment Tests

| Test ID | Test Name | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| ASMNT-020 | Delete Single Assessment | 1. Click delete on row<br>2. Confirm | Assessment removed, weights recalculated | High |
| ASMNT-021 | Multi-Select Delete | 1. Select multiple checkboxes<br>2. Click "Delete Selected" | All selected removed | High |
| ASMNT-022 | Cancel Delete | 1. Click delete<br>2. Cancel | Assessment remains | Medium |

### 6.4 Weight Preview Tests

| Test ID | Test Name | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| ASMNT-030 | Weight Preview on Add | 1. Start adding new assessment<br>2. Select category | All rows in category show preview weight (italicized) | Medium |
| ASMNT-031 | Weight Preview Revert | 1. Start adding<br>2. Cancel/change category | Preview reverts to actual weights | Medium |
| ASMNT-032 | Weight Preview Accuracy | 1. Category has 3 items @ 10% each<br>2. Start adding 4th | Preview shows 7.5% (30/4) | High |

---

## 7. Grade Prediction System

### 7.1 Basic Prediction Tests

| Test ID | Test Name | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| PRED-001 | Predict Grade from Hours | 1. Add prediction row<br>2. Enter hours<br>3. Click Predict | Grade field populated with prediction | High |
| PRED-002 | Predict Hours from Grade | 1. Add prediction row<br>2. Enter target grade<br>3. Click Predict | Hours field populated with required time | High |
| PRED-003 | Prediction Consistency | 1. Enter 2 hours, predict<br>2. Clear, enter 2 hours again<br>3. Predict | Same result both times | Critical |
| PRED-004 | Insufficient Data | 1. Try to predict with no historical data | Appropriate message/fallback | Medium |

### 7.2 Prediction Accuracy Tests

| Test ID | Test Name | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| PRED-010 | k-Value Responds to Data | 1. Add several 100% grades with low hours<br>2. Predict | Higher prediction (learner is efficient) | High |
| PRED-011 | Category-Specific | 1. Have different performance in different categories<br>2. Predict for each | Predictions reflect category-specific history | High |
| PRED-012 | Excludes Predictions from History | 1. Make a prediction<br>2. Make another prediction | Second prediction doesn't include first in calculation | High |

### 7.3 Prediction to Assignment Conversion

| Test ID | Test Name | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| PRED-020 | Convert Prediction | 1. Create prediction<br>2. Click "Add" button | Converts to regular assignment, weights recalculated | High |
| PRED-021 | Stored Prediction Accuracy | 1. Create prediction<br>2. Convert to assignment<br>3. Enter actual grade | Prediction accuracy tracked (predicted vs actual) | Medium |
| PRED-022 | Delete Prediction | 1. Create prediction<br>2. Delete | Prediction removed, no weight impact | Medium |

---

## 8. Subject Predictor

### 8.1 Subject-Level Prediction Tests

| Test ID | Test Name | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| SPRJ-001 | Predict Remaining Weight | 1. Open subject predictor<br>2. Enter hours for remaining assessments | Predicted final grade calculated | High |
| SPRJ-002 | Show Predictions Toggle | 1. Toggle "Show Predictions" ON<br>2. Predict | Existing predictions included in calculation | Medium |
| SPRJ-003 | Hide Predictions Toggle | 1. Toggle "Show Predictions" OFF<br>2. Predict | Predictions excluded from calculation | Medium |
| SPRJ-004 | Grade Lock Interaction | 1. Set grade lock to 90<br>2. Predict | Predictions capped at 90 | Medium |

---

## 9. Statistics & Analytics

### 9.1 Stats Page Tests

| Test ID | Test Name | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| STAT-001 | Subject Statistics Display | 1. Navigate to /stats | All subjects with grades shown | High |
| STAT-002 | Average Grade Calculation | 1. Add grades<br>2. Check stats | Weighted average correctly calculated | High |
| STAT-003 | Total Hours Display | 1. Add assessments with hours<br>2. Check stats | Total hours summed correctly | Medium |
| STAT-004 | Filter by Subject | 1. Select subject from dropdown | Only that subject's stats shown | Medium |

### 9.2 Summary Row Tests

| Test ID | Test Name | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| STAT-010 | Summary Row Updates | 1. Add/edit assessment | Summary row recalculates | High |
| STAT-011 | Summary Accuracy | 1. Manual calculation<br>2. Compare to summary | Values match | High |

---

## 10. User Interface Features

### 10.1 Dark Mode Tests

| Test ID | Test Name | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| UI-001 | Toggle Dark Mode | 1. Click dark mode toggle | UI switches to dark theme | Low |
| UI-002 | Dark Mode Persistence | 1. Enable dark mode<br>2. Refresh page | Dark mode remains | Low |

### 10.2 Drag and Drop Tests

| Test ID | Test Name | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| UI-010 | Reorder Assessments | 1. Drag assessment row to new position | Order updated, persisted | Medium |
| UI-011 | Reorder Categories | 1. Drag category row | Order updated | Low |

### 10.3 Responsive Design Tests

| Test ID | Test Name | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| UI-020 | Mobile View | 1. Resize to mobile width | UI remains usable | Medium |
| UI-021 | Tablet View | 1. Resize to tablet width | UI adapts appropriately | Low |

### 10.4 Toast Notifications Tests

| Test ID | Test Name | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| UI-030 | Success Toast | 1. Save an assessment | Green success toast appears | Low |
| UI-031 | Error Toast | 1. Trigger an error | Red error toast appears | Low |
| UI-032 | Toast Auto-Dismiss | 1. Trigger toast | Toast disappears after timeout | Low |

---

## 11. Data Integrity & Edge Cases

### 11.1 Boundary Tests

| Test ID | Test Name | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| EDGE-001 | Grade = 0 | 1. Enter grade of 0 | Accepted, displayed correctly | Medium |
| EDGE-002 | Grade = 100 | 1. Enter grade of 100 | Accepted, included in predictions | Medium |
| EDGE-003 | Grade > 100 | 1. Try to enter 105% | Validation error OR accepted (extra credit) | Low |
| EDGE-004 | Hours = 0 | 1. Enter 0 hours | May be rejected or accepted | Low |
| EDGE-005 | Very Long Names | 1. Enter 200+ character assignment name | Truncated or accepted | Low |

### 11.2 Concurrent Modification Tests

| Test ID | Test Name | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| EDGE-010 | Edit Same Row Twice | 1. Open edit in two tabs<br>2. Save both | Last save wins, no crash | Medium |
| EDGE-011 | Delete While Editing | 1. Start editing<br>2. Delete same row in another tab | Graceful handling | Medium |

### 11.3 Data Recovery Tests

| Test ID | Test Name | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| EDGE-020 | Refresh During Add | 1. Start adding assessment<br>2. Refresh page | Unsaved data lost (expected), no errors | Medium |
| EDGE-021 | Network Error | 1. Disconnect network<br>2. Try to save | Error message, data not corrupted | Medium |

---

## 12. Performance Tests

### 12.1 Load Tests

| Test ID | Test Name | Steps | Expected Result | Priority |
|---------|-----------|-------|-----------------|----------|
| PERF-001 | Many Assessments | 1. Add 100+ assessments<br>2. Navigate | Page loads in < 3 seconds | Low |
| PERF-002 | Many Subjects | 1. Create 20+ subjects<br>2. Navigate | Sidebar loads quickly | Low |
| PERF-003 | Prediction Speed | 1. Have 100+ data points<br>2. Make prediction | Prediction returns in < 2 seconds | Medium |

---

## 13. Test Execution Summary

### 13.1 Test Priority Guide
- **Critical:** Must pass for release
- **High:** Should pass for release
- **Medium:** Nice to have passing
- **Low:** Can defer fixes

### 13.2 Test Count by Area

| Area | Critical | High | Medium | Low | Total |
|------|----------|------|--------|-----|-------|
| Authentication | 2 | 7 | 4 | 1 | 14 |
| Subject Management | 0 | 5 | 6 | 1 | 12 |
| Category Management | 0 | 5 | 5 | 0 | 10 |
| Assessment Management | 0 | 8 | 7 | 0 | 15 |
| Prediction System | 1 | 6 | 4 | 0 | 11 |
| Subject Predictor | 0 | 1 | 3 | 0 | 4 |
| Statistics | 0 | 2 | 2 | 0 | 4 |
| User Interface | 0 | 0 | 3 | 6 | 9 |
| Edge Cases | 0 | 0 | 5 | 4 | 9 |
| Performance | 0 | 0 | 1 | 2 | 3 |
| **Total** | **3** | **34** | **40** | **14** | **91** |

---

## 14. Appendix: Automated Test Files

### 14.1 Existing Test Files
- `tests/test_code.py` - Core CRUD and DB tests
- `tests/test_db_schema.py` - Database schema tests
- `tests/test_phase2.py` - Phase 2 feature tests
- `tests/test_phase3.py` - Phase 3 feature tests
- `tests/test_phase4.py` - Phase 4 feature tests
- `tests/test_phase5.py` - Phase 5 feature tests
- `tests/test_phase6.py` - Phase 6 feature tests
- `tests/test_phase7.py` - Phase 7 feature tests
- `tests/verify_auth.py` - Authentication verification
- `tests/verify_prediction.py` - Prediction verification
- `tests/verify_user_isolation.py` - User isolation tests

### 14.2 Running Automated Tests
```bash
# Run all tests
cd Project/src
python -m pytest ../tests/ -v

# Run specific test file
python -m pytest ../tests/test_phase7.py -v

# Run with coverage
python -m pytest ../tests/ --cov=. --cov-report=html
```

---

**Document Version History:**
| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Nov 12, 2025 | Team 21 | Initial test plan |
| 2.0 | Nov 30, 2025 | Team 21 | Comprehensive update with all features |
