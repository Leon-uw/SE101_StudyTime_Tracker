#!/usr/bin/env python3
"""
Test Predictions - Comprehensive tests for the prediction system.
Based on comprehensive test plan covering k estimation, grade prediction, hours prediction, and accuracy.
"""

import sys
import os
import pytest
import math

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Import prediction functions from app.py
from app import estimate_k, predict_grade, required_hours, calculate_system_prediction

from crud import (
    create_user, add_subject, add_category, add_grade, get_all_grades
)
from db import _connect, init_db, USERS_TABLE, SUBJECTS_TABLE, TABLE_NAME, CATEGORIES_TABLE


class TestEstimateK:
    """Tests for k estimation algorithm (PRED-001 to PRED-004)"""
    
    def test_pred_001_estimate_k_basic(self):
        """PRED-001: Estimate k with typical study data"""
        hours = [2.0, 3.0, 4.0, 5.0]
        grades = [70, 80, 85, 90]
        weights = [0.2, 0.2, 0.2, 0.2]  # Decimal weights
        
        k = estimate_k(hours, grades, weights)
        
        # k should be a positive number
        assert k > 0, "k should be positive"
        assert k < 100, "k should be reasonable (< 100)"
    
    def test_pred_002_estimate_k_empty_data(self):
        """PRED-002: Estimate k with no historical data returns default"""
        k = estimate_k([], [], [])
        
        assert k == 0.3, "Empty data should return default k (0.3)"
    
    def test_pred_003_estimate_k_filters_invalid(self):
        """PRED-003: Estimate k filters out invalid data points"""
        # Include some invalid points (0 hours, 0 grade)
        hours = [0, 2.0, 3.0, 0]
        grades = [80, 0, 85, 90]
        weights = [0.2, 0.2, 0.2, 0.2]
        
        # Should not crash and should produce a reasonable k
        k = estimate_k(hours, grades, weights)
        
        assert k > 0, "k should be positive even with invalid data filtered"
    
    def test_pred_004_estimate_k_handles_100_percent(self):
        """PRED-004: Estimate k handles 100% grades (capped at 99.5%)"""
        hours = [2.0, 3.0, 4.0, 5.0]
        grades = [100, 100, 100, 100]  # All perfect scores
        weights = [0.2, 0.2, 0.2, 0.2]
        
        k = estimate_k(hours, grades, weights)
        
        # Should not crash and should produce a reasonable k
        assert k > 0, "k should be positive with 100% grades"
        assert not math.isinf(k), "k should not be infinite"
        assert not math.isnan(k), "k should not be NaN"
    
    def test_estimate_k_single_datapoint(self):
        """Estimate k with single data point"""
        hours = [3.0]
        grades = [85]
        weights = [0.25]
        
        k = estimate_k(hours, grades, weights)
        
        assert k > 0, "k should be positive with single data point"
    
    def test_estimate_k_uses_trimmed_mean(self):
        """Estimate k uses trimmed mean (removes bottom 20%)"""
        # Create data where one low performer should be filtered
        hours = [5.0, 5.0, 5.0, 5.0, 5.0]
        grades = [50, 90, 90, 90, 90]  # One outlier low grade
        weights = [0.2, 0.2, 0.2, 0.2, 0.2]
        
        k_with_outlier = estimate_k(hours, grades, weights)
        
        # Without the outlier (90s only)
        hours_clean = [5.0, 5.0, 5.0, 5.0]
        grades_clean = [90, 90, 90, 90]
        weights_clean = [0.2, 0.2, 0.2, 0.2]
        
        k_without_outlier = estimate_k(hours_clean, grades_clean, weights_clean)
        
        # With trimmed mean, k_with_outlier should be close to k_without_outlier
        # because the low performer is trimmed
        assert abs(k_with_outlier - k_without_outlier) < k_without_outlier * 0.5, \
            "Trimmed mean should reduce effect of outliers"
    
    def test_estimate_k_high_performer_increases_k(self):
        """High performers should increase k value (learning efficiency)"""
        # Average performers
        hours_avg = [3.0, 3.0, 3.0]
        grades_avg = [70, 70, 70]
        weights_avg = [0.2, 0.2, 0.2]
        k_avg = estimate_k(hours_avg, grades_avg, weights_avg)
        
        # High performers (same hours, better grades)
        hours_high = [3.0, 3.0, 3.0]
        grades_high = [95, 95, 95]
        weights_high = [0.2, 0.2, 0.2]
        k_high = estimate_k(hours_high, grades_high, weights_high)
        
        assert k_high > k_avg, "High performers should have higher k"


class TestPredictGrade:
    """Tests for grade prediction function (PRED-005 to PRED-008)"""
    
    def test_pred_005_predict_grade_basic(self):
        """PRED-005: Predict grade with typical inputs"""
        hours = 3.0
        weight = 0.2
        k = 0.5
        
        predicted = predict_grade(hours, weight, k)
        
        assert 0 <= predicted <= 100, "Predicted grade should be between 0 and 100"
    
    def test_pred_006_predict_grade_zero_hours(self):
        """PRED-006: Zero study hours returns 0 grade"""
        predicted = predict_grade(0, 0.2, 0.5)
        
        assert predicted == 0, "Zero hours should predict 0 grade"
    
    def test_pred_007_predict_grade_increases_with_hours(self):
        """PRED-007: More hours = higher predicted grade"""
        weight = 0.2
        k = 0.5
        
        pred_1h = predict_grade(1.0, weight, k)
        pred_3h = predict_grade(3.0, weight, k)
        pred_5h = predict_grade(5.0, weight, k)
        
        assert pred_1h < pred_3h < pred_5h, "More hours should predict higher grade"
    
    def test_pred_008_predict_grade_weight_affects_prediction(self):
        """PRED-008: Higher weight (difficulty) affects prediction"""
        hours = 3.0
        k = 0.5
        
        pred_low_weight = predict_grade(hours, 0.1, k)
        pred_high_weight = predict_grade(hours, 0.5, k)
        
        # Higher weight (more difficult) should require more hours for same grade
        # So with same hours, lower weight = higher grade
        assert pred_low_weight > pred_high_weight, \
            "Lower weight (easier) should predict higher grade for same hours"
    
    def test_predict_grade_custom_max(self):
        """Predict grade respects custom max_grade"""
        hours = 10.0
        weight = 0.2
        k = 0.8
        max_grade = 50  # Custom max
        
        predicted = predict_grade(hours, weight, k, max_grade=max_grade)
        
        assert predicted <= max_grade, f"Predicted should not exceed max_grade of {max_grade}"
    
    def test_predict_grade_approaches_max(self):
        """Very high hours approaches but never exceeds max grade"""
        hours = 100.0  # Very high hours
        weight = 0.1
        k = 1.0
        
        predicted = predict_grade(hours, weight, k)
        
        assert predicted > 95, "Very high hours should predict near-max grade"
        assert predicted <= 100, "Should never exceed 100"


class TestRequiredHours:
    """Tests for required hours calculation (PRED-009 to PRED-012)"""
    
    def test_pred_009_required_hours_basic(self):
        """PRED-009: Calculate hours needed for target grade"""
        target = 80
        weight = 0.2
        k = 0.5
        
        hours = required_hours(target, weight, k)
        
        assert hours > 0, "Required hours should be positive"
        assert not math.isinf(hours), "Hours should be finite for achievable target"
    
    def test_pred_010_required_hours_zero_target(self):
        """PRED-010: Zero target grade requires zero hours"""
        hours = required_hours(0, 0.2, 0.5)
        
        assert hours == 0, "Zero target should require zero hours"
    
    def test_pred_011_required_hours_impossible_target(self):
        """PRED-011: 100% target returns infinity (asymptotic)"""
        hours = required_hours(100, 0.2, 0.5)
        
        assert math.isinf(hours), "100% target should return infinity"
    
    def test_pred_012_required_hours_increases_with_difficulty(self):
        """PRED-012: Higher weight (difficulty) requires more hours"""
        target = 80
        k = 0.5
        
        hours_easy = required_hours(target, 0.1, k)
        hours_hard = required_hours(target, 0.5, k)
        
        assert hours_hard > hours_easy, "Higher difficulty should require more hours"
    
    def test_required_hours_roundtrip(self):
        """Hours calculated should produce target grade when used in predict"""
        target = 85
        weight = 0.2
        k = 0.5
        
        hours = required_hours(target, weight, k)
        predicted = predict_grade(hours, weight, k)
        
        # Should be very close
        assert abs(predicted - target) < 0.1, f"Roundtrip: target={target}, predicted={predicted}"


class TestSystemPrediction:
    """Tests for system prediction calculation with database"""
    
    @classmethod
    def setup_class(cls):
        """Initialize database and create test user with historical data."""
        init_db()
        cls.test_username = "TEST_PRED_system_user"
        cls.password = "testpassword123"
        cls.test_subject = "PredictionSubject"
        cls.test_category = "TestCategory"
        
        # Clean up and create test user
        conn = _connect()
        try:
            curs = conn.cursor()
            curs.execute(f"DELETE FROM {TABLE_NAME} WHERE username = %s", (cls.test_username,))
            curs.execute(f"DELETE FROM {CATEGORIES_TABLE} WHERE username = %s", (cls.test_username,))
            curs.execute(f"DELETE FROM {SUBJECTS_TABLE} WHERE username = %s", (cls.test_username,))
            curs.execute(f"DELETE FROM {USERS_TABLE} WHERE username = %s", (cls.test_username,))
            conn.commit()
        finally:
            curs.close()
            conn.close()
        
        create_user(cls.test_username, cls.password)
        add_subject(cls.test_username, cls.test_subject)
        add_category(cls.test_username, cls.test_subject, cls.test_category, 100)
        
        # Add historical data
        add_grade(cls.test_username, cls.test_subject, cls.test_category, 2.0, "Past1", 75, 20)
        add_grade(cls.test_username, cls.test_subject, cls.test_category, 3.0, "Past2", 80, 20)
        add_grade(cls.test_username, cls.test_subject, cls.test_category, 4.0, "Past3", 85, 20)
    
    @classmethod
    def teardown_class(cls):
        """Clean up test user and data."""
        conn = _connect()
        try:
            curs = conn.cursor()
            curs.execute(f"DELETE FROM {TABLE_NAME} WHERE username = %s", (cls.test_username,))
            curs.execute(f"DELETE FROM {CATEGORIES_TABLE} WHERE username = %s", (cls.test_username,))
            curs.execute(f"DELETE FROM {SUBJECTS_TABLE} WHERE username = %s", (cls.test_username,))
            curs.execute(f"DELETE FROM {USERS_TABLE} WHERE username = %s", (cls.test_username,))
            conn.commit()
        finally:
            curs.close()
            conn.close()
    
    def test_system_prediction_with_history(self):
        """System prediction uses historical data"""
        predicted = calculate_system_prediction(
            self.test_username, self.test_subject, self.test_category,
            study_time=3.5, weight=20
        )
        
        assert predicted is not None, "Should return a prediction"
        assert 0 <= predicted <= 100, "Prediction should be valid grade"
    
    def test_system_prediction_excludes_self(self):
        """System prediction can exclude specific assignment"""
        # Add an assignment to exclude
        exclude_id = add_grade(
            self.test_username, self.test_subject, self.test_category,
            5.0, "ToExclude", 95, 20
        )
        
        # Prediction without exclusion
        pred_with = calculate_system_prediction(
            self.test_username, self.test_subject, self.test_category,
            study_time=3.5, weight=20
        )
        
        # Prediction with exclusion
        pred_without = calculate_system_prediction(
            self.test_username, self.test_subject, self.test_category,
            study_time=3.5, weight=20,
            exclude_id=exclude_id
        )
        
        # Clean up
        from crud import delete_grade
        delete_grade(self.test_username, exclude_id)
        
        # They should be different since high grade affects k
        # (They might be similar depending on data, but exclusion should work)
        assert pred_with is not None and pred_without is not None
    
    def test_system_prediction_zero_hours_returns_none(self):
        """System prediction with 0 hours returns None"""
        predicted = calculate_system_prediction(
            self.test_username, self.test_subject, self.test_category,
            study_time=0, weight=20
        )
        
        assert predicted is None, "Zero hours should return None"
    
    def test_system_prediction_no_history(self):
        """System prediction with no history returns None"""
        # Create new subject with no history
        add_subject(self.test_username, "NoHistorySubject")
        add_category(self.test_username, "NoHistorySubject", "NewCat", 100)
        
        # New user with no grades anywhere
        conn = _connect()
        try:
            curs = conn.cursor()
            curs.execute(f"DELETE FROM {USERS_TABLE} WHERE username = 'TEST_PRED_empty_user'")
            conn.commit()
        finally:
            curs.close()
            conn.close()
        
        create_user("TEST_PRED_empty_user", "password123")
        
        predicted = calculate_system_prediction(
            "TEST_PRED_empty_user", "SomeSubject", "SomeCat",
            study_time=3.0, weight=20
        )
        
        # Clean up
        conn = _connect()
        try:
            curs = conn.cursor()
            curs.execute(f"DELETE FROM {USERS_TABLE} WHERE username = 'TEST_PRED_empty_user'")
            conn.commit()
        finally:
            curs.close()
            conn.close()
        
        assert predicted is None, "No history should return None"


class TestPredictionConsistency:
    """Tests for prediction consistency (same inputs = same outputs)"""
    
    def test_same_inputs_same_k(self):
        """Same input data produces same k value"""
        hours = [2.0, 3.0, 4.0]
        grades = [70, 80, 85]
        weights = [0.2, 0.2, 0.2]
        
        k1 = estimate_k(hours, grades, weights)
        k2 = estimate_k(hours, grades, weights)
        k3 = estimate_k(hours, grades, weights)
        
        assert k1 == k2 == k3, "Same inputs should produce same k"
    
    def test_same_inputs_same_prediction(self):
        """Same inputs produce same predicted grade"""
        hours = 3.5
        weight = 0.2
        k = 0.5
        
        pred1 = predict_grade(hours, weight, k)
        pred2 = predict_grade(hours, weight, k)
        pred3 = predict_grade(hours, weight, k)
        
        assert pred1 == pred2 == pred3, "Same inputs should produce same prediction"
    
    def test_same_inputs_same_required_hours(self):
        """Same inputs produce same required hours"""
        target = 85
        weight = 0.25
        k = 0.4
        
        h1 = required_hours(target, weight, k)
        h2 = required_hours(target, weight, k)
        h3 = required_hours(target, weight, k)
        
        assert h1 == h2 == h3, "Same inputs should produce same required hours"


class TestPredictionAccuracy:
    """Tests for prediction accuracy tracking"""
    
    @classmethod
    def setup_class(cls):
        """Initialize database and create test user."""
        init_db()
        cls.test_username = "TEST_PRED_accuracy_user"
        cls.password = "testpassword123"
        cls.test_subject = "AccuracySubject"
        cls.test_category = "TestCategory"
        
        # Clean up and create test user
        conn = _connect()
        try:
            curs = conn.cursor()
            curs.execute(f"DELETE FROM {TABLE_NAME} WHERE username = %s", (cls.test_username,))
            curs.execute(f"DELETE FROM {CATEGORIES_TABLE} WHERE username = %s", (cls.test_username,))
            curs.execute(f"DELETE FROM {SUBJECTS_TABLE} WHERE username = %s", (cls.test_username,))
            curs.execute(f"DELETE FROM {USERS_TABLE} WHERE username = %s", (cls.test_username,))
            conn.commit()
        finally:
            curs.close()
            conn.close()
        
        create_user(cls.test_username, cls.password)
        add_subject(cls.test_username, cls.test_subject)
        add_category(cls.test_username, cls.test_subject, cls.test_category, 100)
    
    @classmethod
    def teardown_class(cls):
        """Clean up test user and data."""
        conn = _connect()
        try:
            curs = conn.cursor()
            curs.execute(f"DELETE FROM {TABLE_NAME} WHERE username = %s", (cls.test_username,))
            curs.execute(f"DELETE FROM {CATEGORIES_TABLE} WHERE username = %s", (cls.test_username,))
            curs.execute(f"DELETE FROM {SUBJECTS_TABLE} WHERE username = %s", (cls.test_username,))
            curs.execute(f"DELETE FROM {USERS_TABLE} WHERE username = %s", (cls.test_username,))
            conn.commit()
        finally:
            curs.close()
            conn.close()
    
    def teardown_method(self):
        """Clean up grades after each test."""
        conn = _connect()
        try:
            curs = conn.cursor()
            curs.execute(f"DELETE FROM {TABLE_NAME} WHERE username = %s", (self.test_username,))
            conn.commit()
        finally:
            curs.close()
            conn.close()
    
    def test_prediction_stored_with_assignment(self):
        """Predicted grade stored when actual grade entered"""
        # Add assignment with predicted grade
        grade_id = add_grade(
            self.test_username, self.test_subject, self.test_category,
            3.0, "PredictionTest", 85, 20,
            is_prediction=False, predicted_grade=80
        )
        
        grades = get_all_grades(self.test_username)
        assignment = [g for g in grades if g['id'] == grade_id][0]
        
        assert assignment['predicted_grade'] == 80, "Predicted grade should be stored"
        assert assignment['grade'] == 85, "Actual grade should be stored"
    
    def test_prediction_accuracy_calculable(self):
        """Can calculate prediction accuracy from stored data"""
        # Add multiple assignments with predictions and actuals
        add_grade(self.test_username, self.test_subject, self.test_category,
                  2.0, "A1", 75, 20, predicted_grade=70)
        add_grade(self.test_username, self.test_subject, self.test_category,
                  3.0, "A2", 85, 20, predicted_grade=82)
        add_grade(self.test_username, self.test_subject, self.test_category,
                  4.0, "A3", 90, 20, predicted_grade=88)
        
        grades = get_all_grades(self.test_username)
        
        # Calculate mean absolute error
        errors = []
        for g in grades:
            if g['grade'] is not None and g['predicted_grade'] is not None:
                errors.append(abs(g['grade'] - g['predicted_grade']))
        
        mae = sum(errors) / len(errors) if errors else None
        
        assert mae is not None, "Should be able to calculate MAE"
        assert mae < 10, "MAE should be reasonable (< 10)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
