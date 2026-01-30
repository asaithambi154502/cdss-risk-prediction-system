"""
Input Validation Utilities for CDSS

Provides validation functions for patient data input.
"""

from typing import Dict, List, Tuple
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from cdss_config import SYMPTOMS_LIST, VITAL_SIGNS, EXISTING_CONDITIONS


def validate_age(age: int) -> Tuple[bool, str]:
    """Validate patient age."""
    if age < 0:
        return False, "Age cannot be negative"
    if age > 120:
        return False, "Age must be 120 or less"
    return True, ""


def validate_vital_signs(vitals: Dict) -> Tuple[bool, List[str]]:
    """
    Validate vital signs values.
    
    Returns:
        Tuple of (all_valid, list of warning messages)
    """
    warnings = []
    
    # Heart rate checks
    hr = vitals.get('heart_rate', 75)
    if hr < 30 or hr > 220:
        return False, ["Heart rate is outside valid range (30-220 bpm)"]
    if hr < 50 or hr > 120:
        warnings.append(f"⚠️ Heart rate ({hr} bpm) is outside normal range (60-100 bpm)")
    
    # Blood pressure checks
    sys_bp = vitals.get('blood_pressure_systolic', 120)
    dia_bp = vitals.get('blood_pressure_diastolic', 80)
    
    if sys_bp < dia_bp:
        return False, ["Systolic BP must be greater than diastolic BP"]
    
    if sys_bp > 180 or sys_bp < 80:
        warnings.append(f"⚠️ Systolic BP ({sys_bp} mmHg) is significantly abnormal")
    
    if dia_bp > 120 or dia_bp < 50:
        warnings.append(f"⚠️ Diastolic BP ({dia_bp} mmHg) is significantly abnormal")
    
    # Temperature checks
    temp = vitals.get('temperature', 37.0)
    if temp < 34 or temp > 42:
        return False, ["Temperature is outside valid range (34-42°C)"]
    if temp > 38.0:
        warnings.append(f"⚠️ Elevated temperature ({temp}°C) indicates fever")
    if temp < 36.0:
        warnings.append(f"⚠️ Low temperature ({temp}°C) - hypothermia risk")
    
    # Oxygen saturation checks
    spo2 = vitals.get('oxygen_saturation', 98)
    if spo2 < 70 or spo2 > 100:
        return False, ["Oxygen saturation is outside valid range (70-100%)"]
    if spo2 < 92:
        warnings.append(f"🚨 Critical: Low oxygen saturation ({spo2}%)")
    elif spo2 < 95:
        warnings.append(f"⚠️ Low oxygen saturation ({spo2}%)")
    
    # Respiratory rate checks
    rr = vitals.get('respiratory_rate', 16)
    if rr < 6 or rr > 50:
        return False, ["Respiratory rate is outside valid range (6-50 breaths/min)"]
    if rr > 25:
        warnings.append(f"⚠️ Elevated respiratory rate ({rr} breaths/min)")
    if rr < 10:
        warnings.append(f"⚠️ Low respiratory rate ({rr} breaths/min)")
    
    return True, warnings


def validate_patient_data(data: Dict) -> Tuple[bool, List[str], List[str]]:
    """
    Comprehensive validation of all patient data.
    
    Args:
        data: Dictionary containing full patient data
        
    Returns:
        Tuple of (is_valid, list of errors, list of warnings)
    """
    errors = []
    warnings = []
    
    # Validate age
    is_valid, msg = validate_age(data.get('age', 0))
    if not is_valid:
        errors.append(msg)
    
    # Validate gender
    if data.get('gender') not in ['male', 'female', 'other']:
        errors.append("Invalid gender value")
    
    # Validate vital signs
    vital_keys = ['heart_rate', 'blood_pressure_systolic', 'blood_pressure_diastolic',
                  'temperature', 'respiratory_rate', 'oxygen_saturation']
    vitals = {k: data.get(k) for k in vital_keys if k in data}
    
    vitals_valid, vital_messages = validate_vital_signs(vitals)
    if not vitals_valid:
        errors.extend(vital_messages)
    else:
        warnings.extend(vital_messages)
    
    # Check symptom count for context
    symptom_count = sum(1 for s in SYMPTOMS_LIST if data.get(s, 0) == 1)
    if symptom_count >= 6:
        warnings.append(f"ℹ️ Multiple symptoms reported ({symptom_count})")
    
    # Check for high-risk symptom combinations
    critical_symptoms = ['chest_pain', 'shortness_of_breath', 'confusion']
    critical_count = sum(1 for s in critical_symptoms if data.get(s, 0) == 1)
    if critical_count >= 2:
        warnings.append("🚨 Multiple critical symptoms present")
    
    return len(errors) == 0, errors, warnings


def get_data_summary(data: Dict) -> Dict:
    """
    Get a summary of the patient data for display.
    
    Args:
        data: Patient data dictionary
        
    Returns:
        Dictionary with summary statistics
    """
    symptom_count = sum(1 for s in SYMPTOMS_LIST if data.get(s, 0) == 1)
    condition_count = sum(1 for c in EXISTING_CONDITIONS 
                         if c != 'none' and data.get(c, 0) == 1)
    
    symptoms_list = [s.replace('_', ' ').title() 
                     for s in SYMPTOMS_LIST if data.get(s, 0) == 1]
    conditions_list = [c.replace('_', ' ').title() 
                       for c in EXISTING_CONDITIONS 
                       if c != 'none' and data.get(c, 0) == 1]
    
    return {
        'age': data.get('age', 'N/A'),
        'gender': data.get('gender', 'N/A').title(),
        'symptom_count': symptom_count,
        'symptoms': symptoms_list,
        'condition_count': condition_count,
        'conditions': conditions_list if conditions_list else ['None reported'],
        'heart_rate': data.get('heart_rate', 'N/A'),
        'blood_pressure': f"{data.get('blood_pressure_systolic', 'N/A')}/{data.get('blood_pressure_diastolic', 'N/A')}",
        'temperature': data.get('temperature', 'N/A'),
        'oxygen_saturation': data.get('oxygen_saturation', 'N/A')
    }
