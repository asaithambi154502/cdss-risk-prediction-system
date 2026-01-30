# CDSS Risk Prediction System Configuration

import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"

# Professional UI Style Tokens
UI_STYLE = {
    "primary_font": "'Poppins', sans-serif",
    "secondary_font": "'Inter', sans-serif",
    "background_gradient": "linear-gradient(-45deg, #1e3a8a, #3b82f6, #0f172a, #1d4ed8)",
    "glass_bg": "rgba(255, 255, 255, 0.08)",
    "glass_border": "1px solid rgba(255, 255, 255, 0.12)",
    "glass_blur": "blur(20px)",
    "card_shadow": "0 8px 32px 0 rgba(0, 0, 0, 0.37)",
    "accent_color": "#60a5fa",
    "text_primary": "#f8fafc",
    "text_muted": "#94a3b8"
}

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

# Risk colors for UI - Professional Palette
RISK_COLORS = {
    "Low": "#00C853",      # Material Emerald Green
    "Medium": "#FFD600",   # Material Gold
    "High": "#FF1744"      # Material Vivid Red
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
    "page_title": "CDSS - Clinical Decision Support System",
    "page_icon": "🏥",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# EXPLAINABLE AI (XAI) CONFIGURATION
XAI_CONFIG = {
    "default_method": "shap",          # Options: "shap", "lime", "both"
    "top_features_count": 5,           # Number of top contributing factors to show
    "generate_on_demand": True,        # If True, only generate when user requests
    "shap_max_samples": 100,           # Max samples for SHAP background dataset
    "lime_num_features": 10,           # Number of features for LIME explanation
    "show_visualization": True,        # Show waterfall/bar charts
    "show_narrative": True,            # Show text-based explanations
}

# Feature display names for explanations
FEATURE_DISPLAY_NAMES = {
    "age": "Patient Age",
    "heart_rate": "Heart Rate",
    "blood_pressure_systolic": "Systolic Blood Pressure",
    "blood_pressure_diastolic": "Diastolic Blood Pressure",
    "temperature": "Body Temperature",
    "respiratory_rate": "Respiratory Rate",
    "oxygen_saturation": "Oxygen Saturation (SpO2)",
    "symptom_count": "Number of Symptoms",
    "num_medications": "Number of Medications",
    "fever": "Fever Present",
    "cough": "Cough Present",
    "fatigue": "Fatigue Present",
    "chest_pain": "Chest Pain",
    "shortness_of_breath": "Difficulty Breathing",
    "confusion": "Confusion/Altered Mental State",
    "blood_sugar": "Blood Sugar Level",
    "pain_score": "Pain Score",
    "consciousness_gcs": "Glasgow Coma Scale",
}

# SMART ALERT FATIGUE REDUCTION CONFIGURATION
ALERT_PRIORITY_CONFIG = {
    "levels": {
        "CRITICAL": {"color": "#dc3545", "icon": "🚨", "display_time": None, "sound": True},
        "HIGH": {"color": "#fd7e14", "icon": "⚠️", "display_time": 30, "sound": False},
        "MEDIUM": {"color": "#ffc107", "icon": "📋", "display_time": 15, "sound": False},
        "LOW": {"color": "#17a2b8", "icon": "ℹ️", "display_time": 5, "sound": False},
    },
    "suppression": {
        "min_interval_minutes": 15,
        "max_low_alerts_per_hour": 5,
        "suppress_repeated_low": True,
        "consecutive_threshold": 3,
    },
    "fatigue_tracking": {
        "alert_history_size": 100,
        "fatigue_threshold": 20,
        "auto_adjust_priority": True,
    }
}

# FHIR ELECTRONIC HEALTH RECORD (EHR) CONFIGURATION
FHIR_CONFIG = {
    "version": "R4",                       # FHIR version (R4 is most common)
    "base_url": None,                      # FHIR server URL (None = file-based only)
    "enable_server_mode": False,           # Enable FHIR server connectivity
    "sample_data_dir": BASE_DIR / "app" / "fhir" / "sample_bundles",
    "supported_resources": [
        "Patient",
        "Observation",
        "MedicationStatement",
        "Condition",
        "AllergyIntolerance",
        "Encounter"
    ],
    # Observation code mappings (LOINC codes)
    "observation_codes": {
        "heart_rate": "8867-4",
        "blood_pressure_systolic": "8480-6",
        "blood_pressure_diastolic": "8462-4",
        "temperature": "8310-5",
        "respiratory_rate": "9279-1",
        "oxygen_saturation": "2708-6",
        "blood_sugar": "2339-0",
    },
}

# UNIFIED MULTI-RISK PREDICTION ENGINE CONFIGURATION
MULTI_RISK_CONFIG = {
    "risk_types": {
        "medication_error": {
            "enabled": True,
            "weight": 0.30,
            "display_name": "Medication Error Risk",
            "icon": "💊",
            "color": "#e74c3c"
        },
        "disease_progression": {
            "enabled": True,
            "weight": 0.25,
            "display_name": "Disease Progression Risk",
            "icon": "🦠",
            "color": "#9b59b6"
        },
        "adverse_event": {
            "enabled": True,
            "weight": 0.25,
            "display_name": "Adverse Event Risk",
            "icon": "⚡",
            "color": "#f39c12"
        },
        "hospital_readmission": {
            "enabled": True,
            "weight": 0.20,
            "display_name": "Hospital Readmission Risk",
            "icon": "🏥",
            "color": "#3498db"
        },
    },
    "aggregation_method": "weighted_max",  # Options: "weighted_avg", "weighted_max", "highest"
    
    # Thresholds for each risk type (can be customized per risk)
    "default_thresholds": {
        "low": 0.3,
        "medium": 0.6,
        "high": 1.0
    }
}

# HYBRID INTELLIGENCE - CLINICAL RULES ENGINE CONFIGURATION
RULES_ENGINE_CONFIG = {
    "enable_rules": True,
    "rules_override_ml": False,           # If True, rules can override ML predictions
    "combine_method": "conservative",      # Options: "conservative", "liberal", "ml_priority"
    
    # Rule categories
    "rule_categories": {
        "drug_interactions": True,
        "vital_sign_alerts": True,
        "age_safety": True,
        "contraindications": True,
        "allergy_checks": True,
    }
}

# Drug interaction database (simplified - in production, use RxNorm or similar)
DRUG_INTERACTIONS = {
    # Severe interactions (will trigger CRITICAL alert)
    "severe": [
        {"drug1": "warfarin", "drug2": "aspirin", "effect": "Increased bleeding risk"},
        {"drug1": "metformin", "drug2": "contrast_dye", "effect": "Lactic acidosis risk"},
        {"drug1": "ssri", "drug2": "maoi", "effect": "Serotonin syndrome risk"},
        {"drug1": "digoxin", "drug2": "amiodarone", "effect": "Digoxin toxicity"},
        {"drug1": "ace_inhibitor", "drug2": "potassium", "effect": "Hyperkalemia risk"},
    ],
    # Moderate interactions (will trigger HIGH alert)
    "moderate": [
        {"drug1": "nsaid", "drug2": "ace_inhibitor", "effect": "Reduced antihypertensive effect"},
        {"drug1": "statin", "drug2": "grapefruit", "effect": "Increased statin levels"},
        {"drug1": "metformin", "drug2": "alcohol", "effect": "Hypoglycemia risk"},
        {"drug1": "antibiotic", "drug2": "antacid", "effect": "Reduced antibiotic absorption"},
    ],
    # Minor interactions (will trigger MEDIUM alert)
    "minor": [
        {"drug1": "caffeine", "drug2": "antibiotic", "effect": "Increased caffeine effect"},
    ]
}

# Vital sign critical thresholds for rules engine
VITAL_CRITICAL_RULES = {
    "heart_rate": {"critical_low": 40, "critical_high": 150},
    "blood_pressure_systolic": {"critical_low": 70, "critical_high": 200},
    "blood_pressure_diastolic": {"critical_low": 40, "critical_high": 120},
    "temperature": {"critical_low": 35.0, "critical_high": 40.0},
    "respiratory_rate": {"critical_low": 8, "critical_high": 30},
    "oxygen_saturation": {"critical_low": 88, "critical_high": 100},
    "blood_sugar": {"critical_low": 50, "critical_high": 400},
}

# Age-based medication safety rules
AGE_SAFETY_RULES = {
    "elderly_avoid": {
        "min_age": 65,
        "medications": ["benzodiazepines", "anticholinergics", "nsaid_long_term"],
        "reason": "Increased risk of falls, confusion, and adverse effects in elderly"
    },
    "pediatric_caution": {
        "max_age": 12,
        "medications": ["aspirin", "fluoroquinolones"],
        "reason": "Not recommended for pediatric patients"
    }
}

# Common medication list for the system
MEDICATION_LIST = [
    "aspirin", "warfarin", "metformin", "lisinopril", "amlodipine",
    "metoprolol", "atorvastatin", "omeprazole", "levothyroxine", "prednisone",
    "furosemide", "gabapentin", "hydrochlorothiazide", "losartan", "albuterol",
    "acetaminophen", "ibuprofen", "naproxen", "tramadol", "oxycodone",
    "amoxicillin", "azithromycin", "ciprofloxacin", "doxycycline", "metronidazole",
    "sertraline", "fluoxetine", "escitalopram", "duloxetine", "bupropion",
    "alprazolam", "lorazepam", "zolpidem", "trazodone", "quetiapine",
    "insulin", "glipizide", "sitagliptin", "empagliflozin", "liraglutide"
]
