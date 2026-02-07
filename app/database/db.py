"""
Database Module for CDSS

Supports PostgreSQL (for Render deployment) and SQLite (for local development).
Provides persistent storage for prediction results, alerts, and analytics.
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
import threading

# Check for DATABASE_URL environment variable (PostgreSQL on Render)
DATABASE_URL = os.environ.get('DATABASE_URL')

# Determine database type
USE_POSTGRES = DATABASE_URL is not None and DATABASE_URL.startswith('postgres')

if USE_POSTGRES:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    # Fix for Render's postgres:// vs postgresql://
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
else:
    import sqlite3
    # SQLite database file location
    DB_PATH = Path(__file__).parent.parent.parent / "data" / "cdss.db"

# Thread-local storage for connections
_local = threading.local()


def get_connection():
    """
    Get a database connection (thread-safe).
    
    Returns:
        Database connection (PostgreSQL or SQLite)
    """
    if USE_POSTGRES:
        if not hasattr(_local, 'connection') or _local.connection is None or _local.connection.closed:
            _local.connection = psycopg2.connect(DATABASE_URL)
        return _local.connection
    else:
        if not hasattr(_local, 'connection') or _local.connection is None:
            DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            _local.connection = sqlite3.connect(str(DB_PATH), check_same_thread=False)
            _local.connection.row_factory = sqlite3.Row
        return _local.connection


@contextmanager
def get_db_cursor():
    """Context manager for database operations."""
    conn = get_connection()
    if USE_POSTGRES:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
    else:
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
    Creates tables if they don't exist.
    """
    conn = get_connection()
    
    if USE_POSTGRES:
        cursor = conn.cursor()
        
        # Create predictions table (PostgreSQL)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                patient_id VARCHAR(100),
                doctor_id VARCHAR(100),
                user_name VARCHAR(100) NOT NULL,
                user_role VARCHAR(50),
                risk_level VARCHAR(20) NOT NULL,
                risk_probability REAL,
                alert_generated INTEGER DEFAULT 0,
                alert_type VARCHAR(50),
                heart_rate INTEGER,
                blood_pressure_systolic INTEGER,
                blood_pressure_diastolic INTEGER,
                temperature REAL,
                oxygen_saturation INTEGER,
                respiratory_rate INTEGER,
                blood_sugar REAL,
                pain_score INTEGER,
                consciousness_gcs INTEGER,
                bmi REAL,
                symptom_count INTEGER DEFAULT 0,
                condition_count INTEGER DEFAULT 0,
                symptoms TEXT,
                conditions TEXT
            )
        ''')
        
        # Create alerts table (PostgreSQL)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                prediction_id INTEGER,
                user_name VARCHAR(100) NOT NULL,
                risk_level VARCHAR(20) NOT NULL,
                alert_message TEXT,
                recommendations TEXT,
                acknowledged INTEGER DEFAULT 0,
                acknowledged_at TIMESTAMP,
                acknowledged_by VARCHAR(100),
                FOREIGN KEY (prediction_id) REFERENCES predictions(id)
            )
        ''')
        
        # Create indexes
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_predictions_timestamp 
            ON predictions(timestamp)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_predictions_patient_id 
            ON predictions(patient_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_predictions_doctor_id 
            ON predictions(doctor_id)
        ''')
        
    else:
        cursor = conn.cursor()
        
        # Create predictions table (SQLite)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                patient_id TEXT,
                doctor_id TEXT,
                user_name TEXT NOT NULL,
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
                blood_sugar REAL,
                pain_score INTEGER,
                consciousness_gcs INTEGER,
                bmi REAL,
                symptom_count INTEGER DEFAULT 0,
                condition_count INTEGER DEFAULT 0,
                symptoms TEXT,
                conditions TEXT
            )
        ''')
        
        # Create alerts table (SQLite)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                prediction_id INTEGER,
                user_name TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                alert_message TEXT,
                recommendations TEXT,
                acknowledged INTEGER DEFAULT 0,
                acknowledged_at DATETIME,
                acknowledged_by TEXT,
                FOREIGN KEY (prediction_id) REFERENCES predictions(id)
            )
        ''')
        
        # Create indexes
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_predictions_timestamp 
            ON predictions(timestamp)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_predictions_patient_id 
            ON predictions(patient_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_predictions_doctor_id 
            ON predictions(doctor_id)
        ''')
        
        # Migration: Add missing columns to existing databases
        try:
            cursor.execute('ALTER TABLE predictions ADD COLUMN patient_id TEXT')
        except:
            pass  # Column already exists
        try:
            cursor.execute('ALTER TABLE predictions ADD COLUMN doctor_id TEXT')
        except:
            pass  # Column already exists
    
    conn.commit()


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
    conditions: Optional[List[str]] = None,
    patient_id: Optional[str] = None,
    doctor_id: Optional[str] = None
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
        symptoms: List of symptom names
        conditions: List of condition names
        patient_id: Patient identifier
        doctor_id: Doctor identifier
    
    Returns:
        int: ID of the inserted prediction
    """
    with get_db_cursor() as cursor:
        if USE_POSTGRES:
            cursor.execute('''
                INSERT INTO predictions (
                    patient_id, doctor_id, user_name, user_role, risk_level, risk_probability,
                    alert_generated, alert_type,
                    heart_rate, blood_pressure_systolic, blood_pressure_diastolic,
                    temperature, oxygen_saturation, respiratory_rate,
                    blood_sugar, pain_score, consciousness_gcs, bmi,
                    symptom_count, condition_count, symptoms, conditions
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (
                patient_id or vital_signs.get('patient_id', ''),
                doctor_id or vital_signs.get('doctor_id', ''),
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
                vital_signs.get('blood_sugar'),
                vital_signs.get('pain_score'),
                vital_signs.get('consciousness_gcs'),
                vital_signs.get('bmi'),
                symptom_count,
                condition_count,
                json.dumps(symptoms) if symptoms else None,
                json.dumps(conditions) if conditions else None
            ))
            return cursor.fetchone()['id']
        else:
            cursor.execute('''
                INSERT INTO predictions (
                    patient_id, doctor_id, user_name, user_role, risk_level, risk_probability,
                    alert_generated, alert_type,
                    heart_rate, blood_pressure_systolic, blood_pressure_diastolic,
                    temperature, oxygen_saturation, respiratory_rate,
                    blood_sugar, pain_score, consciousness_gcs, bmi,
                    symptom_count, condition_count, symptoms, conditions
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                patient_id or vital_signs.get('patient_id', ''),
                doctor_id or vital_signs.get('doctor_id', ''),
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
                vital_signs.get('blood_sugar'),
                vital_signs.get('pain_score'),
                vital_signs.get('consciousness_gcs'),
                vital_signs.get('bmi'),
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
    
    Returns:
        int: ID of the inserted alert
    """
    with get_db_cursor() as cursor:
        if USE_POSTGRES:
            cursor.execute('''
                INSERT INTO alerts (
                    user_name, risk_level, alert_message, recommendations, prediction_id
                ) VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            ''', (
                user,
                risk_level,
                alert_message,
                json.dumps(recommendations),
                prediction_id
            ))
            return cursor.fetchone()['id']
        else:
            cursor.execute('''
                INSERT INTO alerts (
                    user_name, risk_level, alert_message, recommendations, prediction_id
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
    user: Optional[str] = None,
    patient_id: Optional[str] = None,
    doctor_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get prediction records with optional filtering.
    
    Returns:
        List of prediction dictionaries
    """
    params = []
    
    if USE_POSTGRES:
        query = "SELECT * FROM predictions WHERE 1=1"
        
        if risk_level:
            query += " AND risk_level = %s"
            params.append(risk_level)
        
        if start_date:
            query += " AND timestamp >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND timestamp <= %s"
            params.append(end_date)
        
        if user:
            query += " AND user_name = %s"
            params.append(user)
        
        if patient_id:
            query += " AND patient_id = %s"
            params.append(patient_id)
        
        if doctor_id:
            query += " AND doctor_id = %s"
            params.append(doctor_id)
        
        query += " ORDER BY timestamp DESC LIMIT %s"
        params.append(limit)
    else:
        query = "SELECT * FROM predictions WHERE 1=1"
        
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
            query += " AND user_name = ?"
            params.append(user)
        
        if patient_id:
            query += " AND patient_id = ?"
            params.append(patient_id)
        
        if doctor_id:
            query += " AND doctor_id = ?"
            params.append(doctor_id)
        
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
    """
    params = []
    
    if USE_POSTGRES:
        query = "SELECT * FROM alerts WHERE 1=1"
        if acknowledged is not None:
            query += " AND acknowledged = %s"
            params.append(1 if acknowledged else 0)
        query += " ORDER BY timestamp DESC LIMIT %s"
        params.append(limit)
    else:
        query = "SELECT * FROM alerts WHERE 1=1"
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
    """
    with get_db_cursor() as cursor:
        # Total predictions
        cursor.execute("SELECT COUNT(*) as count FROM predictions")
        result = cursor.fetchone()
        total_predictions = result['count'] if USE_POSTGRES else result[0]
        
        # Predictions by risk level
        cursor.execute('''
            SELECT risk_level, COUNT(*) as count 
            FROM predictions 
            GROUP BY risk_level
        ''')
        if USE_POSTGRES:
            risk_distribution = {row['risk_level']: row['count'] for row in cursor.fetchall()}
        else:
            risk_distribution = {row['risk_level']: row['count'] for row in cursor.fetchall()}
        
        # Total alerts
        cursor.execute("SELECT COUNT(*) as count FROM alerts")
        result = cursor.fetchone()
        total_alerts = result['count'] if USE_POSTGRES else result[0]
        
        # Today's predictions
        today = datetime.now().strftime('%Y-%m-%d')
        if USE_POSTGRES:
            cursor.execute(
                "SELECT COUNT(*) as count FROM predictions WHERE DATE(timestamp) = %s",
                (today,)
            )
        else:
            cursor.execute(
                "SELECT COUNT(*) as count FROM predictions WHERE date(timestamp) = ?",
                (today,)
            )
        result = cursor.fetchone()
        today_predictions = result['count'] if USE_POSTGRES else result[0]
        
        # This week's predictions
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        if USE_POSTGRES:
            cursor.execute(
                "SELECT COUNT(*) as count FROM predictions WHERE DATE(timestamp) >= %s",
                (week_ago,)
            )
        else:
            cursor.execute(
                "SELECT COUNT(*) as count FROM predictions WHERE date(timestamp) >= ?",
                (week_ago,)
            )
        result = cursor.fetchone()
        week_predictions = result['count'] if USE_POSTGRES else result[0]
        
        # High risk rate
        high_risk_count = risk_distribution.get('High', 0)
        high_risk_rate = (high_risk_count / total_predictions * 100) if total_predictions > 0 else 0
        
        # Alert rate
        alert_rate = (total_alerts / total_predictions * 100) if total_predictions > 0 else 0
        
        return {
            'total_predictions': total_predictions,
            'total_alerts': total_alerts,
            'today_predictions': today_predictions,
            'week_predictions': week_predictions,
            'risk_distribution': risk_distribution,
            'high_risk_rate': round(high_risk_rate, 1),
            'alert_rate': round(alert_rate, 1)
        }


def get_prediction_trends(days: int = 7) -> List[Dict[str, Any]]:
    """
    Get prediction trends over the specified number of days.
    """
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    with get_db_cursor() as cursor:
        if USE_POSTGRES:
            cursor.execute('''
                SELECT 
                    DATE(timestamp) as date,
                    COUNT(*) as total,
                    SUM(CASE WHEN risk_level = 'Low' THEN 1 ELSE 0 END) as low_risk,
                    SUM(CASE WHEN risk_level = 'Medium' THEN 1 ELSE 0 END) as medium_risk,
                    SUM(CASE WHEN risk_level = 'High' THEN 1 ELSE 0 END) as high_risk,
                    SUM(alert_generated) as alerts
                FROM predictions
                WHERE DATE(timestamp) >= %s
                GROUP BY DATE(timestamp)
                ORDER BY DATE(timestamp)
            ''', (start_date,))
        else:
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


def export_predictions_csv(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> str:
    """
    Export predictions to CSV format.
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


def export_predictions_excel() -> Optional[bytes]:
    """
    Export predictions to Excel format.
    
    Returns:
        Bytes of the Excel file, or None if no records
    """
    import io
    try:
        import pandas as pd
        
        predictions = get_predictions(limit=10000)
        
        if not predictions:
            return None
        
        df = pd.DataFrame(predictions)
        
        output = io.BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        
        return output.getvalue()
    except Exception as e:
        print(f"Error exporting to Excel: {e}")
        return None


def get_total_records() -> int:
    """Return total number of prediction records."""
    with get_db_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as count FROM predictions")
        result = cursor.fetchone()
        return result['count'] if USE_POSTGRES else result[0]


# Initialize database on module import
try:
    init_db()
except Exception as e:
    print(f"Database initialization warning: {e}")
