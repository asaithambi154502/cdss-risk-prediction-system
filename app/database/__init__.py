"""
Database module initialization for CDSS.
"""

from app.database.db import (
    init_db,
    get_connection,
    save_prediction,
    save_alert,
    get_predictions,
    get_alerts,
    get_statistics,
    get_prediction_trends,
    export_predictions_csv,
    export_predictions_excel,
    get_total_records
)

__all__ = [
    'init_db',
    'get_connection',
    'save_prediction',
    'save_alert',
    'get_predictions',
    'get_alerts',
    'get_statistics',
    'get_prediction_trends',
    'export_predictions_csv',
    'export_predictions_excel',
    'get_total_records'
]
