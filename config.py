# CDSS Risk Prediction System Configuration

import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"

# Model configuration
MODEL_PATH = MODELS_DIR / "trained_model.joblib"
ENCODER_PATH = MODELS_DIR / "feature_encoder.joblib"

# Risk thresholds for classification
RISK_THRESHOLDS = {
    "low": 0.3,      # Below 30% probability
    "medium": 0.6,    # 30-60% probability
    "high": 1.0       # Above 60% probability
}

# Risk levels mapping
RISK_LEVELS = {
    0: "Low",
    1: "Medium", 
    2: "High"
}

# Risk colors for UI
RISK_COLORS = {
    "Low": "#28a745",      # Green
    "Medium": "#ffc107",   # Yellow/Amber
    "High": "#dc3545"      # Red
}

# Symptoms list for input form
SYMPTOMS_LIST = [
    "fever",
    "cough",
    "fatigue",
    "headache",
    "chest_pain",
    "shortness_of_breath",
    "nausea",
    "vomiting",
    "dizziness",
    "muscle_pain",
    "loss_of_appetite",
    "confusion"
]

# Vital signs ranges (normal values)
VITAL_SIGNS = {
    "heart_rate": {"min": 60, "max": 100, "unit": "bpm"},
    "blood_pressure_systolic": {"min": 90, "max": 120, "unit": "mmHg"},
    "blood_pressure_diastolic": {"min": 60, "max": 80, "unit": "mmHg"},
    "temperature": {"min": 36.1, "max": 37.2, "unit": "°C"},
    "respiratory_rate": {"min": 12, "max": 20, "unit": "breaths/min"},
    "oxygen_saturation": {"min": 95, "max": 100, "unit": "%"}
}

# Existing medical conditions
EXISTING_CONDITIONS = [
    "diabetes",
    "hypertension",
    "heart_disease",
    "asthma",
    "copd",
    "kidney_disease",
    "liver_disease",
    "cancer",
    "autoimmune_disorder",
    "none"
]

# Age groups for risk stratification
AGE_GROUPS = {
    "young": (0, 30),
    "adult": (31, 50),
    "middle_aged": (51, 65),
    "elderly": (66, 100)
}

# Alert settings
ALERT_CONFIG = {
    "show_low_risk": False,      # Don't show alerts for low risk (reduces alert fatigue)
    "show_medium_risk": True,    # Show warning for medium risk
    "show_high_risk": True       # Show critical alert for high risk
}

# Streamlit page configuration
PAGE_CONFIG = {
    "page_title": "CDSS - Medical Risk Prediction",
    "page_icon": "🏥",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}
