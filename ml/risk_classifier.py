"""
Risk Classification Engine for CDSS

Converts ML model predictions into risk levels and generates
appropriate alerts based on severity.
"""

from typing import Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import RISK_THRESHOLDS, RISK_LEVELS, RISK_COLORS, ALERT_CONFIG


class RiskLevel(Enum):
    """Enumeration of risk levels."""
    LOW = 0
    MEDIUM = 1
    HIGH = 2


@dataclass
class RiskAssessment:
    """Data class for risk assessment results."""
    risk_level: RiskLevel
    risk_label: str
    risk_score: float
    confidence: float
    probabilities: Dict[str, float]
    color: str
    should_alert: bool
    alert_message: Optional[str] = None
    recommendations: Optional[list] = None


class RiskClassifier:
    """Classifies predictions into risk levels and generates alerts."""
    
    def __init__(self):
        self.thresholds = RISK_THRESHOLDS
        self.alert_config = ALERT_CONFIG
        
    def classify(self, predicted_class: int, probabilities: list) -> RiskAssessment:
        """
        Classify prediction into risk assessment.
        
        Args:
            predicted_class: Model's predicted class (0, 1, or 2)
            probabilities: Probability array for each class
            
        Returns:
            RiskAssessment object with full analysis
        """
        # Determine risk level
        risk_level = RiskLevel(predicted_class)
        risk_label = RISK_LEVELS[predicted_class]
        
        # Calculate risk score (weighted probability)
        risk_score = (
            probabilities[0] * 0.0 +   # Low contributes 0
            probabilities[1] * 0.5 +   # Medium contributes 0.5
            probabilities[2] * 1.0     # High contributes 1.0
        )
        
        # Confidence is the probability of the predicted class
        confidence = probabilities[predicted_class]
        
        # Get color
        color = RISK_COLORS[risk_label]
        
        # Determine if alert should be shown
        should_alert = self._should_show_alert(risk_level)
        
        # Generate alert message and recommendations
        alert_message = None
        recommendations = None
        
        if should_alert:
            alert_message = self._generate_alert_message(risk_level, confidence)
            recommendations = self._generate_recommendations(risk_level)
        
        return RiskAssessment(
            risk_level=risk_level,
            risk_label=risk_label,
            risk_score=risk_score,
            confidence=confidence,
            probabilities={
                'Low': probabilities[0],
                'Medium': probabilities[1],
                'High': probabilities[2]
            },
            color=color,
            should_alert=should_alert,
            alert_message=alert_message,
            recommendations=recommendations
        )
    
    def _should_show_alert(self, risk_level: RiskLevel) -> bool:
        """Determine if an alert should be displayed based on risk level."""
        if risk_level == RiskLevel.LOW:
            return self.alert_config['show_low_risk']
        elif risk_level == RiskLevel.MEDIUM:
            return self.alert_config['show_medium_risk']
        else:  # HIGH
            return self.alert_config['show_high_risk']
    
    def _generate_alert_message(self, risk_level: RiskLevel, confidence: float) -> str:
        """Generate appropriate alert message based on risk level."""
        confidence_pct = int(confidence * 100)
        
        messages = {
            RiskLevel.LOW: f"Low risk detected ({confidence_pct}% confidence). Standard care protocol recommended.",
            RiskLevel.MEDIUM: f"⚠️ MEDIUM RISK DETECTED ({confidence_pct}% confidence). Review patient symptoms and consider additional monitoring.",
            RiskLevel.HIGH: f"🚨 HIGH RISK ALERT ({confidence_pct}% confidence). Immediate clinical review recommended. Verify symptoms and consider specialist consultation."
        }
        
        return messages[risk_level]
    
    def _generate_recommendations(self, risk_level: RiskLevel) -> list:
        """Generate clinical recommendations based on risk level."""
        recommendations = {
            RiskLevel.LOW: [
                "Continue standard monitoring",
                "Document patient symptoms",
                "Schedule follow-up as per protocol"
            ],
            RiskLevel.MEDIUM: [
                "Review all patient symptoms carefully",
                "Consider additional diagnostic tests",
                "Increase monitoring frequency",
                "Document findings and rationale",
                "Consider second opinion if uncertain"
            ],
            RiskLevel.HIGH: [
                "🚨 Perform immediate clinical review",
                "Verify all vital signs and symptoms",
                "Consider urgent diagnostic tests",
                "Consult with senior clinician or specialist",
                "Document all observations in detail",
                "Prepare for potential escalation of care",
                "Ensure patient monitoring is continuous"
            ]
        }
        
        return recommendations[risk_level]
    
    def get_risk_summary(self, assessment: RiskAssessment) -> Dict:
        """
        Get a summary dictionary of the risk assessment.
        
        Args:
            assessment: RiskAssessment object
            
        Returns:
            Dictionary with summary information
        """
        return {
            'risk_level': assessment.risk_label,
            'risk_score': round(assessment.risk_score, 3),
            'confidence': round(assessment.confidence * 100, 1),
            'probabilities': {k: round(v * 100, 1) for k, v in assessment.probabilities.items()},
            'color': assessment.color,
            'alert_required': assessment.should_alert,
            'message': assessment.alert_message,
            'recommendations': assessment.recommendations
        }


class AlertEngine:
    """Engine for generating and managing clinical alerts."""
    
    def __init__(self):
        self.classifier = RiskClassifier()
        self.alert_history = []
        
    def process_prediction(self, predicted_class: int, probabilities: list, 
                          patient_id: Optional[str] = None) -> RiskAssessment:
        """
        Process a prediction and generate appropriate alerts.
        
        Args:
            predicted_class: Model's predicted class
            probabilities: Probability array
            patient_id: Optional patient identifier
            
        Returns:
            RiskAssessment with alert information
        """
        assessment = self.classifier.classify(predicted_class, probabilities)
        
        # Log alert if shown
        if assessment.should_alert:
            self.alert_history.append({
                'patient_id': patient_id,
                'risk_level': assessment.risk_label,
                'confidence': assessment.confidence,
                'message': assessment.alert_message
            })
            
        return assessment
    
    def get_alert_statistics(self) -> Dict:
        """Get statistics about generated alerts."""
        if not self.alert_history:
            return {'total_alerts': 0}
            
        return {
            'total_alerts': len(self.alert_history),
            'high_risk_alerts': sum(1 for a in self.alert_history if a['risk_level'] == 'High'),
            'medium_risk_alerts': sum(1 for a in self.alert_history if a['risk_level'] == 'Medium')
        }
