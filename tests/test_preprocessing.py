"""
Tests for ML Preprocessing Module
"""

import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ml.preprocessing import DataPreprocessor


class TestDataPreprocessor:
    """Test cases for DataPreprocessor class."""
    
    @pytest.fixture
    def preprocessor(self):
        """Create a preprocessor instance."""
        return DataPreprocessor()
    
    @pytest.fixture
    def sample_patient_data(self):
        """Create sample patient data."""
        return {
            'age': 45,
            'gender': 'male',
            'fever': 1,
            'cough': 1,
            'fatigue': 0,
            'headache': 0,
            'chest_pain': 0,
            'shortness_of_breath': 0,
            'nausea': 0,
            'vomiting': 0,
            'dizziness': 0,
            'muscle_pain': 1,
            'loss_of_appetite': 0,
            'confusion': 0,
            'heart_rate': 85,
            'blood_pressure_systolic': 125,
            'blood_pressure_diastolic': 82,
            'temperature': 37.5,
            'respiratory_rate': 18,
            'oxygen_saturation': 97,
            'diabetes': 0,
            'hypertension': 1,
            'heart_disease': 0,
            'asthma': 0,
            'copd': 0,
            'kidney_disease': 0
        }
    
    def test_validate_input_valid_data(self, preprocessor, sample_patient_data):
        """Test validation with valid data."""
        is_valid, errors = preprocessor.validate_input(sample_patient_data)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_input_invalid_age(self, preprocessor):
        """Test validation with invalid age."""
        data = {'age': 150, 'gender': 'male'}
        is_valid, errors = preprocessor.validate_input(data)
        assert is_valid is False
        assert any('age' in e.lower() for e in errors)
    
    def test_validate_input_missing_age(self, preprocessor):
        """Test validation with missing age."""
        data = {'gender': 'male'}
        is_valid, errors = preprocessor.validate_input(data)
        assert is_valid is False
    
    def test_clean_data(self, preprocessor):
        """Test data cleaning."""
        df = pd.DataFrame([{
            'age': 45,
            'gender': 'male',
            'fever': None,  # Missing value
            'heart_rate': 85
        }])
        
        cleaned = preprocessor.clean_data(df)
        
        # Fever should be filled with 0
        assert cleaned['fever'].iloc[0] == 0
    
    def test_prepare_features(self, preprocessor, sample_patient_data):
        """Test feature preparation."""
        features = preprocessor.prepare_features(sample_patient_data)
        
        # Check that key columns exist
        assert 'age_normalized' in features.columns
        assert 'gender_encoded' in features.columns
        assert 'symptom_count' in features.columns
    
    def test_age_normalization(self, preprocessor):
        """Test that age is correctly normalized."""
        data = {'age': 60, 'gender': 'female'}
        features = preprocessor.prepare_features(data)
        
        # Age 60 should be normalized to 60/120 = 0.5
        assert abs(features['age_normalized'].iloc[0] - 0.5) < 0.01
    
    def test_gender_encoding(self, preprocessor):
        """Test gender encoding."""
        male_data = {'age': 30, 'gender': 'male'}
        female_data = {'age': 30, 'gender': 'female'}
        
        male_features = preprocessor.prepare_features(male_data)
        female_features = preprocessor.prepare_features(female_data)
        
        assert male_features['gender_encoded'].iloc[0] == 0
        assert female_features['gender_encoded'].iloc[0] == 1


class TestVitalSignsNormalization:
    """Test vital signs normalization."""
    
    @pytest.fixture
    def preprocessor(self):
        return DataPreprocessor()
    
    def test_normalize_heart_rate(self, preprocessor):
        """Test heart rate normalization."""
        df = pd.DataFrame([{'heart_rate': 110}])  # Middle of range
        normalized = preprocessor.normalize_vitals(df)
        
        # Should be normalized between 0 and 1
        assert 0 <= normalized['heart_rate_normalized'].iloc[0] <= 1
    
    def test_normalize_oxygen_saturation(self, preprocessor):
        """Test oxygen saturation normalization."""
        df = pd.DataFrame([{'oxygen_saturation': 95}])
        normalized = preprocessor.normalize_vitals(df)
        
        # 95% O2 sat should give a normalized value
        assert 'oxygen_saturation_normalized' in normalized.columns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
