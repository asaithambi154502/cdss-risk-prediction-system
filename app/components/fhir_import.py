"""
FHIR Import Component for CDSS

Provides UI for importing patient data from FHIR bundles
(file upload or sample data).
"""

import streamlit as st
import json
from typing import Optional, Dict
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import FHIR_CONFIG


def render_fhir_import_section(on_import_callback):
    """
    Render the FHIR data import section.
    
    Args:
        on_import_callback: Function to call with imported data (Dict)
    """
    st.markdown("### 📥 Import Patient Data (FHIR)")
    st.markdown("*Import structured patient data from FHIR R4 format*")
    
    tab1, tab2, tab3 = st.tabs(["📁 Upload File", "📋 Sample Data", "✍️ Manual JSON"])
    
    with tab1:
        render_file_upload(on_import_callback)
    
    with tab2:
        render_sample_data(on_import_callback)
    
    with tab3:
        render_manual_input(on_import_callback)


def render_file_upload(on_import_callback):
    """Render file upload interface for FHIR bundles."""
    st.markdown("#### Upload FHIR Bundle")
    
    uploaded_file = st.file_uploader(
        "Choose a FHIR JSON file",
        type=['json'],
        help="Upload a FHIR R4 Bundle containing patient data"
    )
    
    if uploaded_file is not None:
        try:
            content = uploaded_file.read().decode('utf-8')
            bundle = json.loads(content)
            
            # Validate it's a FHIR bundle
            if bundle.get('resourceType') != 'Bundle':
                st.error("❌ Invalid FHIR Bundle: resourceType must be 'Bundle'")
                return
            
            # Show preview
            st.success(f"✅ Valid FHIR Bundle loaded")
            
            entries = bundle.get('entry', [])
            resource_counts = {}
            for entry in entries:
                res_type = entry.get('resource', {}).get('resourceType', 'Unknown')
                resource_counts[res_type] = resource_counts.get(res_type, 0) + 1
            
            st.markdown("**Bundle Contents:**")
            for res_type, count in resource_counts.items():
                st.markdown(f"- {res_type}: {count}")
            
            if st.button("Import This Data", key="import_uploaded"):
                on_import_callback(bundle)
                st.success("✅ Data imported successfully!")
                
        except json.JSONDecodeError as e:
            st.error(f"❌ Invalid JSON: {e}")
        except Exception as e:
            st.error(f"❌ Error processing file: {e}")


def render_sample_data(on_import_callback):
    """Render sample data selection interface."""
    st.markdown("#### Use Sample Patient Data")
    st.markdown("Select a pre-configured sample patient for demonstration.")
    
    samples = {
        "sample_1": {
            "name": "John Doe - Elderly Diabetic",
            "description": "69-year-old male with Type 2 Diabetes and Hypertension",
            "data": get_sample_elderly_diabetic()
        },
        "sample_2": {
            "name": "Jane Smith - Young Healthy",
            "description": "32-year-old female with no significant medical history",
            "data": get_sample_young_healthy()
        },
        "sample_3": {
            "name": "Robert Johnson - Complex Case",
            "description": "75-year-old male with multiple comorbidities and polypharmacy",
            "data": get_sample_complex_case()
        }
    }
    
    selected = st.selectbox(
        "Select Sample Patient",
        options=list(samples.keys()),
        format_func=lambda x: samples[x]["name"]
    )
    
    if selected:
        sample = samples[selected]
        st.info(f"📋 {sample['description']}")
        
        with st.expander("Preview Bundle"):
            st.json(sample['data'])
        
        if st.button("Load Sample Data", key="load_sample"):
            on_import_callback(sample['data'])
            st.success(f"✅ Loaded: {sample['name']}")


def render_manual_input(on_import_callback):
    """Render manual JSON input interface."""
    st.markdown("#### Paste FHIR JSON")
    
    json_input = st.text_area(
        "Enter FHIR Bundle JSON:",
        height=300,
        placeholder='{"resourceType": "Bundle", "type": "collection", "entry": [...]}'
    )
    
    if st.button("Parse and Import", key="import_manual"):
        if not json_input.strip():
            st.warning("Please enter JSON data")
            return
        
        try:
            bundle = json.loads(json_input)
            
            if bundle.get('resourceType') != 'Bundle':
                st.error("❌ Invalid: resourceType must be 'Bundle'")
                return
            
            on_import_callback(bundle)
            st.success("✅ Data imported successfully!")
            
        except json.JSONDecodeError as e:
            st.error(f"❌ Invalid JSON: {e}")


def render_fhir_data_preview(fhir_patient_data):
    """
    Render a preview of imported FHIR data.
    
    Args:
        fhir_patient_data: FHIRPatientData object from converter
    """
    st.markdown("### 📊 Imported Patient Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Patient Demographics")
        st.markdown(f"**ID:** {fhir_patient_data.patient_id}")
        if fhir_patient_data.name:
            st.markdown(f"**Name:** {fhir_patient_data.name}")
        if fhir_patient_data.age:
            st.markdown(f"**Age:** {fhir_patient_data.age} years")
        if fhir_patient_data.gender:
            st.markdown(f"**Gender:** {fhir_patient_data.gender.title()}")
    
    with col2:
        st.markdown("#### Vital Signs")
        if fhir_patient_data.vitals:
            for vital, value in fhir_patient_data.vitals.items():
                display_name = vital.replace('_', ' ').title()
                st.markdown(f"**{display_name}:** {value}")
        else:
            st.markdown("_No vitals data_")
    
    st.markdown("---")
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown("#### Conditions")
        if fhir_patient_data.conditions:
            for condition in fhir_patient_data.conditions:
                st.markdown(f"- {condition.replace('_', ' ').title()}")
        else:
            st.markdown("_No conditions recorded_")
        
        st.markdown("#### Allergies")
        if fhir_patient_data.allergies:
            for allergy in fhir_patient_data.allergies:
                st.markdown(f"- ⚠️ {allergy.title()}")
        else:
            st.markdown("_No known allergies_")
    
    with col4:
        st.markdown("#### Medications")
        if fhir_patient_data.medications:
            for med in fhir_patient_data.medications:
                st.markdown(f"- 💊 {med.title()}")
        else:
            st.markdown("_No medications_")
        
        st.markdown("#### Symptoms")
        if fhir_patient_data.symptoms:
            for symptom in fhir_patient_data.symptoms:
                st.markdown(f"- {symptom.replace('_', ' ').title()}")
        else:
            st.markdown("_No symptoms noted_")


# Sample data generators
def get_sample_elderly_diabetic():
    """Generate sample FHIR bundle for elderly diabetic patient."""
    return {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": "elderly-diabetic-001",
                    "name": [{"given": ["John"], "family": "Doe"}],
                    "gender": "male",
                    "birthDate": "1956-05-15"
                }
            },
            {
                "resource": {
                    "resourceType": "Observation",
                    "code": {"coding": [{"system": "http://loinc.org", "code": "8867-4"}]},
                    "valueQuantity": {"value": 82, "unit": "beats/minute"}
                }
            },
            {
                "resource": {
                    "resourceType": "Observation",
                    "code": {"coding": [{"system": "http://loinc.org", "code": "8480-6"}]},
                    "valueQuantity": {"value": 142, "unit": "mmHg"}
                }
            },
            {
                "resource": {
                    "resourceType": "Observation",
                    "code": {"coding": [{"system": "http://loinc.org", "code": "2708-6"}]},
                    "valueQuantity": {"value": 96, "unit": "%"}
                }
            },
            {
                "resource": {
                    "resourceType": "Condition",
                    "code": {"text": "Type 2 Diabetes Mellitus"}
                }
            },
            {
                "resource": {
                    "resourceType": "Condition",
                    "code": {"text": "Essential Hypertension"}
                }
            },
            {
                "resource": {
                    "resourceType": "MedicationStatement",
                    "medicationCodeableConcept": {"text": "Metformin 500mg"}
                }
            },
            {
                "resource": {
                    "resourceType": "MedicationStatement",
                    "medicationCodeableConcept": {"text": "Lisinopril 10mg"}
                }
            }
        ]
    }


def get_sample_young_healthy():
    """Generate sample FHIR bundle for young healthy patient."""
    return {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": "young-healthy-001",
                    "name": [{"given": ["Jane"], "family": "Smith"}],
                    "gender": "female",
                    "birthDate": "1993-08-22"
                }
            },
            {
                "resource": {
                    "resourceType": "Observation",
                    "code": {"coding": [{"system": "http://loinc.org", "code": "8867-4"}]},
                    "valueQuantity": {"value": 72, "unit": "beats/minute"}
                }
            },
            {
                "resource": {
                    "resourceType": "Observation",
                    "code": {"coding": [{"system": "http://loinc.org", "code": "8480-6"}]},
                    "valueQuantity": {"value": 118, "unit": "mmHg"}
                }
            },
            {
                "resource": {
                    "resourceType": "Observation",
                    "code": {"coding": [{"system": "http://loinc.org", "code": "2708-6"}]},
                    "valueQuantity": {"value": 99, "unit": "%"}
                }
            }
        ]
    }


def get_sample_complex_case():
    """Generate sample FHIR bundle for complex case patient."""
    return {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": "complex-case-001",
                    "name": [{"given": ["Robert"], "family": "Johnson"}],
                    "gender": "male",
                    "birthDate": "1950-01-10"
                }
            },
            {
                "resource": {
                    "resourceType": "Observation",
                    "code": {"coding": [{"system": "http://loinc.org", "code": "8867-4"}]},
                    "valueQuantity": {"value": 95, "unit": "beats/minute"}
                }
            },
            {
                "resource": {
                    "resourceType": "Observation",
                    "code": {"coding": [{"system": "http://loinc.org", "code": "8480-6"}]},
                    "valueQuantity": {"value": 165, "unit": "mmHg"}
                }
            },
            {
                "resource": {
                    "resourceType": "Observation",
                    "code": {"coding": [{"system": "http://loinc.org", "code": "8310-5"}]},
                    "valueQuantity": {"value": 38.1, "unit": "Cel"}
                }
            },
            {
                "resource": {
                    "resourceType": "Observation",
                    "code": {"coding": [{"system": "http://loinc.org", "code": "2708-6"}]},
                    "valueQuantity": {"value": 91, "unit": "%"}
                }
            },
            {
                "resource": {
                    "resourceType": "Condition",
                    "code": {"text": "Type 2 Diabetes Mellitus"}
                }
            },
            {
                "resource": {
                    "resourceType": "Condition",
                    "code": {"text": "Chronic Heart Failure"}
                }
            },
            {
                "resource": {
                    "resourceType": "Condition",
                    "code": {"text": "Chronic Kidney Disease Stage 3"}
                }
            },
            {
                "resource": {
                    "resourceType": "MedicationStatement",
                    "medicationCodeableConcept": {"text": "Metformin 1000mg"}
                }
            },
            {
                "resource": {
                    "resourceType": "MedicationStatement",
                    "medicationCodeableConcept": {"text": "Furosemide 40mg"}
                }
            },
            {
                "resource": {
                    "resourceType": "MedicationStatement",
                    "medicationCodeableConcept": {"text": "Lisinopril 20mg"}
                }
            },
            {
                "resource": {
                    "resourceType": "MedicationStatement",
                    "medicationCodeableConcept": {"text": "Aspirin 81mg"}
                }
            },
            {
                "resource": {
                    "resourceType": "MedicationStatement",
                    "medicationCodeableConcept": {"text": "Warfarin 5mg"}
                }
            },
            {
                "resource": {
                    "resourceType": "MedicationStatement",
                    "medicationCodeableConcept": {"text": "Atorvastatin 40mg"}
                }
            },
            {
                "resource": {
                    "resourceType": "AllergyIntolerance",
                    "code": {"text": "Penicillin"}
                }
            }
        ]
    }
