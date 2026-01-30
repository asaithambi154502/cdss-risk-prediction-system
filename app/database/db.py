"""
SQLite Database Module for CDSS

Provides persistent storage for prediction results, alerts, and analytics.
No personal identifiers are stored - data is anonymized for system monitoring.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from contextlib import contextmanager
import threading

# Database file location
DB_PATH = Path(__file__).parent.parent.parent / "data" / "cdss.db"

# Thread-local storage for connections
_local = threading.local()


def get_connection() -> sqlite3.Connection:
    """
    Get a database connection (thread-safe).
    
    Returns:
        sqlite3.Connection: Database connection
    """
    if not hasattr(_local, 'connection') or _local.connection is None:
        _local.connection = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        _local.connection.row_factory = sqlite3.Row
    return _local.connection


@contextmanager
def get_db_cursor():
    """Context manager for database operations."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e


def init_db() -> None:
    """
    Initialize the database with required tables.
    Creates the database file and tables if they don't exist.
    """
    # Ensure data directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Create predictions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            user TEXT NOT NULL,
            user_role TEXT,
            risk_level TEXT NOT NULL,
            risk_probability REAL,
            alert_generated INTEGER DEFAULT 0,
            alert_type TEXT,
            heart_rate INTEGER,
            blood_pressure_systolic INTEGER,
            blood_pressure_diastolic INTEGER,
            temperature REAL,
            oxygen_saturation INTEGER,
            respiratory_rate INTEGER,
            symptom_count INTEGER DEFAULT 0,
            condition_count INTEGER DEFAULT 0,
            symptoms TEXT,
            conditions TEXT
        )
    ''')
    
    # Create alerts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            prediction_id INTEGER,
            user TEXT NOT NULL,
            risk_level TEXT NOT NULL,
            alert_message TEXT,
            recommendations TEXT,
            acknowledged INTEGER DEFAULT 0,
            acknowledged_at DATETIME,
            acknowledged_by TEXT,
            FOREIGN KEY (prediction_id) REFERENCES predictions(id)
        )
    ''')
    
    # Create indexes for faster queries
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_predictions_timestamp 
        ON predictions(timestamp)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_predictions_risk_level 
        ON predictions(risk_level)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_alerts_timestamp 
        ON alerts(timestamp)
    ''')
    
    conn.commit()
    conn.close()


def save_prediction(
    user: str,
    user_role: str,
    risk_level: str,
    risk_probability: float,
    alert_generated: bool,
    alert_type: Optional[str],
    vital_signs: Dict[str, Any],
    symptom_count: int,
    condition_count: int,
    symptoms: Optional[List[str]] = None,
    conditions: Optional[List[str]] = None
) -> int:
    """
    Save a prediction record to the database.
    
    Args:
        user: Username who made the prediction
        user_role: Role of the user
        risk_level: Predicted risk level (Low/Medium/High)
        risk_probability: Confidence score (0-1)
        alert_generated: Whether an alert was generated
        alert_type: Type of alert if generated
        vital_signs: Dictionary of vital signs
        symptom_count: Number of symptoms
        condition_count: Number of conditions
        symptoms: List of symptom names (stored as JSON)
        conditions: List of condition names (stored as JSON)
    
    Returns:
        int: ID of the inserted prediction
    """
    with get_db_cursor() as cursor:
        cursor.execute('''
            INSERT INTO predictions (
                user, user_role, risk_level, risk_probability,
                alert_generated, alert_type,
                heart_rate, blood_pressure_systolic, blood_pressure_diastolic,
                temperature, oxygen_saturation, respiratory_rate,
                symptom_count, condition_count, symptoms, conditions
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user,
            user_role,
            risk_level,
            risk_probability,
            1 if alert_generated else 0,
            alert_type,
            vital_signs.get('heart_rate'),
            vital_signs.get('blood_pressure_systolic'),
            vital_signs.get('blood_pressure_diastolic'),
            vital_signs.get('temperature'),
            vital_signs.get('oxygen_saturation'),
            vital_signs.get('respiratory_rate'),
            symptom_count,
            condition_count,
            json.dumps(symptoms) if symptoms else None,
            json.dumps(conditions) if conditions else None
        ))
        return cursor.lastrowid


def save_alert(
    user: str,
    risk_level: str,
    alert_message: str,
    recommendations: List[str],
    prediction_id: Optional[int] = None
) -> int:
    """
    Save an alert record to the database.
    
    Args:
        user: Username
        risk_level: Risk level
        alert_message: Alert message text
        recommendations: List of recommendations
        prediction_id: Optional ID of associated prediction
    
    Returns:
        int: ID of the inserted alert
    """
    with get_db_cursor() as cursor:
        cursor.execute('''
            INSERT INTO alerts (
                user, risk_level, alert_message, recommendations, prediction_id
            ) VALUES (?, ?, ?, ?, ?)
        ''', (
            user,
            risk_level,
            alert_message,
            json.dumps(recommendations),
            prediction_id
        ))
        return cursor.lastrowid


def get_predictions(
    limit: int = 100,
    risk_level: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get prediction records with optional filtering.
    
    Args:
        limit: Maximum number of records to return
        risk_level: Filter by risk level
        start_date: Filter by start date (ISO format)
        end_date: Filter by end date (ISO format)
        user: Filter by username
    
    Returns:
        List of prediction dictionaries
    """
    query = "SELECT * FROM predictions WHERE 1=1"
    params = []
    
    if risk_level:
        query += " AND risk_level = ?"
        params.append(risk_level)
    
    if start_date:
        query += " AND timestamp >= ?"
        params.append(start_date)
    
    if end_date:
        query += " AND timestamp <= ?"
        params.append(end_date)
    
    if user:
        query += " AND user = ?"
        params.append(user)
    
    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)
    
    with get_db_cursor() as cursor:
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_alerts(
    limit: int = 50,
    acknowledged: Optional[bool] = None
) -> List[Dict[str, Any]]:
    """
    Get alert records.
    
    Args:
        limit: Maximum number of records
        acknowledged: Filter by acknowledged status
    
    Returns:
        List of alert dictionaries
    """
    query = "SELECT * FROM alerts WHERE 1=1"
    params = []
    
    if acknowledged is not None:
        query += " AND acknowledged = ?"
        params.append(1 if acknowledged else 0)
    
    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)
    
    with get_db_cursor() as cursor:
        cursor.execute(query, params)
        rows = cursor.fetchall()
        results = []
        for row in rows:
            d = dict(row)
            # Parse recommendations JSON
            if d.get('recommendations'):
                try:
                    d['recommendations'] = json.loads(d['recommendations'])
                except:
                    d['recommendations'] = []
            results.append(d)
        return results


def get_statistics() -> Dict[str, Any]:
    """
    Get summary statistics for the analytics dashboard.
    
    Returns:
        Dictionary with various statistics
    """
    with get_db_cursor() as cursor:
        # Total predictions
        cursor.execute("SELECT COUNT(*) FROM predictions")
        total_predictions = cursor.fetchone()[0]
        
        # Predictions by risk level
        cursor.execute('''
            SELECT risk_level, COUNT(*) as count 
            FROM predictions 
            GROUP BY risk_level
        ''')
        risk_distribution = {row['risk_level']: row['count'] for row in cursor.fetchall()}
        
        # Total alerts
        cursor.execute("SELECT COUNT(*) FROM alerts")
        total_alerts = cursor.fetchone()[0]
        
        # Alerts by risk level
        cursor.execute('''
            SELECT risk_level, COUNT(*) as count 
            FROM alerts 
            GROUP BY risk_level
        ''')
        alert_distribution = {row['risk_level']: row['count'] for row in cursor.fetchall()}
        
        # Today's predictions
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute(
            "SELECT COUNT(*) FROM predictions WHERE date(timestamp) = ?",
            (today,)
        )
        today_predictions = cursor.fetchone()[0]
        
        # This week's predictions
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        cursor.execute(
            "SELECT COUNT(*) FROM predictions WHERE date(timestamp) >= ?",
            (week_ago,)
        )
        week_predictions = cursor.fetchone()[0]
        
        # High risk rate
        high_risk_count = risk_distribution.get('High', 0)
        high_risk_rate = (high_risk_count / total_predictions * 100) if total_predictions > 0 else 0
        
        # Alert rate
        alert_rate = (total_alerts / total_predictions * 100) if total_predictions > 0 else 0
        
        # Average vital signs for high risk cases
        cursor.execute('''
            SELECT 
                AVG(heart_rate) as avg_hr,
                AVG(blood_pressure_systolic) as avg_bp_sys,
                AVG(temperature) as avg_temp,
                AVG(oxygen_saturation) as avg_spo2
            FROM predictions 
            WHERE risk_level = 'High'
        ''')
        high_risk_vitals = cursor.fetchone()
        
        return {
            'total_predictions': total_predictions,
            'total_alerts': total_alerts,
            'today_predictions': today_predictions,
            'week_predictions': week_predictions,
            'risk_distribution': risk_distribution,
            'alert_distribution': alert_distribution,
            'high_risk_rate': round(high_risk_rate, 1),
            'alert_rate': round(alert_rate, 1),
            'high_risk_vitals': {
                'avg_heart_rate': round(high_risk_vitals['avg_hr'] or 0, 1),
                'avg_bp_systolic': round(high_risk_vitals['avg_bp_sys'] or 0, 1),
                'avg_temperature': round(high_risk_vitals['avg_temp'] or 0, 1),
                'avg_spo2': round(high_risk_vitals['avg_spo2'] or 0, 1)
            } if high_risk_vitals else {}
        }


def get_prediction_trends(days: int = 7) -> List[Dict[str, Any]]:
    """
    Get prediction trends over the specified number of days.
    
    Args:
        days: Number of days to include
    
    Returns:
        List of daily statistics
    """
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    with get_db_cursor() as cursor:
        cursor.execute('''
            SELECT 
                date(timestamp) as date,
                COUNT(*) as total,
                SUM(CASE WHEN risk_level = 'Low' THEN 1 ELSE 0 END) as low_risk,
                SUM(CASE WHEN risk_level = 'Medium' THEN 1 ELSE 0 END) as medium_risk,
                SUM(CASE WHEN risk_level = 'High' THEN 1 ELSE 0 END) as high_risk,
                SUM(alert_generated) as alerts
            FROM predictions
            WHERE date(timestamp) >= ?
            GROUP BY date(timestamp)
            ORDER BY date(timestamp)
        ''', (start_date,))
        
        return [dict(row) for row in cursor.fetchall()]


def acknowledge_alert(alert_id: int, user: str) -> bool:
    """
    Mark an alert as acknowledged.
    
    Args:
        alert_id: ID of the alert
        user: Username acknowledging the alert
    
    Returns:
        True if successful
    """
    with get_db_cursor() as cursor:
        cursor.execute('''
            UPDATE alerts 
            SET acknowledged = 1, 
                acknowledged_at = CURRENT_TIMESTAMP,
                acknowledged_by = ?
            WHERE id = ?
        ''', (user, alert_id))
        return cursor.rowcount > 0


def export_predictions_csv(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> str:
    """
    Export predictions to CSV format.
    
    Args:
        start_date: Optional start date filter
        end_date: Optional end date filter
    
    Returns:
        CSV string
    """
    import csv
    import io
    
    predictions = get_predictions(
        limit=10000,
        start_date=start_date,
        end_date=end_date
    )
    
    if not predictions:
        return ""
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=predictions[0].keys())
    writer.writeheader()
    writer.writerows(predictions)
    
    return output.getvalue()


def clear_old_data(days: int = 90) -> int:
    """
    Clear prediction and alert data older than specified days.
    For data retention compliance.
    
    Args:
        days: Age threshold for deletion
    
    Returns:
        Number of records deleted
    """
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    with get_db_cursor() as cursor:
        # Delete old alerts first (foreign key constraint)
        cursor.execute(
            "DELETE FROM alerts WHERE date(timestamp) < ?",
            (cutoff_date,)
        )
        alerts_deleted = cursor.rowcount
        
        # Delete old predictions
        cursor.execute(
            "DELETE FROM predictions WHERE date(timestamp) < ?",
            (cutoff_date,)
        )
        predictions_deleted = cursor.rowcount
        
        return alerts_deleted + predictions_deleted


# Initialize database on module import
init_db()
