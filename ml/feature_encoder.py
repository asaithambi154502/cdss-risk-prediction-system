"""
Feature Encoder Module for CDSS

Handles encoding of patient symptoms and clinical data into
machine-readable format for ML model input.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import joblib
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import SYMPTOMS_LIST, VITAL_SIGNS, EXISTING_CONDITIONS


class FeatureEncoder:
    """Encodes patient features for ML model input."""
    
    def __init__(self):
        self.symptoms = SYMPTOMS_LIST
        self.vital_signs = list(VITAL_SIGNS.keys())
        self.conditions = [c for c in EXISTING_CONDITIONS if c != 'none']
        self.feature_names = self._build_feature_names()
        self.is_fitted = False
        
    def _build_feature_names(self) -> List[str]:
        """Build list of all feature names."""
        features = [
            'age_normalized',
            'gender_encoded',
            'symptom_count_normalized',
            'condition_count'
        ]
        features.extend(self.symptoms)
        features.extend([f'{v}_normalized' for v in self.vital_signs])
        features.extend(self.conditions)
        return features
    
    def fit(self, df: pd.DataFrame) -> 'FeatureEncoder':
        """
        Fit the encoder on training data.
        Currently stores feature statistics for future use.
        
        Args:
            df: Training DataFrame
            
        Returns:
            self
        """
        self.is_fitted = True
        return self
    
    def transform(self, df: pd.DataFrame) -> np.ndarray:
        """
        Transform DataFrame to feature matrix.
        
        Args:
            df: DataFrame with patient data
            
        Returns:
            NumPy array of features
        """
        # Ensure all required columns exist
        for col in self.feature_names:
            if col not in df.columns:
                df[col] = 0
                
        # Select features in correct order
        X = df[self.feature_names].values
        
        # Replace NaN with 0
        X = np.nan_to_num(X, nan=0.0)
        
        return X
    
    def fit_transform(self, df: pd.DataFrame) -> np.ndarray:
        """Fit and transform in one step."""
        self.fit(df)
        return self.transform(df)
    
    def encode_patient(self, patient_data: Dict) -> np.ndarray:
        """
        Encode single patient data for prediction.
        
        Args:
            patient_data: Dictionary with patient information
            
        Returns:
            Feature array for model input
        """
        features = []
        
        # Age (normalized to 0-1)
        age = patient_data.get('age', 40)
        features.append(age / 120.0)
        
        # Gender encoded
        gender = patient_data.get('gender', 'other')
        gender_map = {'male': 0, 'female': 1, 'other': 0.5}
        features.append(gender_map.get(gender, 0.5))
        
        # Symptom count normalized
        symptom_values = [patient_data.get(s, 0) for s in self.symptoms]
        symptom_count = sum(symptom_values)
        features.append(symptom_count / len(self.symptoms))
        
        # Condition count
        condition_values = [patient_data.get(c, 0) for c in self.conditions]
        features.append(sum(condition_values))
        
        # Individual symptoms
        features.extend(symptom_values)
        
        # Normalized vital signs
        vital_ranges = {
            'heart_rate': (40, 180),
            'blood_pressure_systolic': (70, 200),
            'blood_pressure_diastolic': (40, 130),
            'temperature': (35, 41),
            'respiratory_rate': (8, 35),
            'oxygen_saturation': (80, 100)
        }
        
        for vital in self.vital_signs:
            value = patient_data.get(vital, None)
            if value is not None:
                min_v, max_v = vital_ranges.get(vital, (0, 100))
                normalized = (value - min_v) / (max_v - min_v)
                features.append(max(0, min(1, normalized)))
            else:
                features.append(0.5)  # Default to middle if missing
                
        # Conditions
        features.extend(condition_values)
        
        return np.array(features).reshape(1, -1)
    
    def get_feature_importance_labels(self) -> List[str]:
        """Get human-readable labels for feature importance display."""
        labels = [
            'Age',
            'Gender',
            'Total Symptoms',
            'Pre-existing Conditions'
        ]
        labels.extend([s.replace('_', ' ').title() for s in self.symptoms])
        labels.extend([v.replace('_', ' ').title() for v in self.vital_signs])
        labels.extend([c.replace('_', ' ').title() for c in self.conditions])
        return labels
    
    def save(self, filepath: str) -> None:
        """Save encoder to file."""
        joblib.dump(self, filepath)
        
    @classmethod
    def load(cls, filepath: str) -> 'FeatureEncoder':
        """Load encoder from file."""
        return joblib.load(filepath)
