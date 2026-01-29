"""
Smart Alert Fatigue Reduction Module for CDSS

Implements dynamic alert prioritization to reduce clinician fatigue
while ensuring critical alerts are never missed.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
from collections import deque
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import ALERT_PRIORITY_CONFIG


class AlertPriority(Enum):
    """Alert priority levels."""
    CRITICAL = 4  # Immediate action required
    HIGH = 3      # Review within 30 minutes
    MEDIUM = 2    # Review when able
    LOW = 1       # For documentation only


@dataclass
class SmartAlert:
    """Represents a prioritized clinical alert."""
    alert_id: str
    patient_id: Optional[str]
    risk_level: str
    risk_score: float
    priority: AlertPriority
    message: str
    recommendations: List[str]
    timestamp: datetime
    source: str  # "ml", "rules", or "hybrid"
    
    # Display properties
    icon: str = ""
    color: str = ""
    display_time: Optional[int] = None  # seconds before auto-dismiss
    sound: bool = False
    
    # Tracking
    was_suppressed: bool = False
    suppression_reason: Optional[str] = None
    clinician_feedback: Optional[str] = None
    was_acknowledged: bool = False
    
    def __post_init__(self):
        """Set display properties based on priority."""
        config = ALERT_PRIORITY_CONFIG['levels']
        priority_config = config.get(self.priority.name, {})
        self.icon = priority_config.get('icon', '📋')
        self.color = priority_config.get('color', '#6c757d')
        self.display_time = priority_config.get('display_time')
        self.sound = priority_config.get('sound', False)


@dataclass
class FatigueMetrics:
    """Metrics for tracking alert fatigue."""
    total_alerts: int = 0
    alerts_per_hour: float = 0.0
    suppressed_count: int = 0
    acknowledged_count: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    fatigue_level: str = "normal"  # "normal", "elevated", "high"
    recommendation: str = ""


class SmartAlertEngine:
    """
    Dynamic alert prioritization to reduce clinician fatigue.
    
    This engine:
    1. Prioritizes alerts based on risk severity and context
    2. Suppresses repeated low-priority alerts
    3. Tracks alert patterns to detect clinician fatigue
    4. Adapts prioritization based on feedback
    """
    
    def __init__(self):
        self.config = ALERT_PRIORITY_CONFIG
        self.alert_history: deque = deque(
            maxlen=self.config['fatigue_tracking']['alert_history_size']
        )
        self.suppression_cache: Dict[str, datetime] = {}
        self.feedback_log: List[Dict] = []
        self.consecutive_alerts: Dict[str, int] = {}
    
    def _generate_alert_id(self, patient_id: Optional[str], 
                           risk_level: str, source: str) -> str:
        """Generate a unique alert ID."""
        timestamp = datetime.now().isoformat()
        content = f"{patient_id}:{risk_level}:{source}:{timestamp}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _get_suppression_key(self, patient_id: Optional[str], 
                             risk_level: str) -> str:
        """Generate key for suppression tracking."""
        return f"{patient_id or 'unknown'}:{risk_level}"
    
    def prioritize_alert(self, risk_level: str, risk_score: float,
                         message: str, recommendations: List[str],
                         patient_id: Optional[str] = None,
                         source: str = "ml",
                         context: Optional[Dict] = None) -> SmartAlert:
        """
        Dynamically prioritize and create an alert.
        
        Args:
            risk_level: The risk classification ("Low", "Medium", "High")
            risk_score: The numerical risk score (0-1)
            message: The alert message
            recommendations: List of recommended actions
            patient_id: Optional patient identifier
            source: Source of the alert ("ml", "rules", "hybrid")
            context: Additional context (e.g., ward type, time of day)
            
        Returns:
            SmartAlert with assigned priority
        """
        # Determine base priority from risk level
        base_priority = self._get_base_priority(risk_level, risk_score)
        
        # Adjust priority based on context and history
        adjusted_priority, adjustment_reason = self._adjust_priority(
            base_priority, patient_id, risk_level, context
        )
        
        # Create the alert
        alert = SmartAlert(
            alert_id=self._generate_alert_id(patient_id, risk_level, source),
            patient_id=patient_id,
            risk_level=risk_level,
            risk_score=risk_score,
            priority=adjusted_priority,
            message=message,
            recommendations=recommendations,
            timestamp=datetime.now(),
            source=source
        )
        
        # Check if should be suppressed
        should_suppress, suppression_reason = self._should_suppress(
            alert, patient_id, risk_level
        )
        
        if should_suppress:
            alert.was_suppressed = True
            alert.suppression_reason = suppression_reason
        
        # Track in history
        self._record_alert(alert)
        
        return alert
    
    def _get_base_priority(self, risk_level: str, 
                           risk_score: float) -> AlertPriority:
        """
        Determine base priority from risk level and score.
        
        Args:
            risk_level: The risk classification
            risk_score: The numerical risk score
            
        Returns:
            Base AlertPriority
        """
        if risk_level == "High":
            # High risk with very high score is critical
            if risk_score >= 0.85:
                return AlertPriority.CRITICAL
            return AlertPriority.HIGH
        elif risk_level == "Medium":
            # Medium risk with higher score gets elevated
            if risk_score >= 0.55:
                return AlertPriority.HIGH
            return AlertPriority.MEDIUM
        else:  # Low
            return AlertPriority.LOW
    
    def _adjust_priority(self, base_priority: AlertPriority,
                         patient_id: Optional[str],
                         risk_level: str,
                         context: Optional[Dict]) -> Tuple[AlertPriority, str]:
        """
        Adjust priority based on context and fatigue tracking.
        
        Returns:
            Tuple of (adjusted priority, reason for adjustment)
        """
        adjusted = base_priority
        reason = "Base priority"
        
        # Check fatigue level
        metrics = self.get_fatigue_metrics()
        if metrics.fatigue_level == "high" and base_priority.value <= AlertPriority.MEDIUM.value:
            # Reduce priority during high fatigue, except for critical
            adjusted = AlertPriority.LOW
            reason = "Priority reduced due to high alert fatigue"
        
        # Check consecutive alerts for same patient
        supp_key = self._get_suppression_key(patient_id, risk_level)
        consecutive = self.consecutive_alerts.get(supp_key, 0)
        threshold = self.config['suppression']['consecutive_threshold']
        
        if consecutive >= threshold and adjusted != AlertPriority.CRITICAL:
            # Reduce priority after many consecutive similar alerts
            if adjusted.value > AlertPriority.LOW.value:
                adjusted = AlertPriority(adjusted.value - 1)
                reason = f"Priority reduced after {consecutive} similar alerts"
        
        # Context-based adjustments
        if context:
            # ICU context - elevate all alerts
            if context.get('ward_type') == 'ICU':
                if adjusted.value < AlertPriority.HIGH.value:
                    adjusted = AlertPriority.HIGH
                    reason = "Priority elevated for ICU context"
            
            # Night shift - be more conservative with low priority
            if context.get('shift') == 'night':
                if adjusted == AlertPriority.LOW:
                    reason = "Low priority during night shift"
        
        return adjusted, reason
    
    def _should_suppress(self, alert: SmartAlert,
                         patient_id: Optional[str],
                         risk_level: str) -> Tuple[bool, Optional[str]]:
        """
        Determine if an alert should be suppressed.
        
        Returns:
            Tuple of (should_suppress, reason)
        """
        config = self.config['suppression']
        
        # Never suppress critical alerts
        if alert.priority == AlertPriority.CRITICAL:
            return False, None
        
        # Check time-based suppression
        supp_key = self._get_suppression_key(patient_id, risk_level)
        last_alert = self.suppression_cache.get(supp_key)
        
        if last_alert:
            min_interval = timedelta(minutes=config['min_interval_minutes'])
            if datetime.now() - last_alert < min_interval:
                return True, f"Similar alert within {config['min_interval_minutes']} minutes"
        
        # Check low alert rate limit
        if alert.priority == AlertPriority.LOW:
            recent_low = sum(
                1 for a in self.alert_history
                if a.priority == AlertPriority.LOW
                and (datetime.now() - a.timestamp) < timedelta(hours=1)
            )
            
            if recent_low >= config['max_low_alerts_per_hour']:
                return True, f"Exceeded {config['max_low_alerts_per_hour']} low alerts per hour"
        
        return False, None
    
    def _record_alert(self, alert: SmartAlert):
        """Record alert in history and update tracking."""
        self.alert_history.append(alert)
        
        # Update suppression cache
        supp_key = self._get_suppression_key(alert.patient_id, alert.risk_level)
        self.suppression_cache[supp_key] = alert.timestamp
        
        # Update consecutive count
        if supp_key not in self.consecutive_alerts:
            self.consecutive_alerts[supp_key] = 0
        self.consecutive_alerts[supp_key] += 1
    
    def acknowledge_alert(self, alert_id: str):
        """Mark an alert as acknowledged by clinician."""
        for alert in self.alert_history:
            if alert.alert_id == alert_id:
                alert.was_acknowledged = True
                break
    
    def register_feedback(self, alert_id: str, was_useful: bool,
                          feedback_text: Optional[str] = None):
        """
        Track clinician feedback on alert usefulness.
        
        This feedback is used for adaptive learning to improve
        future alert prioritization.
        """
        self.feedback_log.append({
            'alert_id': alert_id,
            'was_useful': was_useful,
            'feedback_text': feedback_text,
            'timestamp': datetime.now()
        })
        
        # Find and update the alert
        for alert in self.alert_history:
            if alert.alert_id == alert_id:
                alert.clinician_feedback = "useful" if was_useful else "not_useful"
                
                # If marked as not useful, reduce future similar alert priority
                if not was_useful:
                    supp_key = self._get_suppression_key(
                        alert.patient_id, alert.risk_level
                    )
                    self.consecutive_alerts[supp_key] = \
                        self.consecutive_alerts.get(supp_key, 0) + 2  # Penalty
                break
    
    def get_fatigue_metrics(self) -> FatigueMetrics:
        """
        Calculate current alert fatigue metrics.
        
        Returns:
            FatigueMetrics object with current statistics
        """
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)
        
        # Filter recent alerts
        recent_alerts = [
            a for a in self.alert_history
            if a.timestamp > one_hour_ago
        ]
        
        total = len(self.alert_history)
        alerts_per_hour = len(recent_alerts)
        
        # Count by priority
        critical = sum(1 for a in recent_alerts if a.priority == AlertPriority.CRITICAL)
        high = sum(1 for a in recent_alerts if a.priority == AlertPriority.HIGH)
        medium = sum(1 for a in recent_alerts if a.priority == AlertPriority.MEDIUM)
        low = sum(1 for a in recent_alerts if a.priority == AlertPriority.LOW)
        
        # Count suppressed and acknowledged
        suppressed = sum(1 for a in self.alert_history if a.was_suppressed)
        acknowledged = sum(1 for a in self.alert_history if a.was_acknowledged)
        
        # Determine fatigue level
        fatigue_threshold = self.config['fatigue_tracking']['fatigue_threshold']
        if alerts_per_hour >= fatigue_threshold:
            fatigue_level = "high"
            recommendation = "Consider reviewing alert thresholds or taking a break"
        elif alerts_per_hour >= fatigue_threshold * 0.7:
            fatigue_level = "elevated"
            recommendation = "Alert volume approaching fatigue threshold"
        else:
            fatigue_level = "normal"
            recommendation = "Alert volume is manageable"
        
        return FatigueMetrics(
            total_alerts=total,
            alerts_per_hour=alerts_per_hour,
            suppressed_count=suppressed,
            acknowledged_count=acknowledged,
            critical_count=critical,
            high_count=high,
            medium_count=medium,
            low_count=low,
            fatigue_level=fatigue_level,
            recommendation=recommendation
        )
    
    def get_priority_distribution(self) -> Dict[str, int]:
        """Get distribution of alerts by priority level."""
        distribution = {
            'CRITICAL': 0,
            'HIGH': 0,
            'MEDIUM': 0,
            'LOW': 0
        }
        
        for alert in self.alert_history:
            distribution[alert.priority.name] += 1
        
        return distribution
    
    def get_suppression_statistics(self) -> Dict:
        """Get statistics about alert suppression."""
        total = len(self.alert_history)
        suppressed = sum(1 for a in self.alert_history if a.was_suppressed)
        
        return {
            'total_alerts': total,
            'suppressed_alerts': suppressed,
            'suppression_rate': suppressed / total if total > 0 else 0,
            'effective_alerts': total - suppressed
        }
    
    def format_alert_for_display(self, alert: SmartAlert) -> Dict:
        """
        Format an alert for UI display.
        
        Returns:
            Dictionary with formatted alert data
        """
        return {
            'id': alert.alert_id,
            'priority': alert.priority.name,
            'priority_value': alert.priority.value,
            'risk_level': alert.risk_level,
            'risk_score': round(alert.risk_score * 100, 1),
            'message': alert.message,
            'recommendations': alert.recommendations,
            'icon': alert.icon,
            'color': alert.color,
            'timestamp': alert.timestamp.strftime('%H:%M:%S'),
            'source': alert.source,
            'display_time': alert.display_time,
            'sound': alert.sound,
            'suppressed': alert.was_suppressed,
            'suppression_reason': alert.suppression_reason
        }
    
    def get_active_alerts(self, 
                          include_suppressed: bool = False) -> List[SmartAlert]:
        """
        Get list of active (non-suppressed) alerts.
        
        Args:
            include_suppressed: Whether to include suppressed alerts
            
        Returns:
            List of alerts sorted by priority (highest first)
        """
        alerts = list(self.alert_history)
        
        if not include_suppressed:
            alerts = [a for a in alerts if not a.was_suppressed]
        
        # Sort by priority (descending) then timestamp (descending)
        alerts.sort(key=lambda a: (a.priority.value, a.timestamp), reverse=True)
        
        return alerts
    
    def clear_old_alerts(self, hours: int = 24):
        """Clear alerts older than the specified hours."""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        # Filter alert history
        self.alert_history = deque(
            (a for a in self.alert_history if a.timestamp > cutoff),
            maxlen=self.config['fatigue_tracking']['alert_history_size']
        )
        
        # Clear old suppression cache entries
        self.suppression_cache = {
            k: v for k, v in self.suppression_cache.items()
            if v > cutoff
        }


# Convenience function to create a quick alert
def create_quick_alert(risk_level: str, message: str,
                       engine: Optional[SmartAlertEngine] = None) -> SmartAlert:
    """
    Quick helper to create an alert without full engine.
    
    Args:
        risk_level: Risk level string
        message: Alert message
        engine: Optional SmartAlertEngine instance
        
    Returns:
        SmartAlert object
    """
    if engine is None:
        engine = SmartAlertEngine()
    
    risk_scores = {'Low': 0.2, 'Medium': 0.5, 'High': 0.8}
    
    return engine.prioritize_alert(
        risk_level=risk_level,
        risk_score=risk_scores.get(risk_level, 0.5),
        message=message,
        recommendations=[],
        source="quick"
    )
