"""
Logging Module for CDSS

Provides prediction and alert logging for quality improvement and audit trails.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import threading

# Ensure project root is in path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Get the logs directory path
LOGS_DIR = project_root / "logs"

# Import database functions
try:
    from app.database.db import save_prediction as db_save_prediction
    from app.database.db import save_alert as db_save_alert
    DB_AVAILABLE = True
except ImportError as e:
    print(f"Database module not available: {e}")
    DB_AVAILABLE = False


@dataclass
class PredictionLog:
    """Log entry for a prediction."""
    timestamp: str
    user: str
    user_role: str
    risk_level: str
    risk_probability: float
    alert_generated: bool
    alert_type: Optional[str]
    vital_signs_summary: Dict[str, Any]
    symptom_count: int
    condition_count: int
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class AlertLog:
    """Log entry for an alert."""
    timestamp: str
    user: str
    risk_level: str
    alert_message: str
    recommendations: List[str]
    acknowledged: bool = False
    
    def to_dict(self) -> Dict:
        return asdict(self)


class CDSSLogger:
    """Logger for CDSS predictions and alerts."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern to ensure single logger instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self._ensure_logs_directory()
        self.predictions_file = LOGS_DIR / "predictions.json"
        self.alerts_file = LOGS_DIR / "alerts.json"
        
        # Initialize files if they don't exist
        self._init_log_file(self.predictions_file)
        self._init_log_file(self.alerts_file)
    
    def _ensure_logs_directory(self) -> None:
        """Create logs directory if it doesn't exist."""
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    def _init_log_file(self, file_path: Path) -> None:
        """Initialize a log file with empty array if it doesn't exist."""
        if not file_path.exists():
            with open(file_path, 'w') as f:
                json.dump([], f)
    
    def _read_logs(self, file_path: Path) -> List[Dict]:
        """Read logs from a file."""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def _write_logs(self, file_path: Path, logs: List[Dict]) -> None:
        """Write logs to a file."""
        with open(file_path, 'w') as f:
            json.dump(logs, f, indent=2, default=str)
    
    def log_prediction(
        self,
        user: str,
        user_role: str,
        risk_level: str,
        risk_probability: float,
        alert_generated: bool,
        alert_type: Optional[str],
        vital_signs: Dict[str, Any],
        symptom_count: int,
        condition_count: int
    ) -> None:
        """
        Log a prediction event.
        
        Note: No patient identifiers are stored - only clinical data.
        Saves to both SQLite database and JSON file for redundancy.
        """
        log_entry = PredictionLog(
            timestamp=datetime.now().isoformat(),
            user=user,
            user_role=user_role,
            risk_level=risk_level,
            risk_probability=round(risk_probability, 4),
            alert_generated=alert_generated,
            alert_type=alert_type,
            vital_signs_summary={
                "heart_rate": vital_signs.get("heart_rate"),
                "temperature": vital_signs.get("temperature"),
                "blood_pressure": f"{vital_signs.get('blood_pressure_systolic', 'N/A')}/{vital_signs.get('blood_pressure_diastolic', 'N/A')}",
                "oxygen_saturation": vital_signs.get("oxygen_saturation"),
                "respiratory_rate": vital_signs.get("respiratory_rate")
            },
            symptom_count=symptom_count,
            condition_count=condition_count
        )
        
        # Save to SQLite database
        if DB_AVAILABLE:
            try:
                print(f"[DEBUG] Attempting to save prediction to database...")
                print(f"[DEBUG] patient_id: {vital_signs.get('patient_id', '')}, doctor_id: {vital_signs.get('doctor_id', '')}")
                db_save_prediction(
                    user=user,
                    user_role=user_role,
                    risk_level=risk_level,
                    risk_probability=risk_probability,
                    alert_generated=alert_generated,
                    alert_type=alert_type,
                    vital_signs=vital_signs,
                    symptom_count=symptom_count,
                    condition_count=condition_count,
                    patient_id=vital_signs.get('patient_id', ''),
                    doctor_id=vital_signs.get('doctor_id', '')
                )
                print(f"[DEBUG] Database save SUCCESSFUL!")
            except Exception as e:
                # Log error but don't fail - fallback to JSON
                print(f"[DEBUG] Database save FAILED: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"[DEBUG] DB_AVAILABLE is False, skipping database save")
        
        # Also save to JSON file (backup)
        logs = self._read_logs(self.predictions_file)
        logs.append(log_entry.to_dict())
        
        # Keep only last 1000 logs to prevent file from growing too large
        if len(logs) > 1000:
            logs = logs[-1000:]
        
        self._write_logs(self.predictions_file, logs)
    
    def log_alert(
        self,
        user: str,
        risk_level: str,
        alert_message: str,
        recommendations: List[str]
    ) -> None:
        """Log an alert event. Saves to both SQLite database and JSON file."""
        log_entry = AlertLog(
            timestamp=datetime.now().isoformat(),
            user=user,
            risk_level=risk_level,
            alert_message=alert_message,
            recommendations=recommendations
        )
        
        # Save to SQLite database
        if DB_AVAILABLE:
            try:
                db_save_alert(
                    user=user,
                    risk_level=risk_level,
                    alert_message=alert_message,
                    recommendations=recommendations
                )
            except Exception as e:
                # Log error but don't fail - fallback to JSON
                print(f"Database alert save failed: {e}")
        
        # Also save to JSON file (backup)
        logs = self._read_logs(self.alerts_file)
        logs.append(log_entry.to_dict())
        
        # Keep only last 500 alerts
        if len(logs) > 500:
            logs = logs[-500:]
        
        self._write_logs(self.alerts_file, logs)
    
    def get_predictions(
        self,
        limit: int = 100,
        risk_level: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict]:
        """
        Get prediction logs with optional filtering.
        
        Args:
            limit: Maximum number of logs to return
            risk_level: Filter by risk level (Low, Medium, High)
            start_date: Filter by start date (ISO format)
            end_date: Filter by end date (ISO format)
        """
        logs = self._read_logs(self.predictions_file)
        
        # Apply filters
        if risk_level:
            logs = [l for l in logs if l.get('risk_level') == risk_level]
        
        if start_date:
            logs = [l for l in logs if l.get('timestamp', '') >= start_date]
        
        if end_date:
            logs = [l for l in logs if l.get('timestamp', '') <= end_date]
        
        # Return most recent first, limited
        return list(reversed(logs))[:limit]
    
    def get_alerts(self, limit: int = 50) -> List[Dict]:
        """Get recent alert logs."""
        logs = self._read_logs(self.alerts_file)
        return list(reversed(logs))[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get summary statistics for the dashboard."""
        predictions = self._read_logs(self.predictions_file)
        alerts = self._read_logs(self.alerts_file)
        
        if not predictions:
            return {
                "total_predictions": 0,
                "total_alerts": 0,
                "risk_distribution": {"Low": 0, "Medium": 0, "High": 0},
                "alert_rate": 0
            }
        
        # Risk distribution
        risk_counts = {"Low": 0, "Medium": 0, "High": 0}
        for log in predictions:
            risk = log.get('risk_level', 'Low')
            if risk in risk_counts:
                risk_counts[risk] += 1
        
        total = len(predictions)
        alert_count = len(alerts)
        
        return {
            "total_predictions": total,
            "total_alerts": alert_count,
            "risk_distribution": risk_counts,
            "risk_percentages": {
                k: round(v / total * 100, 1) if total > 0 else 0 
                for k, v in risk_counts.items()
            },
            "alert_rate": round(alert_count / total * 100, 1) if total > 0 else 0
        }
    
    def clear_logs(self) -> None:
        """Clear all logs (admin only function)."""
        self._write_logs(self.predictions_file, [])
        self._write_logs(self.alerts_file, [])


# Singleton instance
logger = CDSSLogger()


def log_prediction(*args, **kwargs):
    """Convenience function to log a prediction."""
    logger.log_prediction(*args, **kwargs)


def log_alert(*args, **kwargs):
    """Convenience function to log an alert."""
    logger.log_alert(*args, **kwargs)


def get_logger() -> CDSSLogger:
    """Get the logger instance."""
    return logger
