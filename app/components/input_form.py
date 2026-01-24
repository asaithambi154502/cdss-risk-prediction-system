"""
Input Form Component for CDSS

Provides patient data input forms for the Streamlit application.
"""

import streamlit as st
from typing import Dict
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import SYMPTOMS_LIST, VITAL_SIGNS, EXISTING_CONDITIONS


def render_patient_demographics() -> Dict:
    """Render patient demographics input form."""
    st.subheader("👤 Patient Demographics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        age = st.number_input(
            "Age",
            min_value=0,
            max_value=120,
            value=45,
            step=1,
            help="Patient's age in years"
        )
        
    with col2:
        gender = st.selectbox(
            "Gender",
            options=["male", "female", "other"],
            index=0,
            help="Patient's gender"
        )
    
    return {"age": age, "gender": gender}


def render_symptoms_form() -> Dict:
    """Render symptoms checklist form."""
    st.subheader("🩺 Symptoms")
    st.caption("Select all symptoms the patient is currently experiencing")
    
    symptoms = {}
    
    # Create a 3-column layout for symptoms
    cols = st.columns(3)
    
    for idx, symptom in enumerate(SYMPTOMS_LIST):
        col_idx = idx % 3
        with cols[col_idx]:
            symptom_label = symptom.replace("_", " ").title()
            symptoms[symptom] = 1 if st.checkbox(symptom_label, key=f"symptom_{symptom}") else 0
    
    return symptoms


def render_vital_signs() -> Dict:
    """Render vital signs input form."""
    st.subheader("📊 Vital Signs")
    
    vitals = {}
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        vitals['heart_rate'] = st.number_input(
            "Heart Rate (bpm)",
            min_value=30,
            max_value=220,
            value=75,
            help="Normal: 60-100 bpm"
        )
        
        vitals['temperature'] = st.number_input(
            "Temperature (°C)",
            min_value=34.0,
            max_value=42.0,
            value=37.0,
            step=0.1,
            format="%.1f",
            help="Normal: 36.1-37.2°C"
        )
    
    with col2:
        vitals['blood_pressure_systolic'] = st.number_input(
            "Blood Pressure - Systolic (mmHg)",
            min_value=60,
            max_value=220,
            value=120,
            help="Normal: 90-120 mmHg"
        )
        
        vitals['blood_pressure_diastolic'] = st.number_input(
            "Blood Pressure - Diastolic (mmHg)",
            min_value=40,
            max_value=140,
            value=80,
            help="Normal: 60-80 mmHg"
        )
    
    with col3:
        vitals['respiratory_rate'] = st.number_input(
            "Respiratory Rate (breaths/min)",
            min_value=6,
            max_value=50,
            value=16,
            help="Normal: 12-20 breaths/min"
        )
        
        vitals['oxygen_saturation'] = st.number_input(
            "Oxygen Saturation (%)",
            min_value=70,
            max_value=100,
            value=98,
            help="Normal: 95-100%"
        )
    
    return vitals


def render_medical_history() -> Dict:
    """Render medical history/existing conditions form."""
    st.subheader("📋 Medical History")
    st.caption("Select any pre-existing conditions")
    
    conditions = {}
    
    # Filter out 'none' from conditions list
    condition_list = [c for c in EXISTING_CONDITIONS if c != 'none']
    
    cols = st.columns(3)
    
    for idx, condition in enumerate(condition_list):
        col_idx = idx % 3
        with cols[col_idx]:
            condition_label = condition.replace("_", " ").title()
            conditions[condition] = 1 if st.checkbox(condition_label, key=f"condition_{condition}") else 0
    
    return conditions


def render_complete_form() -> Dict:
    """
    Render the complete patient input form.
    
    Returns:
        Dictionary containing all patient data
    """
    patient_data = {}
    
    # Demographics
    with st.container():
        demographics = render_patient_demographics()
        patient_data.update(demographics)
    
    st.divider()
    
    # Symptoms
    with st.container():
        symptoms = render_symptoms_form()
        patient_data.update(symptoms)
    
    st.divider()
    
    # Vital Signs
    with st.container():
        vitals = render_vital_signs()
        patient_data.update(vitals)
    
    st.divider()
    
    # Medical History
    with st.container():
        history = render_medical_history()
        patient_data.update(history)
    
    return patient_data


def validate_patient_data(data: Dict) -> tuple:
    """
    Validate patient data before prediction.
    
    Returns:
        Tuple of (is_valid, list of errors)
    """
    errors = []
    
    # Check age
    if data.get('age', 0) < 0 or data.get('age', 0) > 120:
        errors.append("Age must be between 0 and 120")
    
    # Check vital signs for critical values
    if data.get('oxygen_saturation', 100) < 85:
        errors.append("⚠️ Warning: Very low oxygen saturation detected")
    
    if data.get('heart_rate', 75) < 40 or data.get('heart_rate', 75) > 180:
        errors.append("⚠️ Warning: Abnormal heart rate detected")
    
    return len([e for e in errors if not e.startswith("⚠️")]) == 0, errors
