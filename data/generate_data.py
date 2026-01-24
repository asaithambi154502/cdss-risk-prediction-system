"""
Sample Medical Dataset Generator for CDSS Training

This module generates a synthetic dataset with patient symptoms, clinical attributes,
and risk labels for training the medical error risk prediction model.
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path

# Ensure reproducibility
np.random.seed(42)

def generate_sample_data(n_samples: int = 1000) -> pd.DataFrame:
    """
    Generate synthetic medical dataset for training.
    
    Args:
        n_samples: Number of samples to generate
        
    Returns:
        DataFrame with patient data and risk labels
    """
    data = {
        # Demographics
        'age': np.random.randint(18, 90, n_samples),
        'gender': np.random.choice(['male', 'female'], n_samples),
        
        # Symptoms (binary: 0 = absent, 1 = present)
        'fever': np.random.choice([0, 1], n_samples, p=[0.6, 0.4]),
        'cough': np.random.choice([0, 1], n_samples, p=[0.5, 0.5]),
        'fatigue': np.random.choice([0, 1], n_samples, p=[0.4, 0.6]),
        'headache': np.random.choice([0, 1], n_samples, p=[0.5, 0.5]),
        'chest_pain': np.random.choice([0, 1], n_samples, p=[0.8, 0.2]),
        'shortness_of_breath': np.random.choice([0, 1], n_samples, p=[0.75, 0.25]),
        'nausea': np.random.choice([0, 1], n_samples, p=[0.65, 0.35]),
        'vomiting': np.random.choice([0, 1], n_samples, p=[0.8, 0.2]),
        'dizziness': np.random.choice([0, 1], n_samples, p=[0.7, 0.3]),
        'muscle_pain': np.random.choice([0, 1], n_samples, p=[0.55, 0.45]),
        'loss_of_appetite': np.random.choice([0, 1], n_samples, p=[0.6, 0.4]),
        'confusion': np.random.choice([0, 1], n_samples, p=[0.9, 0.1]),
        
        # Vital Signs
        'heart_rate': np.random.normal(80, 20, n_samples).clip(40, 180).astype(int),
        'blood_pressure_systolic': np.random.normal(120, 20, n_samples).clip(70, 200).astype(int),
        'blood_pressure_diastolic': np.random.normal(80, 15, n_samples).clip(40, 130).astype(int),
        'temperature': np.round(np.random.normal(37.0, 0.8, n_samples).clip(35.0, 41.0), 1),
        'respiratory_rate': np.random.normal(16, 4, n_samples).clip(8, 35).astype(int),
        'oxygen_saturation': np.random.normal(97, 3, n_samples).clip(80, 100).astype(int),
        
        # Medical History (binary: 0 = absent, 1 = present)
        'diabetes': np.random.choice([0, 1], n_samples, p=[0.85, 0.15]),
        'hypertension': np.random.choice([0, 1], n_samples, p=[0.75, 0.25]),
        'heart_disease': np.random.choice([0, 1], n_samples, p=[0.9, 0.1]),
        'asthma': np.random.choice([0, 1], n_samples, p=[0.92, 0.08]),
        'copd': np.random.choice([0, 1], n_samples, p=[0.95, 0.05]),
        'kidney_disease': np.random.choice([0, 1], n_samples, p=[0.93, 0.07]),
    }
    
    df = pd.DataFrame(data)
    
    # Calculate risk score based on multiple factors
    df['risk_score'] = calculate_risk_score(df)
    
    # Convert risk score to risk level (0: Low, 1: Medium, 2: High)
    df['risk_level'] = df['risk_score'].apply(categorize_risk)
    
    return df


def calculate_risk_score(df: pd.DataFrame) -> pd.Series:
    """
    Calculate a risk score based on patient attributes.
    
    This function simulates realistic risk patterns based on:
    - Age (elderly patients have higher risk)
    - Number and severity of symptoms
    - Abnormal vital signs
    - Pre-existing conditions
    """
    risk_score = np.zeros(len(df))
    
    # Age factor (higher risk for elderly)
    risk_score += np.where(df['age'] > 65, 0.15, 0)
    risk_score += np.where(df['age'] > 75, 0.1, 0)
    
    # Critical symptoms (higher weight)
    risk_score += df['chest_pain'] * 0.2
    risk_score += df['shortness_of_breath'] * 0.18
    risk_score += df['confusion'] * 0.22
    
    # Common symptoms
    risk_score += df['fever'] * 0.08
    risk_score += df['cough'] * 0.05
    risk_score += df['fatigue'] * 0.04
    risk_score += df['nausea'] * 0.05
    risk_score += df['vomiting'] * 0.08
    risk_score += df['dizziness'] * 0.07
    
    # Abnormal vital signs
    risk_score += np.where((df['heart_rate'] < 50) | (df['heart_rate'] > 110), 0.12, 0)
    risk_score += np.where((df['blood_pressure_systolic'] < 90) | (df['blood_pressure_systolic'] > 160), 0.1, 0)
    risk_score += np.where(df['temperature'] > 38.5, 0.1, 0)
    risk_score += np.where(df['oxygen_saturation'] < 92, 0.2, 0)
    risk_score += np.where(df['respiratory_rate'] > 24, 0.12, 0)
    
    # Pre-existing conditions
    risk_score += df['diabetes'] * 0.08
    risk_score += df['hypertension'] * 0.07
    risk_score += df['heart_disease'] * 0.15
    risk_score += df['copd'] * 0.12
    risk_score += df['kidney_disease'] * 0.1
    
    # Add some random noise
    risk_score += np.random.normal(0, 0.05, len(df))
    
    # Clip to [0, 1] range
    return np.clip(risk_score, 0, 1)


def categorize_risk(score: float) -> int:
    """Categorize risk score into Low (0), Medium (1), or High (2)."""
    if score < 0.3:
        return 0  # Low
    elif score < 0.6:
        return 1  # Medium
    else:
        return 2  # High


def save_dataset(df: pd.DataFrame, filepath: str) -> None:
    """Save dataset to CSV file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df.to_csv(filepath, index=False)
    print(f"Dataset saved to: {filepath}")
    print(f"Total samples: {len(df)}")
    print(f"Risk distribution:\n{df['risk_level'].value_counts().sort_index()}")


if __name__ == "__main__":
    # Generate and save sample dataset
    base_dir = Path(__file__).parent.parent
    
    # Generate training data
    train_data = generate_sample_data(n_samples=1000)
    save_dataset(train_data, str(base_dir / "data" / "processed" / "training_data.csv"))
    
    # Generate smaller test data
    test_data = generate_sample_data(n_samples=200)
    save_dataset(test_data, str(base_dir / "data" / "processed" / "test_data.csv"))
    
    print("\n✅ Sample datasets generated successfully!")
