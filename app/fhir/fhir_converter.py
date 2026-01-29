"""
FHIR Data Converter for CDSS

Converts between FHIR R4 resources and the internal CDSS data format.
Enables interoperability with Electronic Health Record (EHR) systems.
"""

import json
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import FHIR_CONFIG, VITAL_SIGNS, SYMPTOMS_LIST, EXISTING_CONDITIONS


@dataclass
class FHIRPatientData:
    """Structured patient data extracted from FHIR resources."""
    patient_id: str
    name: Optional[str]
    birth_date: Optional[date]
    age: Optional[int]
    gender: Optional[str]
    vitals: Dict[str, float]
    symptoms: List[str]
    conditions: List[str]
    medications: List[str]
    allergies: List[str]
    observations: Dict[str, Any]
    raw_resources: Dict[str, List[Dict]]
    
    def to_prediction_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for risk prediction models."""
        result = {
            'age': self.age or 50,
            'num_medications': len(self.medications),
            'symptom_count': len(self.symptoms),
            'medications': self.medications,
            'allergies': self.allergies
        }
        
        # Add vitals with defaults
        vital_defaults = {
            'heart_rate': 75,
            'blood_pressure_systolic': 120,
            'blood_pressure_diastolic': 80,
            'temperature': 37.0,
            'respiratory_rate': 16,
            'oxygen_saturation': 98
        }
        for vital, default in vital_defaults.items():
            result[vital] = self.vitals.get(vital, default)
        
        # Add condition flags
        for condition in self.conditions:
            result[f'condition_{condition}'] = 1
        
        return result


class FHIRConverter:
    """
    Converts between FHIR resources and internal CDSS data format.
    
    Supports FHIR R4 format for:
    - Patient demographics
    - Observations (vitals, lab results)
    - Conditions (diagnoses, medical history)
    - MedicationStatements
    - AllergyIntolerance
    """
    
    def __init__(self):
        self.config = FHIR_CONFIG
        self.observation_codes = self.config['observation_codes']
        self._reverse_observation_codes = {
            v: k for k, v in self.observation_codes.items()
        }
    
    def from_bundle(self, bundle: Dict) -> FHIRPatientData:
        """
        Extract patient data from a FHIR Bundle.
        
        Args:
            bundle: FHIR Bundle resource (as dictionary)
            
        Returns:
            FHIRPatientData object with extracted information
        """
        if bundle.get('resourceType') != 'Bundle':
            raise ValueError("Input must be a FHIR Bundle resource")
        
        entries = bundle.get('entry', [])
        
        # Initialize containers
        patient_data = None
        observations = []
        conditions = []
        medications = []
        allergies = []
        
        # Sort resources by type
        for entry in entries:
            resource = entry.get('resource', {})
            resource_type = resource.get('resourceType')
            
            if resource_type == 'Patient':
                patient_data = resource
            elif resource_type == 'Observation':
                observations.append(resource)
            elif resource_type == 'Condition':
                conditions.append(resource)
            elif resource_type == 'MedicationStatement':
                medications.append(resource)
            elif resource_type == 'AllergyIntolerance':
                allergies.append(resource)
        
        # Extract data from each resource type
        patient_info = self._parse_patient(patient_data) if patient_data else {}
        vitals, obs_data = self._parse_observations(observations)
        condition_list = self._parse_conditions(conditions)
        medication_list = self._parse_medications(medications)
        allergy_list = self._parse_allergies(allergies)
        
        # Infer symptoms from observations and conditions
        symptoms = self._infer_symptoms(obs_data, condition_list)
        
        return FHIRPatientData(
            patient_id=patient_info.get('id', 'unknown'),
            name=patient_info.get('name'),
            birth_date=patient_info.get('birth_date'),
            age=patient_info.get('age'),
            gender=patient_info.get('gender'),
            vitals=vitals,
            symptoms=symptoms,
            conditions=condition_list,
            medications=medication_list,
            allergies=allergy_list,
            observations=obs_data,
            raw_resources={
                'Patient': [patient_data] if patient_data else [],
                'Observation': observations,
                'Condition': conditions,
                'MedicationStatement': medications,
                'AllergyIntolerance': allergies
            }
        )
    
    # Alias for backwards compatibility
    def bundle_to_patient_data(self, bundle: Dict) -> FHIRPatientData:
        """Alias for from_bundle method."""
        return self.from_bundle(bundle)
    
    def _parse_patient(self, patient: Dict) -> Dict:
        """Extract patient demographics from Patient resource."""
        result = {
            'id': patient.get('id', 'unknown')
        }
        
        # Parse name
        names = patient.get('name', [])
        if names:
            name = names[0]
            given = ' '.join(name.get('given', []))
            family = name.get('family', '')
            result['name'] = f"{given} {family}".strip()
        
        # Parse birth date and calculate age
        birth_date_str = patient.get('birthDate')
        if birth_date_str:
            try:
                birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
                result['birth_date'] = birth_date
                today = date.today()
                age = today.year - birth_date.year
                if (today.month, today.day) < (birth_date.month, birth_date.day):
                    age -= 1
                result['age'] = age
            except ValueError:
                pass
        
        # Parse gender
        result['gender'] = patient.get('gender')
        
        return result
    
    def _parse_observations(self, observations: List[Dict]) -> tuple:
        """
        Extract vital signs and other observations.
        
        Returns:
            Tuple of (vitals dict, all observations dict)
        """
        vitals = {}
        all_obs = {}
        
        for obs in observations:
            code_info = obs.get('code', {})
            codings = code_info.get('coding', [])
            
            # Try to find LOINC code
            loinc_code = None
            display = None
            for coding in codings:
                if coding.get('system') == 'http://loinc.org':
                    loinc_code = coding.get('code')
                    display = coding.get('display')
                    break
            
            if not loinc_code and codings:
                loinc_code = codings[0].get('code')
                display = codings[0].get('display')
            
            # Extract value
            value = None
            if 'valueQuantity' in obs:
                value = obs['valueQuantity'].get('value')
            elif 'valueCodeableConcept' in obs:
                value = obs['valueCodeableConcept'].get('text')
            elif 'valueString' in obs:
                value = obs['valueString']
            elif 'valueBoolean' in obs:
                value = obs['valueBoolean']
            
            # Map to internal vital sign name
            vital_name = self._reverse_observation_codes.get(loinc_code)
            
            if vital_name and value is not None:
                vitals[vital_name] = value
            
            # Store all observations
            if loinc_code:
                all_obs[loinc_code] = {
                    'code': loinc_code,
                    'display': display,
                    'value': value,
                    'unit': obs.get('valueQuantity', {}).get('unit'),
                    'effective_datetime': obs.get('effectiveDateTime')
                }
        
        return vitals, all_obs
    
    def _parse_conditions(self, conditions: List[Dict]) -> List[str]:
        """Extract condition names from Condition resources."""
        condition_list = []
        
        for cond in conditions:
            code_info = cond.get('code', {})
            text = code_info.get('text')
            
            if text:
                # Map to internal condition names
                mapped = self._map_condition(text)
                if mapped:
                    condition_list.append(mapped)
            else:
                # Try to get from coding display
                codings = code_info.get('coding', [])
                for coding in codings:
                    display = coding.get('display')
                    if display:
                        mapped = self._map_condition(display)
                        if mapped:
                            condition_list.append(mapped)
                        break
        
        return list(set(condition_list))  # Remove duplicates
    
    def _map_condition(self, condition_text: str) -> Optional[str]:
        """Map FHIR condition text to internal condition name."""
        text_lower = condition_text.lower()
        
        mappings = {
            'diabetes': ['diabetes', 'diabetic', 'dm', 'type 2 diabetes', 'type 1 diabetes'],
            'hypertension': ['hypertension', 'high blood pressure', 'htn', 'elevated blood pressure'],
            'heart_disease': ['heart disease', 'cardiac', 'coronary', 'heart failure', 'cad', 'chf'],
            'asthma': ['asthma', 'reactive airway'],
            'copd': ['copd', 'chronic obstructive', 'emphysema', 'chronic bronchitis'],
            'kidney_disease': ['kidney', 'renal', 'ckd', 'chronic kidney'],
            'liver_disease': ['liver', 'hepatic', 'cirrhosis', 'hepatitis'],
            'cancer': ['cancer', 'malignancy', 'neoplasm', 'carcinoma', 'tumor'],
            'autoimmune_disorder': ['autoimmune', 'lupus', 'rheumatoid', 'multiple sclerosis']
        }
        
        for condition, keywords in mappings.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return condition
        
        return None
    
    def _parse_medications(self, medications: List[Dict]) -> List[str]:
        """Extract medication names from MedicationStatement resources."""
        med_list = []
        
        for med in medications:
            med_info = med.get('medicationCodeableConcept', {})
            text = med_info.get('text')
            
            if text:
                med_list.append(text.lower())
            else:
                codings = med_info.get('coding', [])
                for coding in codings:
                    display = coding.get('display')
                    if display:
                        med_list.append(display.lower())
                        break
        
        return list(set(med_list))
    
    def _parse_allergies(self, allergies: List[Dict]) -> List[str]:
        """Extract allergy information from AllergyIntolerance resources."""
        allergy_list = []
        
        for allergy in allergies:
            code_info = allergy.get('code', {})
            text = code_info.get('text')
            
            if text:
                allergy_list.append(text.lower())
            else:
                codings = code_info.get('coding', [])
                for coding in codings:
                    display = coding.get('display')
                    if display:
                        allergy_list.append(display.lower())
                        break
        
        return list(set(allergy_list))
    
    def _infer_symptoms(self, observations: Dict, 
                        conditions: List[str]) -> List[str]:
        """
        Infer symptoms from observations and conditions.
        
        This is a simplified inference - in production, would use
        clinical ontologies like SNOMED CT.
        """
        symptoms = []
        
        # Check for fever from temperature
        temp_obs = observations.get('8310-5')  # Body temperature LOINC
        if temp_obs and temp_obs.get('value'):
            if float(temp_obs['value']) > 37.5:
                symptoms.append('fever')
        
        # Infer symptoms from conditions
        condition_symptom_map = {
            'asthma': ['shortness_of_breath', 'cough'],
            'copd': ['shortness_of_breath', 'cough', 'fatigue'],
            'heart_disease': ['chest_pain', 'shortness_of_breath', 'fatigue']
        }
        
        for condition in conditions:
            if condition in condition_symptom_map:
                symptoms.extend(condition_symptom_map[condition])
        
        return list(set(symptoms))
    
    def to_cdss_input(self, fhir_data: FHIRPatientData) -> Dict:
        """
        Convert FHIR patient data to CDSS input format.
        
        Args:
            fhir_data: FHIRPatientData object
            
        Returns:
            Dictionary compatible with CDSS prediction functions
        """
        cdss_input = {
            'age': fhir_data.age or 50,  # Default age if not available
        }
        
        # Add vitals with defaults
        vital_defaults = {
            'heart_rate': 75,
            'blood_pressure_systolic': 120,
            'blood_pressure_diastolic': 80,
            'temperature': 37.0,
            'respiratory_rate': 16,
            'oxygen_saturation': 98
        }
        
        for vital, default in vital_defaults.items():
            cdss_input[vital] = fhir_data.vitals.get(vital, default)
        
        # Add symptom flags
        for symptom in SYMPTOMS_LIST:
            cdss_input[symptom] = 1 if symptom in fhir_data.symptoms else 0
        
        # Add condition flags
        for condition in EXISTING_CONDITIONS:
            if condition != 'none':
                cdss_input[f'condition_{condition}'] = \
                    1 if condition in fhir_data.conditions else 0
        
        # Add medication count
        cdss_input['num_medications'] = len(fhir_data.medications)
        
        # Calculate symptom count
        cdss_input['symptom_count'] = len(fhir_data.symptoms)
        
        return cdss_input
    
    def to_fhir_bundle(self, patient_data: Dict, 
                       patient_id: str = "cdss-patient-001") -> Dict:
        """
        Convert CDSS patient data to a FHIR Bundle.
        
        Args:
            patient_data: Dictionary with patient information
            patient_id: Patient identifier
            
        Returns:
            FHIR Bundle resource as dictionary
        """
        bundle = {
            'resourceType': 'Bundle',
            'type': 'collection',
            'timestamp': datetime.now().isoformat(),
            'entry': []
        }
        
        # Add Patient resource
        patient_resource = self._create_patient_resource(patient_data, patient_id)
        bundle['entry'].append({'resource': patient_resource})
        
        # Add Observation resources for vitals
        for vital_name, loinc_code in self.observation_codes.items():
            if vital_name in patient_data:
                obs = self._create_observation_resource(
                    patient_id, vital_name, patient_data[vital_name], loinc_code
                )
                bundle['entry'].append({'resource': obs})
        
        return bundle
    
    def _create_patient_resource(self, data: Dict, patient_id: str) -> Dict:
        """Create a FHIR Patient resource."""
        patient = {
            'resourceType': 'Patient',
            'id': patient_id,
            'active': True
        }
        
        if 'age' in data:
            birth_year = datetime.now().year - data['age']
            patient['birthDate'] = f"{birth_year}-01-01"
        
        if 'gender' in data:
            patient['gender'] = data['gender']
        
        return patient
    
    def _create_observation_resource(self, patient_id: str, 
                                      vital_name: str, 
                                      value: float,
                                      loinc_code: str) -> Dict:
        """Create a FHIR Observation resource for a vital sign."""
        unit_map = {
            'heart_rate': {'unit': 'beats/minute', 'code': '/min'},
            'blood_pressure_systolic': {'unit': 'mmHg', 'code': 'mm[Hg]'},
            'blood_pressure_diastolic': {'unit': 'mmHg', 'code': 'mm[Hg]'},
            'temperature': {'unit': 'Cel', 'code': 'Cel'},
            'respiratory_rate': {'unit': 'breaths/minute', 'code': '/min'},
            'oxygen_saturation': {'unit': '%', 'code': '%'},
            'blood_sugar': {'unit': 'mg/dL', 'code': 'mg/dL'}
        }
        
        unit_info = unit_map.get(vital_name, {'unit': '', 'code': ''})
        
        return {
            'resourceType': 'Observation',
            'id': f"{patient_id}-{vital_name}",
            'status': 'final',
            'code': {
                'coding': [{
                    'system': 'http://loinc.org',
                    'code': loinc_code,
                    'display': vital_name.replace('_', ' ').title()
                }]
            },
            'subject': {
                'reference': f'Patient/{patient_id}'
            },
            'effectiveDateTime': datetime.now().isoformat(),
            'valueQuantity': {
                'value': value,
                'unit': unit_info['unit'],
                'system': 'http://unitsofmeasure.org',
                'code': unit_info['code']
            }
        }
    
    def load_from_file(self, file_path: Union[str, Path]) -> FHIRPatientData:
        """
        Load and parse a FHIR Bundle from a JSON file.
        
        Args:
            file_path: Path to the FHIR JSON file
            
        Returns:
            FHIRPatientData object
        """
        with open(file_path, 'r') as f:
            bundle = json.load(f)
        
        return self.from_bundle(bundle)
    
    def save_to_file(self, bundle: Dict, file_path: Union[str, Path]):
        """
        Save a FHIR Bundle to a JSON file.
        
        Args:
            bundle: FHIR Bundle dictionary
            file_path: Path to save the file
        """
        with open(file_path, 'w') as f:
            json.dump(bundle, f, indent=2, default=str)


def get_sample_fhir_bundle() -> Dict:
    """
    Generate a sample FHIR Bundle for testing.
    
    Returns:
        Sample FHIR Bundle with patient, observations, conditions, and medications
    """
    return {
        "resourceType": "Bundle",
        "type": "collection",
        "timestamp": datetime.now().isoformat(),
        "entry": [
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": "sample-patient-001",
                    "name": [{"given": ["John"], "family": "Doe"}],
                    "gender": "male",
                    "birthDate": "1955-03-15"
                }
            },
            {
                "resource": {
                    "resourceType": "Observation",
                    "id": "hr-001",
                    "status": "final",
                    "code": {
                        "coding": [{"system": "http://loinc.org", "code": "8867-4", "display": "Heart rate"}]
                    },
                    "subject": {"reference": "Patient/sample-patient-001"},
                    "valueQuantity": {"value": 88, "unit": "beats/minute"}
                }
            },
            {
                "resource": {
                    "resourceType": "Observation",
                    "id": "bp-sys-001",
                    "status": "final",
                    "code": {
                        "coding": [{"system": "http://loinc.org", "code": "8480-6", "display": "Systolic blood pressure"}]
                    },
                    "subject": {"reference": "Patient/sample-patient-001"},
                    "valueQuantity": {"value": 145, "unit": "mmHg"}
                }
            },
            {
                "resource": {
                    "resourceType": "Observation",
                    "id": "temp-001",
                    "status": "final",
                    "code": {
                        "coding": [{"system": "http://loinc.org", "code": "8310-5", "display": "Body temperature"}]
                    },
                    "subject": {"reference": "Patient/sample-patient-001"},
                    "valueQuantity": {"value": 38.2, "unit": "Cel"}
                }
            },
            {
                "resource": {
                    "resourceType": "Observation",
                    "id": "spo2-001",
                    "status": "final",
                    "code": {
                        "coding": [{"system": "http://loinc.org", "code": "2708-6", "display": "Oxygen saturation"}]
                    },
                    "subject": {"reference": "Patient/sample-patient-001"},
                    "valueQuantity": {"value": 94, "unit": "%"}
                }
            },
            {
                "resource": {
                    "resourceType": "Condition",
                    "id": "cond-001",
                    "code": {"text": "Type 2 Diabetes Mellitus"},
                    "subject": {"reference": "Patient/sample-patient-001"}
                }
            },
            {
                "resource": {
                    "resourceType": "Condition",
                    "id": "cond-002",
                    "code": {"text": "Essential Hypertension"},
                    "subject": {"reference": "Patient/sample-patient-001"}
                }
            },
            {
                "resource": {
                    "resourceType": "MedicationStatement",
                    "id": "med-001",
                    "status": "active",
                    "medicationCodeableConcept": {"text": "Metformin 500mg"},
                    "subject": {"reference": "Patient/sample-patient-001"}
                }
            },
            {
                "resource": {
                    "resourceType": "MedicationStatement",
                    "id": "med-002",
                    "status": "active",
                    "medicationCodeableConcept": {"text": "Lisinopril 10mg"},
                    "subject": {"reference": "Patient/sample-patient-001"}
                }
            },
            {
                "resource": {
                    "resourceType": "AllergyIntolerance",
                    "id": "allergy-001",
                    "code": {"text": "Penicillin"},
                    "patient": {"reference": "Patient/sample-patient-001"}
                }
            }
        ]
    }
