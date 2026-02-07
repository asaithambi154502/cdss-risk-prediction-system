"""
Input Form Component for CDSS

Provides patient data input forms for the Streamlit application.
"""

import streamlit as st
from typing import Dict
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from cdss_config import (
    SYMPTOMS_LIST, VITAL_SIGNS, EXISTING_CONDITIONS,
    EXTENDED_VITAL_SIGNS, PAIN_SCORE_LABELS, GCS_INTERPRETATION, UI_STYLE
)





def render_patient_demographics() -> Dict:
    """Render patient demographics input form."""
    st.subheader("👤 Patient Demographics")
    
    # Patient and Doctor ID Row
    col_id1, col_id2 = st.columns(2)
    
    with col_id1:
        patient_id = st.text_input(
            "🆔 Patient ID",
            placeholder="Enter unique patient ID",
            help="Unique identifier for the patient"
        )
    
    with col_id2:
        doctor_id = st.text_input(
            "👨‍⚕️ Doctor ID",
            placeholder="Enter attending doctor ID",
            help="ID of the doctor performing the assessment"
        )
    
    # Age and Gender Row
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
    
    return {"patient_id": patient_id, "doctor_id": doctor_id, "age": age, "gender": gender}



def render_symptoms_form() -> Dict:
    """Render symptoms checklist form."""
    st.markdown(f"""
        <h2 style='color: #60a5fa; font-family: {UI_STYLE['primary_font']};'>🩺 Clinical Data Input</h2>
        <p style='color: {UI_STYLE['text_muted']}; font-size: 1.1rem; margin-bottom: 2rem;'>
            Please provide comprehensive patient data for high-accuracy clinical risk prediction.
        </p>
    """, unsafe_allow_html=True)
    
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


def get_vital_status(value: float, config: dict) -> tuple:
    """
    Determine the status of a vital sign value.
    
    Returns:
        Tuple of (status_emoji, status_text, status_color)
        🟢 = Normal, 🟡 = Warning, 🔴 = Critical
    """
    # Check for critical values first
    if 'critical_low' in config and value <= config['critical_low']:
        return "🔴", "Critical (Low)", "red"
    if 'critical_high' in config and value >= config['critical_high']:
        return "🔴", "Critical (High)", "red"
    
    # Check for warning values
    if 'warning_low' in config and value <= config['warning_low']:
        return "🟡", "Warning (Low)", "orange"
    if 'warning_high' in config and value >= config['warning_high']:
        return "🟡", "Warning (High)", "orange"
    
    # Check if within normal range
    normal_min = config.get('normal_min', float('-inf'))
    normal_max = config.get('normal_max', float('inf'))
    
    if normal_min <= value <= normal_max:
        return "🟢", "Normal", "green"
    else:
        return "🟡", "Abnormal", "orange"


def render_extended_vitals() -> Dict:
    """Render extended vital signs input form with visual status indicators."""
    st.subheader("📈 Extended Vital Signs")
    st.caption("Additional clinical indicators for comprehensive assessment")
    
    extended = {}
    
    # Row 1: Blood Sugar and Weight/Height/BMI
    col1, col2, col3 = st.columns(3)
    
    with col1:
        blood_sugar_config = EXTENDED_VITAL_SIGNS['blood_sugar']
        extended['blood_sugar'] = st.number_input(
            f"{blood_sugar_config['label']} ({blood_sugar_config['unit']})",
            min_value=blood_sugar_config['input_min'],
            max_value=blood_sugar_config['input_max'],
            value=blood_sugar_config['default'],
            help=blood_sugar_config['help']
        )
        # Show status indicator
        status_emoji, status_text, _ = get_vital_status(extended['blood_sugar'], blood_sugar_config)
        st.caption(f"{status_emoji} {status_text}")
    
    with col2:
        weight_config = EXTENDED_VITAL_SIGNS['body_weight']
        extended['body_weight'] = st.number_input(
            f"{weight_config['label']} ({weight_config['unit']})",
            min_value=float(weight_config['input_min']),
            max_value=float(weight_config['input_max']),
            value=float(weight_config['default']),
            step=0.5,
            help=weight_config['help']
        )
    
    with col3:
        height_config = EXTENDED_VITAL_SIGNS['height']
        extended['height'] = st.number_input(
            f"{height_config['label']} ({height_config['unit']})",
            min_value=float(height_config['input_min']),
            max_value=float(height_config['input_max']),
            value=float(height_config['default']),
            step=1.0,
            help=height_config['help']
        )
    
    # Calculate and display BMI
    if extended['height'] > 0:
        height_m = extended['height'] / 100
        extended['bmi'] = round(extended['body_weight'] / (height_m ** 2), 1)
        
        bmi_config = EXTENDED_VITAL_SIGNS['bmi']
        status_emoji, status_text, status_color = get_vital_status(extended['bmi'], bmi_config)
        
        st.markdown(f"""
        <div style="background-color: {'#d4edda' if status_color == 'green' else '#fff3cd' if status_color == 'orange' else '#f8d7da'}; 
                    padding: 10px; border-radius: 5px; margin: 5px 0;">
            <strong>📊 BMI: {extended['bmi']} {bmi_config['unit']}</strong> {status_emoji} {status_text}
        </div>
        """, unsafe_allow_html=True)
    else:
        extended['bmi'] = 0
    
    st.divider()
    
    # Row 2: Pain Score and Consciousness
    col1, col2 = st.columns(2)
    
    with col1:
        pain_config = EXTENDED_VITAL_SIGNS['pain_score']
        extended['pain_score'] = st.slider(
            f"{pain_config['label']} {pain_config['unit']}",
            min_value=pain_config['input_min'],
            max_value=pain_config['input_max'],
            value=pain_config['default'],
            help=pain_config['help']
        )
        # Show pain description and status
        pain_label = PAIN_SCORE_LABELS.get(extended['pain_score'], "Unknown")
        status_emoji, status_text, _ = get_vital_status(extended['pain_score'], pain_config)
        st.caption(f"{status_emoji} {pain_label} - {status_text}")
    
    with col2:
        gcs_config = EXTENDED_VITAL_SIGNS['consciousness_gcs']
        extended['consciousness_gcs'] = st.number_input(
            f"{gcs_config['label']} ({gcs_config['unit']})",
            min_value=gcs_config['input_min'],
            max_value=gcs_config['input_max'],
            value=gcs_config['default'],
            help=gcs_config['help']
        )
        # Show GCS interpretation
        gcs_val = extended['consciousness_gcs']
        gcs_interp = "Unknown"
        for (low, high), label in GCS_INTERPRETATION.items():
            if low <= gcs_val <= high:
                gcs_interp = label
                break
        status_emoji, status_text, _ = get_vital_status(gcs_val, gcs_config)
        st.caption(f"{status_emoji} {gcs_interp}")
    
    return extended


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
    
    # Extended Vital Signs
    with st.container():
        extended_vitals = render_extended_vitals()
        patient_data.update(extended_vitals)
    
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
    
    # Check extended vital signs
    blood_sugar = data.get('blood_sugar', 90)
    if blood_sugar < 50:
        errors.append("🔴 Critical: Dangerously low blood sugar (hypoglycemia)")
    elif blood_sugar > 200:
        errors.append("🔴 Critical: Very high blood sugar detected")
    elif blood_sugar < 70 or blood_sugar > 125:
        errors.append("⚠️ Warning: Abnormal blood sugar level")
    
    bmi = data.get('bmi', 22)
    if bmi < 15 or bmi > 40:
        errors.append("⚠️ Warning: BMI in critical range")
    
    pain_score = data.get('pain_score', 0)
    if pain_score >= 8:
        errors.append("🔴 Critical: Severe pain reported")
    elif pain_score >= 6:
        errors.append("⚠️ Warning: Significant pain reported")
    
    gcs = data.get('consciousness_gcs', 15)
    if gcs <= 8:
        errors.append("🔴 Critical: Severe consciousness impairment (GCS ≤ 8)")
    elif gcs <= 12:
        errors.append("⚠️ Warning: Consciousness impairment detected")
    
    return len([e for e in errors if not e.startswith("⚠️") and not e.startswith("🔴")]) == 0, errors
