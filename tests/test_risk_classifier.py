"""
Tests for Risk Classifier Module
"""

import pytest
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ml.risk_classifier import RiskClassifier, RiskLevel, AlertEngine


class TestRiskClassifier:
    """Test cases for RiskClassifier class."""
    
    @pytest.fixture
    def classifier(self):
        """Create a classifier instance."""
        return RiskClassifier()
    
    def test_classify_low_risk(self, classifier):
        """Test classification of low risk prediction."""
        # Probabilities: [0.8, 0.15, 0.05] = mostly low risk
        assessment = classifier.classify(0, [0.8, 0.15, 0.05])
        
        assert assessment.risk_level == RiskLevel.LOW
        assert assessment.risk_label == "Low"
        assert assessment.should_alert is False  # Low risk doesn't trigger alert
    
    def test_classify_medium_risk(self, classifier):
        """Test classification of medium risk prediction."""
        # Probabilities: [0.2, 0.6, 0.2] = mostly medium risk
        assessment = classifier.classify(1, [0.2, 0.6, 0.2])
        
        assert assessment.risk_level == RiskLevel.MEDIUM
        assert assessment.risk_label == "Medium"
        assert assessment.should_alert is True  # Medium risk triggers alert
    
    def test_classify_high_risk(self, classifier):
        """Test classification of high risk prediction."""
        # Probabilities: [0.05, 0.15, 0.8] = mostly high risk
        assessment = classifier.classify(2, [0.05, 0.15, 0.8])
        
        assert assessment.risk_level == RiskLevel.HIGH
        assert assessment.risk_label == "High"
        assert assessment.should_alert is True  # High risk triggers alert
    
    def test_risk_score_calculation(self, classifier):
        """Test that risk score is correctly calculated."""
        # Pure high risk should give score close to 1
        high_risk_assessment = classifier.classify(2, [0.0, 0.0, 1.0])
        assert high_risk_assessment.risk_score >= 0.9
        
        # Pure low risk should give score close to 0
        low_risk_assessment = classifier.classify(0, [1.0, 0.0, 0.0])
        assert low_risk_assessment.risk_score <= 0.1
    
    def test_confidence_is_probability(self, classifier):
        """Test that confidence matches predicted class probability."""
        probs = [0.1, 0.3, 0.6]
        assessment = classifier.classify(2, probs)
        
        assert assessment.confidence == 0.6
    
    def test_alert_message_generated(self, classifier):
        """Test that alert messages are generated for medium/high risk."""
        medium_assessment = classifier.classify(1, [0.2, 0.6, 0.2])
        high_assessment = classifier.classify(2, [0.1, 0.1, 0.8])
        
        assert medium_assessment.alert_message is not None
        assert high_assessment.alert_message is not None
        assert "HIGH" in high_assessment.alert_message.upper()
    
    def test_recommendations_populated(self, classifier):
        """Test that recommendations are generated."""
        assessment = classifier.classify(2, [0.1, 0.1, 0.8])
        
        assert assessment.recommendations is not None
        assert len(assessment.recommendations) > 0
    
    def test_risk_summary(self, classifier):
        """Test get_risk_summary method."""
        assessment = classifier.classify(1, [0.2, 0.6, 0.2])
        summary = classifier.get_risk_summary(assessment)
        
        assert 'risk_level' in summary
        assert 'risk_score' in summary
        assert 'confidence' in summary
        assert 'probabilities' in summary
        assert 'color' in summary


class TestAlertEngine:
    """Test cases for AlertEngine class."""
    
    @pytest.fixture
    def engine(self):
        """Create an alert engine instance."""
        return AlertEngine()
    
    def test_process_prediction(self, engine):
        """Test processing a prediction."""
        assessment = engine.process_prediction(
            predicted_class=2,
            probabilities=[0.1, 0.2, 0.7],
            patient_id="TEST001"
        )
        
        assert assessment.risk_level == RiskLevel.HIGH
    
    def test_alert_history_tracking(self, engine):
        """Test that alerts are tracked in history."""
        # Process high risk (should generate alert)
        engine.process_prediction(2, [0.1, 0.1, 0.8], "P001")
        
        # Process low risk (no alert)
        engine.process_prediction(0, [0.8, 0.1, 0.1], "P002")
        
        # Process medium risk (should generate alert)
        engine.process_prediction(1, [0.2, 0.6, 0.2], "P003")
        
        stats = engine.get_alert_statistics()
        
        assert stats['total_alerts'] == 2  # High + Medium
        assert stats['high_risk_alerts'] == 1
        assert stats['medium_risk_alerts'] == 1
    
    def test_alert_statistics_empty(self, engine):
        """Test statistics when no alerts generated."""
        stats = engine.get_alert_statistics()
        assert stats['total_alerts'] == 0


class TestRiskLevel:
    """Test RiskLevel enum."""
    
    def test_risk_level_values(self):
        """Test enum values."""
        assert RiskLevel.LOW.value == 0
        assert RiskLevel.MEDIUM.value == 1
        assert RiskLevel.HIGH.value == 2
    
    def test_risk_level_from_int(self):
        """Test creating enum from integer."""
        assert RiskLevel(0) == RiskLevel.LOW
        assert RiskLevel(1) == RiskLevel.MEDIUM
        assert RiskLevel(2) == RiskLevel.HIGH


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
