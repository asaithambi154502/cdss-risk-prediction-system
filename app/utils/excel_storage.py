"""
Excel Storage Module for CDSS

Handles saving and loading patient records to/from Excel files.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import os


# Excel file path - stored in data directory
DATA_DIR = Path(__file__).parent.parent.parent / "data"
EXCEL_FILE = DATA_DIR / "patient_records.xlsx"


def ensure_data_dir():
    """Ensure the data directory exists."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def get_record_columns() -> List[str]:
    """Return the standard column order for patient records."""
    return [
        "patient_id",
        "doctor_id",
        "timestamp",
        "age",
        "gender",
        "heart_rate",
        "blood_pressure_systolic",
        "blood_pressure_diastolic",
        "temperature",
        "oxygen_saturation",
        "respiratory_rate",
        "blood_sugar",
        "pain_score",
        "consciousness_gcs",
        "bmi",
        "symptoms",
        "conditions",
        "risk_level",
        "risk_score",
        "alert_generated"
    ]


def save_patient_record(
    patient_data: Dict,
    risk_level: str,
    risk_score: float,
    alert_generated: bool = False
) -> bool:
    """
    Save a patient record to the Excel file.
    
    Args:
        patient_data: Dictionary containing all patient form data
        risk_level: The predicted risk level (Low/Medium/High/Critical)
        risk_score: The probability/confidence score
        alert_generated: Whether an alert was triggered
        
    Returns:
        True if save was successful, False otherwise
    """
    try:
        ensure_data_dir()
        
        # Extract symptoms (fields with value 1 that are likely symptoms)
        symptom_fields = [
            'fever', 'cough', 'fatigue', 'difficulty_breathing', 'chest_pain',
            'headache', 'nausea', 'vomiting', 'diarrhea', 'muscle_pain',
            'joint_pain', 'sore_throat', 'runny_nose', 'loss_of_taste',
            'loss_of_smell', 'skin_rash', 'confusion', 'dizziness'
        ]
        symptoms = [s for s in symptom_fields if patient_data.get(s, 0) == 1]
        
        # Extract conditions
        condition_fields = [
            'diabetes', 'hypertension', 'heart_disease', 'asthma', 'copd',
            'kidney_disease', 'liver_disease', 'cancer', 'hiv_aids',
            'autoimmune_disease', 'obesity', 'smoking', 'pregnancy'
        ]
        conditions = [c for c in condition_fields if patient_data.get(c, 0) == 1]
        
        # Create record
        record = {
            "patient_id": patient_data.get("patient_id", ""),
            "doctor_id": patient_data.get("doctor_id", ""),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "age": patient_data.get("age", 0),
            "gender": patient_data.get("gender", ""),
            "heart_rate": patient_data.get("heart_rate", 0),
            "blood_pressure_systolic": patient_data.get("blood_pressure_systolic", 0),
            "blood_pressure_diastolic": patient_data.get("blood_pressure_diastolic", 0),
            "temperature": patient_data.get("temperature", 0),
            "oxygen_saturation": patient_data.get("oxygen_saturation", 0),
            "respiratory_rate": patient_data.get("respiratory_rate", 0),
            "blood_sugar": patient_data.get("blood_sugar", 0),
            "pain_score": patient_data.get("pain_score", 0),
            "consciousness_gcs": patient_data.get("consciousness_gcs", 15),
            "bmi": patient_data.get("bmi", 0),
            "symptoms": ", ".join(symptoms) if symptoms else "None",
            "conditions": ", ".join(conditions) if conditions else "None",
            "risk_level": risk_level,
            "risk_score": round(risk_score * 100, 2),  # Convert to percentage
            "alert_generated": "Yes" if alert_generated else "No"
        }
        
        # Load existing data or create new DataFrame
        if EXCEL_FILE.exists():
            df = pd.read_excel(EXCEL_FILE)
            # Append new record
            new_row = pd.DataFrame([record])
            df = pd.concat([df, new_row], ignore_index=True)
        else:
            df = pd.DataFrame([record])
        
        # Ensure column order
        columns = get_record_columns()
        for col in columns:
            if col not in df.columns:
                df[col] = ""
        df = df[columns]
        
        # Save to Excel
        df.to_excel(EXCEL_FILE, index=False, engine='openpyxl')
        
        return True
        
    except Exception as e:
        print(f"Error saving patient record: {e}")
        return False


def load_all_records() -> Optional[pd.DataFrame]:
    """
    Load all patient records from the Excel file.
    
    Returns:
        DataFrame with all records, or None if file doesn't exist
    """
    try:
        if EXCEL_FILE.exists():
            return pd.read_excel(EXCEL_FILE)
        return None
    except Exception as e:
        print(f"Error loading patient records: {e}")
        return None


def get_records_count() -> int:
    """Return the total number of patient records."""
    df = load_all_records()
    return len(df) if df is not None else 0


def get_excel_file_path() -> Path:
    """Return the path to the Excel file."""
    return EXCEL_FILE


def export_to_excel_bytes() -> Optional[bytes]:
    """
    Export records to Excel file bytes for download.
    
    Returns:
        Bytes of the Excel file, or None if no records exist
    """
    try:
        if not EXCEL_FILE.exists():
            return None
        
        with open(EXCEL_FILE, 'rb') as f:
            return f.read()
    except Exception as e:
        print(f"Error exporting Excel: {e}")
        return None
