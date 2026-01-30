"""
Unified Multi-Risk Prediction Engine for CDSS

Detects multiple types of medical risks within a single framework:
- Medication Error Risk
- Disease Progression Risk
- Adverse Event Risk
- Hospital Readmission Risk
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from cdss_config import (
    MULTI_RISK_CONFIG, RISK_THRESHOLDS, DRUG_INTERACTIONS,
    VITAL_CRITICAL_RULES, EXISTING_CONDITIONS
)


class RiskType(Enum):
    """Types of risks that can be predicted."""
    MEDICATION_ERROR = "medication_error"
    DISEASE_PROGRESSION = "disease_progression"
    ADVERSE_EVENT = "adverse_event"
    HOSPITAL_READMISSION = "hospital_readmission"


@dataclass
class RiskResult:
    """Result of a single risk prediction."""
    risk_type: RiskType
    risk_score: float  # 0.0 to 1.0
    risk_level: str    # "Low", "Medium", "High"
    confidence: float
    contributing_factors: List[str]
    recommendations: List[str]
    
    @property
    def display_name(self) -> str:
        config = MULTI_RISK_CONFIG['risk_types'].get(self.risk_type.value, {})
        return config.get('display_name', self.risk_type.value)
    
    @property
    def icon(self) -> str:
        config = MULTI_RISK_CONFIG['risk_types'].get(self.risk_type.value, {})
        return config.get('icon', '⚠️')
    
    @property
    def color(self) -> str:
        config = MULTI_RISK_CONFIG['risk_types'].get(self.risk_type.value, {})
        return config.get('color', '#6c757d')


@dataclass
class MultiRiskAssessment:
    """Combined assessment of all risk types."""
    patient_id: Optional[str]
    timestamp: str
    overall_risk_score: float
    overall_risk_level: str
    risk_results: Dict[str, RiskResult]
    highest_risk: RiskResult
    summary: str
    requires_immediate_attention: bool = False
    
    def get_risk(self, risk_type: RiskType) -> Optional[RiskResult]:
        """Get a specific risk result."""
        return self.risk_results.get(risk_type.value)
    
    def get_all_recommendations(self) -> List[str]:
        """Get combined recommendations from all risk types."""
        all_recs = []
        for result in self.risk_results.values():
            all_recs.extend(result.recommendations)
        return list(set(all_recs))  # Remove duplicates


class MultiRiskEngine:
    """
    Unified engine for multiple risk type predictions.
    
    Provides a comprehensive risk assessment by analyzing:
    1. Medication Error Risk - Based on polypharmacy, drug interactions
    2. Disease Progression Risk - Based on vitals, symptoms, conditions
    3. Adverse Event Risk - Based on allergies, lab values, symptoms
    4. Hospital Readmission Risk - Based on conditions, age, previous data
    """
    
    def __init__(self, ml_model=None):
        """
        Initialize the multi-risk engine.
        
        Args:
            ml_model: Optional trained ML model for enhanced predictions
        """
        self.config = MULTI_RISK_CONFIG
        self.thresholds = self.config['default_thresholds']
        self.ml_model = ml_model
    
    def predict_all_risks(self, patient_data: Dict,
                          patient_id: Optional[str] = None) -> MultiRiskAssessment:
        """
        Run all risk predictions and return unified assessment.
        
        Args:
            patient_data: Dictionary with patient clinical data
            patient_id: Optional patient identifier
            
        Returns:
            MultiRiskAssessment with all risk analysis
        """
        from datetime import datetime
        
        risk_results = {}
        
        # Get each enabled risk type prediction
        risk_types = self.config['risk_types']
        
        if risk_types['medication_error']['enabled']:
            risk_results['medication_error'] = self.get_medication_error_risk(patient_data)
        
        if risk_types['disease_progression']['enabled']:
            risk_results['disease_progression'] = self.get_disease_progression_risk(patient_data)
        
        if risk_types['adverse_event']['enabled']:
            risk_results['adverse_event'] = self.get_adverse_event_risk(patient_data)
        
        if risk_types['hospital_readmission']['enabled']:
            risk_results['hospital_readmission'] = self.get_readmission_risk(patient_data)
        
        # Calculate overall risk
        overall_score, overall_level = self._aggregate_risks(risk_results)
        
        # Find highest risk
        highest_risk = max(risk_results.values(), key=lambda r: r.risk_score)
        
        # Generate summary
        summary = self._generate_summary(risk_results, overall_level)
        
        # Determine if immediate attention needed
        requires_attention = any(
            r.risk_level == "High" for r in risk_results.values()
        )
        
        return MultiRiskAssessment(
            patient_id=patient_id,
            timestamp=datetime.now().isoformat(),
            overall_risk_score=overall_score,
            overall_risk_level=overall_level,
            risk_results=risk_results,
            highest_risk=highest_risk,
            summary=summary,
            requires_immediate_attention=requires_attention
        )
    
    def get_medication_error_risk(self, patient_data: Dict) -> RiskResult:
        """
        Predict medication error risk.
        
        Factors:
        - Number of medications (polypharmacy)
        - Drug-drug interactions
        - High-risk medications
        - Patient age (elderly more vulnerable)
        """
        factors = []
        risk_score = 0.0
        
        # Get medication data
        medications = patient_data.get('medications', [])
        num_meds = patient_data.get('num_medications', len(medications))
        age = patient_data.get('age', 50)
        
        # Polypharmacy risk
        if num_meds >= 10:
            risk_score += 0.35
            factors.append(f"High polypharmacy ({num_meds} medications)")
        elif num_meds >= 5:
            risk_score += 0.20
            factors.append(f"Moderate polypharmacy ({num_meds} medications)")
        elif num_meds >= 3:
            risk_score += 0.10
            factors.append(f"Multiple medications ({num_meds})")
        
        # Check for known drug interactions
        interactions = self._check_drug_interactions(medications)
        if interactions['severe']:
            risk_score += 0.40
            factors.extend([f"Severe interaction: {i['effect']}" for i in interactions['severe']])
        if interactions['moderate']:
            risk_score += 0.20
            factors.extend([f"Moderate interaction: {i['effect']}" for i in interactions['moderate']])
        
        # Age factor
        if age >= 75:
            risk_score += 0.15
            factors.append("Advanced age increases medication error risk")
        elif age >= 65:
            risk_score += 0.10
            factors.append("Elderly patient - monitor medication closely")
        
        # Check for high-risk medications
        high_risk_meds = ['warfarin', 'insulin', 'opioids', 'digoxin', 'methotrexate']
        patient_high_risk = [m for m in medications if any(hr in m.lower() for hr in high_risk_meds)]
        if patient_high_risk:
            risk_score += 0.15
            factors.append(f"High-risk medications present: {', '.join(patient_high_risk)}")
        
        # Cap at 1.0
        risk_score = min(risk_score, 1.0)
        
        # Determine level
        risk_level = self._score_to_level(risk_score)
        
        # Generate recommendations
        recommendations = self._get_medication_recommendations(risk_level, factors)
        
        return RiskResult(
            risk_type=RiskType.MEDICATION_ERROR,
            risk_score=risk_score,
            risk_level=risk_level,
            confidence=0.75,
            contributing_factors=factors,
            recommendations=recommendations
        )
    
    def get_disease_progression_risk(self, patient_data: Dict) -> RiskResult:
        """
        Predict disease progression risk.
        
        Factors:
        - Vital signs abnormalities
        - Symptom severity
        - Existing conditions
        - Age
        """
        factors = []
        risk_score = 0.0
        
        age = patient_data.get('age', 50)
        
        # Check vital signs
        vitals_risk, vital_factors = self._assess_vitals(patient_data)
        risk_score += vitals_risk
        factors.extend(vital_factors)
        
        # Symptom count
        symptom_count = patient_data.get('symptom_count', 0)
        if symptom_count >= 5:
            risk_score += 0.25
            factors.append(f"Multiple symptoms present ({symptom_count})")
        elif symptom_count >= 3:
            risk_score += 0.15
            factors.append(f"Several symptoms present ({symptom_count})")
        
        # Check for critical symptoms
        critical_symptoms = ['chest_pain', 'shortness_of_breath', 'confusion']
        for symptom in critical_symptoms:
            if patient_data.get(symptom, 0) == 1:
                risk_score += 0.15
                factors.append(f"Critical symptom: {symptom.replace('_', ' ')}")
        
        # Existing conditions
        conditions_risk = 0
        for condition in EXISTING_CONDITIONS:
            if condition != 'none' and patient_data.get(f'condition_{condition}', 0) == 1:
                conditions_risk += 0.08
                factors.append(f"Existing condition: {condition.replace('_', ' ')}")
        risk_score += min(conditions_risk, 0.30)  # Cap conditions contribution
        
        # Age factor
        if age >= 75:
            risk_score += 0.15
            factors.append("Advanced age increases disease progression risk")
        elif age >= 65:
            risk_score += 0.10
        
        risk_score = min(risk_score, 1.0)
        risk_level = self._score_to_level(risk_score)
        recommendations = self._get_disease_recommendations(risk_level, factors)
        
        return RiskResult(
            risk_type=RiskType.DISEASE_PROGRESSION,
            risk_score=risk_score,
            risk_level=risk_level,
            confidence=0.80,
            contributing_factors=factors,
            recommendations=recommendations
        )
    
    def get_adverse_event_risk(self, patient_data: Dict) -> RiskResult:
        """
        Predict adverse event risk.
        
        Factors:
        - Allergies
        - Abnormal lab values
        - Drug interactions
        - Recent procedures
        """
        factors = []
        risk_score = 0.0
        
        # Allergies
        allergies = patient_data.get('allergies', [])
        if len(allergies) >= 3:
            risk_score += 0.20
            factors.append(f"Multiple allergies ({len(allergies)})")
        elif allergies:
            risk_score += 0.10
            factors.append(f"Known allergies: {', '.join(allergies[:3])}")
        
        # Critical vital abnormalities
        vitals_critical = self._check_critical_vitals(patient_data)
        if vitals_critical:
            risk_score += 0.35
            factors.extend(vitals_critical)
        
        # Drug interactions (severe ones increase adverse event risk)
        medications = patient_data.get('medications', [])
        interactions = self._check_drug_interactions(medications)
        if interactions['severe']:
            risk_score += 0.30
            factors.append("Severe drug interactions present")
        
        # Symptom indicators for adverse events
        adverse_symptoms = ['nausea', 'vomiting', 'dizziness', 'confusion']
        adverse_present = sum(
            1 for s in adverse_symptoms 
            if patient_data.get(s, 0) == 1
        )
        if adverse_present >= 2:
            risk_score += 0.20
            factors.append(f"Multiple adverse event indicators ({adverse_present})")
        elif adverse_present >= 1:
            risk_score += 0.10
        
        risk_score = min(risk_score, 1.0)
        risk_level = self._score_to_level(risk_score)
        recommendations = self._get_adverse_event_recommendations(risk_level, factors)
        
        return RiskResult(
            risk_type=RiskType.ADVERSE_EVENT,
            risk_score=risk_score,
            risk_level=risk_level,
            confidence=0.70,
            contributing_factors=factors,
            recommendations=recommendations
        )
    
    def get_readmission_risk(self, patient_data: Dict) -> RiskResult:
        """
        Predict hospital readmission risk.
        
        Factors:
        - Number of chronic conditions
        - Recent hospitalization history
        - Age
        - Polypharmacy
        - Social/functional status
        """
        factors = []
        risk_score = 0.0
        
        age = patient_data.get('age', 50)
        
        # Chronic conditions count
        chronic_count = 0
        chronic_conditions = ['diabetes', 'heart_disease', 'copd', 'kidney_disease']
        for condition in chronic_conditions:
            if patient_data.get(f'condition_{condition}', 0) == 1:
                chronic_count += 1
        
        if chronic_count >= 3:
            risk_score += 0.35
            factors.append(f"Multiple chronic conditions ({chronic_count})")
        elif chronic_count >= 2:
            risk_score += 0.25
            factors.append(f"Two chronic conditions")
        elif chronic_count >= 1:
            risk_score += 0.15
            factors.append(f"One chronic condition")
        
        # Age factor (significant for readmission)
        if age >= 80:
            risk_score += 0.20
            factors.append("Age 80+ significantly increases readmission risk")
        elif age >= 70:
            risk_score += 0.15
            factors.append("Age 70+ increases readmission risk")
        elif age >= 65:
            risk_score += 0.10
        
        # Polypharmacy
        num_meds = patient_data.get('num_medications', 0)
        if num_meds >= 8:
            risk_score += 0.15
            factors.append(f"Polypharmacy ({num_meds} medications)")
        elif num_meds >= 5:
            risk_score += 0.10
        
        # Recent hospitalization (if available)
        if patient_data.get('recent_hospitalization', False):
            risk_score += 0.25
            factors.append("Recent hospitalization within 30 days")
        
        # Heart failure is a major readmission risk
        if patient_data.get('condition_heart_disease', 0) == 1:
            risk_score += 0.10
            factors.append("Heart disease increases readmission risk")
        
        # Functional status (if available)
        if patient_data.get('limited_mobility', False):
            risk_score += 0.15
            factors.append("Limited mobility")
        
        risk_score = min(risk_score, 1.0)
        risk_level = self._score_to_level(risk_score)
        recommendations = self._get_readmission_recommendations(risk_level, factors)
        
        return RiskResult(
            risk_type=RiskType.HOSPITAL_READMISSION,
            risk_score=risk_score,
            risk_level=risk_level,
            confidence=0.75,
            contributing_factors=factors,
            recommendations=recommendations
        )
    
    def _check_drug_interactions(self, medications: List[str]) -> Dict:
        """Check for known drug interactions."""
        result = {'severe': [], 'moderate': [], 'minor': []}
        
        if not medications:
            return result
        
        meds_lower = [m.lower() for m in medications]
        
        for severity, interactions in DRUG_INTERACTIONS.items():
            for interaction in interactions:
                drug1, drug2 = interaction['drug1'], interaction['drug2']
                # Check if both drugs are present
                has_drug1 = any(drug1 in m for m in meds_lower)
                has_drug2 = any(drug2 in m for m in meds_lower)
                if has_drug1 and has_drug2:
                    result[severity].append(interaction)
        
        return result
    
    def _assess_vitals(self, patient_data: Dict) -> Tuple[float, List[str]]:
        """Assess vital signs and return risk contribution."""
        risk = 0.0
        factors = []
        
        vitals_to_check = {
            'heart_rate': (60, 100),
            'blood_pressure_systolic': (90, 140),
            'blood_pressure_diastolic': (60, 90),
            'temperature': (36.1, 37.5),
            'respiratory_rate': (12, 20),
            'oxygen_saturation': (95, 100)
        }
        
        for vital, (low, high) in vitals_to_check.items():
            value = patient_data.get(vital)
            if value is not None:
                if value < low:
                    risk += 0.10
                    factors.append(f"Low {vital.replace('_', ' ')}: {value}")
                elif value > high:
                    risk += 0.10
                    factors.append(f"Elevated {vital.replace('_', ' ')}: {value}")
        
        # Special case for oxygen saturation
        spo2 = patient_data.get('oxygen_saturation')
        if spo2 is not None and spo2 < 92:
            risk += 0.15  # Additional risk for low SpO2
        
        return risk, factors
    
    def _check_critical_vitals(self, patient_data: Dict) -> List[str]:
        """Check for critically abnormal vitals."""
        critical = []
        
        for vital, thresholds in VITAL_CRITICAL_RULES.items():
            value = patient_data.get(vital)
            if value is not None:
                if 'critical_low' in thresholds and value < thresholds['critical_low']:
                    critical.append(f"CRITICAL: {vital.replace('_', ' ')} = {value} (below {thresholds['critical_low']})")
                if 'critical_high' in thresholds and value > thresholds['critical_high']:
                    critical.append(f"CRITICAL: {vital.replace('_', ' ')} = {value} (above {thresholds['critical_high']})")
        
        return critical
    
    def _score_to_level(self, score: float) -> str:
        """Convert risk score to level string."""
        if score >= self.thresholds['medium']:
            return "High"
        elif score >= self.thresholds['low']:
            return "Medium"
        else:
            return "Low"
    
    def _aggregate_risks(self, risk_results: Dict[str, RiskResult]) -> Tuple[float, str]:
        """
        Aggregate individual risks into overall score.
        
        Uses the configured aggregation method.
        """
        if not risk_results:
            return 0.0, "Low"
        
        method = self.config['aggregation_method']
        
        if method == 'weighted_avg':
            # Weighted average of all risks
            total_weight = 0
            weighted_sum = 0
            for risk_type, result in risk_results.items():
                weight = self.config['risk_types'][risk_type]['weight']
                weighted_sum += result.risk_score * weight
                total_weight += weight
            overall = weighted_sum / total_weight if total_weight > 0 else 0
        
        elif method == 'weighted_max':
            # Maximum risk, weighted by importance
            max_weighted = 0
            for risk_type, result in risk_results.items():
                weight = self.config['risk_types'][risk_type]['weight']
                weighted = result.risk_score * (1 + weight * 0.5)  # Boost by weight
                max_weighted = max(max_weighted, weighted)
            overall = min(max_weighted, 1.0)
        
        else:  # 'highest'
            # Simply take the highest risk
            overall = max(r.risk_score for r in risk_results.values())
        
        level = self._score_to_level(overall)
        return overall, level
    
    def _generate_summary(self, risk_results: Dict[str, RiskResult], 
                          overall_level: str) -> str:
        """Generate a summary of the multi-risk assessment."""
        high_risks = [r for r in risk_results.values() if r.risk_level == "High"]
        medium_risks = [r for r in risk_results.values() if r.risk_level == "Medium"]
        
        if high_risks:
            risk_names = [r.display_name for r in high_risks]
            return f"🚨 HIGH RISK: {', '.join(risk_names)}. Immediate clinical review recommended."
        elif medium_risks:
            risk_names = [r.display_name for r in medium_risks]
            return f"⚠️ MODERATE RISK: {', '.join(risk_names)}. Enhanced monitoring recommended."
        else:
            return "✅ LOW RISK across all categories. Continue standard care protocol."
    
    def _get_medication_recommendations(self, level: str, factors: List[str]) -> List[str]:
        """Get medication error risk recommendations."""
        recs = {
            "High": [
                "Perform comprehensive medication reconciliation",
                "Review for potential drug-drug interactions",
                "Consider clinical pharmacist consultation",
                "Implement enhanced medication monitoring",
                "Verify dosing for renal/hepatic function"
            ],
            "Medium": [
                "Review current medication list for accuracy",
                "Check for common drug interactions",
                "Verify patient understanding of medications",
                "Document any medication changes"
            ],
            "Low": [
                "Continue standard medication monitoring",
                "Ensure medication list is up to date"
            ]
        }
        return recs.get(level, [])
    
    def _get_disease_recommendations(self, level: str, factors: List[str]) -> List[str]:
        """Get disease progression risk recommendations."""
        recs = {
            "High": [
                "Increase monitoring frequency",
                "Consider additional diagnostic tests",
                "Review and optimize treatment plan",
                "Consult with specialist if needed",
                "Document all clinical findings"
            ],
            "Medium": [
                "Monitor vital signs more frequently",
                "Review symptom progression",
                "Ensure treatment compliance",
                "Schedule follow-up assessment"
            ],
            "Low": [
                "Continue current treatment plan",
                "Standard monitoring protocol"
            ]
        }
        return recs.get(level, [])
    
    def _get_adverse_event_recommendations(self, level: str, factors: List[str]) -> List[str]:
        """Get adverse event risk recommendations."""
        recs = {
            "High": [
                "Immediate review of current medications",
                "Check for drug-allergy interactions",
                "Monitor for adverse event symptoms",
                "Consider alternative medications",
                "Prepare for potential intervention"
            ],
            "Medium": [
                "Review allergy and medication lists",
                "Monitor for adverse reactions",
                "Document any new symptoms",
                "Consider dose adjustments"
            ],
            "Low": [
                "Maintain allergy awareness",
                "Standard adverse event monitoring"
            ]
        }
        return recs.get(level, [])
    
    def _get_readmission_recommendations(self, level: str, factors: List[str]) -> List[str]:
        """Get hospital readmission risk recommendations."""
        recs = {
            "High": [
                "Develop comprehensive discharge plan",
                "Arrange early follow-up appointment (within 7 days)",
                "Consider home health services",
                "Ensure medication reconciliation at discharge",
                "Provide detailed patient education",
                "Coordinate with primary care provider"
            ],
            "Medium": [
                "Schedule follow-up within 14 days",
                "Review discharge instructions thoroughly",
                "Provide contact information for questions",
                "Consider transitional care coordination"
            ],
            "Low": [
                "Standard discharge planning",
                "Routine follow-up scheduling"
            ]
        }
        return recs.get(level, [])
    
    def get_risk_radar_data(self, assessment: MultiRiskAssessment) -> Dict:
        """
        Prepare data for radar/spider chart visualization.
        
        Returns:
            Dictionary with chart data
        """
        labels = []
        values = []
        colors = []
        
        for risk_type, result in assessment.risk_results.items():
            config = self.config['risk_types'].get(risk_type, {})
            labels.append(config.get('display_name', risk_type))
            values.append(result.risk_score * 100)  # Convert to percentage
            colors.append(config.get('color', '#6c757d'))
        
        return {
            'labels': labels,
            'values': values,
            'colors': colors,
            'overall_score': assessment.overall_risk_score * 100,
            'overall_level': assessment.overall_risk_level
        }
