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

# Extended vital signs with validation ranges
# Each vital has: input_min/max (allowed input), normal_min/max (healthy range), 
# warning thresholds, and critical thresholds
EXTENDED_VITAL_SIGNS = {
    "blood_sugar": {
        "label": "Blood Sugar (Fasting)",
        "unit": "mg/dL",
        "input_min": 20,
        "input_max": 600,
        "normal_min": 70,
        "normal_max": 100,
        "warning_low": 60,
        "warning_high": 125,
        "critical_low": 50,
        "critical_high": 200,
        "default": 90,
        "help": "Fasting blood glucose. Normal: 70-100 mg/dL"
    },
    "body_weight": {
        "label": "Body Weight",
        "unit": "kg",
        "input_min": 20,
        "input_max": 300,
        "default": 70,
        "help": "Patient weight in kilograms"
    },
    "height": {
        "label": "Height",
        "unit": "cm",
        "input_min": 100,
        "input_max": 250,
        "default": 170,
        "help": "Patient height in centimeters"
    },
    "bmi": {
        "label": "BMI",
        "unit": "kg/m²",
        "normal_min": 18.5,
        "normal_max": 24.9,
        "warning_low": 16,
        "warning_high": 30,
        "critical_low": 15,
        "critical_high": 40,
        "help": "Body Mass Index. Normal: 18.5-24.9 kg/m²"
    },
    "pain_score": {
        "label": "Pain Score",
        "unit": "/10",
        "input_min": 0,
        "input_max": 10,
        "normal_min": 0,
        "normal_max": 3,
        "warning_high": 6,
        "critical_high": 8,
        "default": 0,
        "help": "0=No pain, 1-3=Mild, 4-6=Moderate, 7-10=Severe"
    },
    "consciousness_gcs": {
        "label": "Consciousness (GCS)",
        "unit": "score",
        "input_min": 3,
        "input_max": 15,
        "normal_min": 15,
        "normal_max": 15,
        "warning_low": 13,
        "critical_low": 8,
        "default": 15,
        "help": "Glasgow Coma Scale. Normal: 15, Mild impairment: 13-14, Moderate: 9-12, Severe: 3-8"
    }
}

# Pain score labels for UI display
PAIN_SCORE_LABELS = {
    0: "No Pain",
    1: "Minimal",
    2: "Mild",
    3: "Uncomfortable",
    4: "Moderate",
    5: "Distracting",
    6: "Distressing",
    7: "Unmanageable",
    8: "Intense",
    9: "Severe",
    10: "Worst Possible"
}

# GCS interpretation
GCS_INTERPRETATION = {
    (15, 15): "Alert",
    (13, 14): "Mild Impairment",
    (9, 12): "Moderate Impairment",
    (3, 8): "Severe Impairment"
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

# Logging configuration
LOGS_DIR = BASE_DIR / "logs"

# Privacy disclaimer
PRIVACY_NOTICE = """
🔒 **Privacy Notice:** This system does not store patient personal identifiers. 
All patient data is processed in-session only and is not persisted. 
Prediction logs contain only anonymized clinical data for quality improvement purposes.
"""

# Streamlit page configuration
PAGE_CONFIG = {
    "page_title": "CDSS - Medical Risk Prediction",
    "page_icon": "🏥",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}
