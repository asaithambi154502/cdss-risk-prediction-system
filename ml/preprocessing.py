"""
Data Preprocessing Module for CDSS

Handles data cleaning, validation, and transformation of patient data
for machine learning model input.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import SYMPTOMS_LIST, VITAL_SIGNS, EXISTING_CONDITIONS


class DataPreprocessor:
    """Preprocesses patient data for ML model input."""
    
    def __init__(self):
        self.symptoms = SYMPTOMS_LIST
        self.vital_signs = VITAL_SIGNS
        self.conditions = [c for c in EXISTING_CONDITIONS if c != 'none']
        
    def validate_input(self, data: Dict) -> Tuple[bool, List[str]]:
        """
        Validate patient input data.
        
        Args:
            data: Dictionary containing patient data
            
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []
        
        # Validate age
        if 'age' not in data:
            errors.append("Age is required")
        elif not isinstance(data['age'], (int, float)) or data['age'] < 0 or data['age'] > 120:
            errors.append("Age must be between 0 and 120")
            
        # Validate gender
        if 'gender' not in data:
            errors.append("Gender is required")
        elif data['gender'] not in ['male', 'female', 'other']:
            errors.append("Gender must be 'male', 'female', or 'other'")
            
        # Validate vital signs
        for vital, ranges in self.vital_signs.items():
            if vital in data:
                value = data[vital]
                # Allow values outside normal range (they indicate abnormality)
                # but reject clearly invalid values
                if vital == 'heart_rate' and (value < 20 or value > 250):
                    errors.append(f"Heart rate must be between 20 and 250 bpm")
                elif vital == 'oxygen_saturation' and (value < 50 or value > 100):
                    errors.append(f"Oxygen saturation must be between 50 and 100%")
                elif vital == 'temperature' and (value < 30 or value > 45):
                    errors.append(f"Temperature must be between 30 and 45°C")
                    
        return len(errors) == 0, errors
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean the dataset by handling missing values and outliers.
        
        Args:
            df: Raw DataFrame
            
        Returns:
            Cleaned DataFrame
        """
        df_clean = df.copy()
        
        # Handle missing values
        # For symptoms and conditions, assume 0 (absent) if missing
        symptom_cols = [s for s in self.symptoms if s in df_clean.columns]
        condition_cols = [c for c in self.conditions if c in df_clean.columns]
        
        for col in symptom_cols + condition_cols:
            df_clean[col] = df_clean[col].fillna(0).astype(int)
            
        # For vital signs, fill with normal values (median)
        vital_cols = [v for v in self.vital_signs.keys() if v in df_clean.columns]
        for col in vital_cols:
            df_clean[col] = df_clean[col].fillna(df_clean[col].median())
            
        # Handle age
        if 'age' in df_clean.columns:
            df_clean['age'] = df_clean['age'].fillna(df_clean['age'].median())
            df_clean['age'] = df_clean['age'].clip(0, 120)
            
        # Handle gender
        if 'gender' in df_clean.columns:
            df_clean['gender'] = df_clean['gender'].fillna('unknown')
            
        return df_clean
    
    def normalize_vitals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize vital signs to 0-1 range based on clinical ranges.
        
        Args:
            df: DataFrame with vital sign columns
            
        Returns:
            DataFrame with normalized vital signs
        """
        df_norm = df.copy()
        
        normalization_ranges = {
            'heart_rate': (40, 180),
            'blood_pressure_systolic': (70, 200),
            'blood_pressure_diastolic': (40, 130),
            'temperature': (35, 41),
            'respiratory_rate': (8, 35),
            'oxygen_saturation': (80, 100)
        }
        
        for col, (min_val, max_val) in normalization_ranges.items():
            if col in df_norm.columns:
                df_norm[f'{col}_normalized'] = (df_norm[col] - min_val) / (max_val - min_val)
                df_norm[f'{col}_normalized'] = df_norm[f'{col}_normalized'].clip(0, 1)
                
        return df_norm
    
    def prepare_features(self, data: Dict) -> pd.DataFrame:
        """
        Convert patient data dictionary to feature DataFrame.
        
        Args:
            data: Patient data dictionary
            
        Returns:
            DataFrame ready for model prediction
        """
        # Create DataFrame from single record
        df = pd.DataFrame([data])
        
        # Clean data
        df = self.clean_data(df)
        
        # Encode gender
        if 'gender' in df.columns:
            df['gender_encoded'] = df['gender'].map({'male': 0, 'female': 1, 'other': 0.5})
        else:
            df['gender_encoded'] = 0.5
            
        # Normalize age (0-120 range)
        if 'age' in df.columns:
            df['age_normalized'] = df['age'] / 120.0
        else:
            df['age_normalized'] = 0.5
            
        # Normalize vital signs
        df = self.normalize_vitals(df)
        
        # Calculate symptom count
        symptom_cols = [s for s in self.symptoms if s in df.columns]
        df['symptom_count'] = df[symptom_cols].sum(axis=1)
        df['symptom_count_normalized'] = df['symptom_count'] / len(self.symptoms)
        
        # Calculate condition count
        condition_cols = [c for c in self.conditions if c in df.columns]
        if condition_cols:
            df['condition_count'] = df[condition_cols].sum(axis=1)
        else:
            df['condition_count'] = 0
            
        return df
    
    def get_feature_columns(self) -> List[str]:
        """Get list of feature columns used for model input."""
        features = [
            'age_normalized',
            'gender_encoded',
            'symptom_count_normalized',
            'condition_count'
        ]
        
        # Add individual symptoms
        features.extend(self.symptoms)
        
        # Add normalized vitals
        for vital in self.vital_signs.keys():
            features.append(f'{vital}_normalized')
            
        # Add conditions
        features.extend(self.conditions)
        
        return features
