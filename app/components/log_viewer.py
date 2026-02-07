"""
Log Viewer Component for CDSS

Provides admin dashboard for viewing prediction and alert logs.
Now uses SQLite database for consistent data with Analytics Dashboard.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.database.db import (
    get_statistics,
    get_predictions,
    get_alerts,
    get_total_records
)
from app.auth import get_current_user, UserRole


def render_log_viewer():
    """Render the log viewer dashboard (admin only)."""
    user = get_current_user()
    
    if not user or not user.is_admin():
        st.error("🚫 Access Denied: Only administrators can view logs.")
        return
    
    st.header("📊 System Logs & Analytics")
    st.caption("View prediction history and system statistics")
    
    # Statistics overview - now from database
    stats = get_statistics()
    
    st.subheader("📈 Quick Stats")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Predictions",
            value=stats["total_predictions"],
            delta=None
        )
    
    with col2:
        st.metric(
            label="Total Alerts",
            value=stats["total_alerts"],
            delta=None
        )
    
    with col3:
        st.metric(
            label="Alert Rate",
            value=f"{stats['alert_rate']}%",
            delta=None
        )
    
    with col4:
        # Calculate high risk percentage
        total = stats.get('total_predictions', 0)
        high_count = stats.get('risk_distribution', {}).get('High', 0)
        high_risk_pct = round((high_count / total * 100), 1) if total > 0 else 0
        st.metric(
            label="High Risk Cases",
            value=f"{high_risk_pct}%",
            delta=None
        )
    
    st.divider()
    
    # Risk distribution chart
    if stats["total_predictions"] > 0:
        st.subheader("📊 Risk Level Distribution")
        
        col_chart1, col_chart2 = st.columns([2, 1])
        
        with col_chart1:
            # Create a horizontal bar chart
            risk_dist = stats.get('risk_distribution', {})
            risk_data = pd.DataFrame({
                'Risk Level': ['Low', 'Medium', 'High'],
                'Count': [
                    risk_dist.get('Low', 0),
                    risk_dist.get('Medium', 0),
                    risk_dist.get('High', 0)
                ],
                'Color': ['#28a745', '#ffc107', '#dc3545']
            })
            
            st.bar_chart(risk_data.set_index('Risk Level')['Count'])
        
        with col_chart2:
            st.markdown("**Distribution Breakdown:**")
            total = stats.get('total_predictions', 1)  # Avoid division by zero
            for level in ['Low', 'Medium', 'High']:
                count = stats['risk_distribution'].get(level, 0)
                pct = round((count / total * 100), 1) if total > 0 else 0
                color = {'Low': '🟢', 'Medium': '🟡', 'High': '🔴'}[level]
                st.markdown(f"{color} **{level}**: {count} ({pct}%)")
    
    st.divider()
    
    # Tabs for different log views
    tab1, tab2 = st.tabs(["📋 Prediction History", "🚨 Alert History"])
    
    with tab1:
        render_prediction_logs()
    
    with tab2:
        render_alert_logs()
    
    st.divider()
    
    # Admin actions
    st.subheader("⚙️ Admin Actions")
    
    col_action1, col_action2, col_action3 = st.columns(3)
    
    with col_action1:
        if st.button("🔄 Refresh Logs", use_container_width=True):
            st.rerun()
    
    with col_action3:
        st.info("💡 Database records are persistent. Use Analytics tab for data export.")


def render_prediction_logs():
    """Render prediction logs table from database."""
    st.subheader("📋 Recent Predictions")
    
    # Filters
    col_filter1, col_filter2, col_filter3 = st.columns(3)
    
    with col_filter1:
        risk_filter = st.selectbox(
            "Filter by Risk Level",
            options=["All", "Low", "Medium", "High"],
            key="pred_risk_filter"
        )
    
    with col_filter2:
        limit = st.selectbox(
            "Show entries",
            options=[25, 50, 100, 200],
            key="pred_limit"
        )
    
    # Get filtered predictions from database
    risk_level = None if risk_filter == "All" else risk_filter
    predictions = get_predictions(limit=limit, risk_level=risk_level)
    
    if predictions:
        # Convert to DataFrame for display
        df = pd.DataFrame(predictions)
        
        # Format columns
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
        
        if 'risk_probability' in df.columns:
            df['risk_probability'] = df['risk_probability'].apply(lambda x: f"{x*100:.1f}%")
        
        if 'alert_generated' in df.columns:
            df['alert_generated'] = df['alert_generated'].apply(lambda x: "✅ Yes" if x else "❌ No")
        
        # Select and rename columns for display (database uses user_name instead of user)
        display_columns = ['timestamp', 'user_name', 'risk_level', 'risk_probability', 
                          'alert_generated', 'symptom_count', 'condition_count']
        display_columns = [c for c in display_columns if c in df.columns]
        
        column_names = {
            'timestamp': 'Time',
            'user_name': 'User',
            'risk_level': 'Risk Level',
            'risk_probability': 'Probability',
            'alert_generated': 'Alert',
            'symptom_count': 'Symptoms',
            'condition_count': 'Conditions'
        }
        
        df_display = df[display_columns].rename(columns=column_names)
        
        # Add color coding for risk level
        def highlight_risk(row):
            colors = {
                'Low': 'background-color: #d4edda',
                'Medium': 'background-color: #fff3cd',
                'High': 'background-color: #f8d7da'
            }
            risk = row.get('Risk Level', 'Low')
            return [colors.get(risk, '')] * len(row)
        
        st.dataframe(
            df_display.style.apply(highlight_risk, axis=1),
            use_container_width=True,
            hide_index=True
        )
        
        st.caption(f"Showing {len(df_display)} of {len(predictions)} entries")
    else:
        st.info("📭 No prediction logs found")


def render_alert_logs():
    """Render alert logs table from database."""
    st.subheader("🚨 Recent Alerts")
    
    alerts = get_alerts(limit=50)
    
    if alerts:
        df = pd.DataFrame(alerts)
        
        # Format columns
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
        
        if 'recommendations' in df.columns:
            df['recommendations'] = df['recommendations'].apply(
                lambda x: f"{len(x)} recommendations" if isinstance(x, list) else "N/A"
            )
        
        # Select columns for display (database uses user_name instead of user)
        display_columns = ['timestamp', 'user_name', 'risk_level', 'alert_message']
        display_columns = [c for c in display_columns if c in df.columns]
        
        column_names = {
            'timestamp': 'Time',
            'user_name': 'User',
            'risk_level': 'Risk Level',
            'alert_message': 'Alert Message'
        }
        
        df_display = df[display_columns].rename(columns=column_names)
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        st.caption(f"Showing {len(df_display)} alerts")
    else:
        st.info("📭 No alert logs found")


def render_quality_report():
    """Render a quality improvement report."""
    user = get_current_user()
    
    if not user or not user.is_admin():
        return
    
    logger = get_logger()
    stats = logger.get_statistics()
    
    st.subheader("📝 Quality Improvement Report")
    
    report = f"""
    ### CDSS Quality Report
    **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
    
    #### Summary Statistics
    - **Total Predictions Made:** {stats['total_predictions']}
    - **Total Alerts Generated:** {stats['total_alerts']}
    - **Alert Rate:** {stats['alert_rate']}%
    
    #### Risk Distribution
    - 🟢 **Low Risk:** {stats['risk_distribution']['Low']} ({stats.get('risk_percentages', {}).get('Low', 0)}%)
    - 🟡 **Medium Risk:** {stats['risk_distribution']['Medium']} ({stats.get('risk_percentages', {}).get('Medium', 0)}%)
    - 🔴 **High Risk:** {stats['risk_distribution']['High']} ({stats.get('risk_percentages', {}).get('High', 0)}%)
    
    #### Recommendations
    - Monitor high-risk case trends
    - Review alert acknowledgment rates
    - Assess prediction accuracy through clinical feedback
    """
    
    st.markdown(report)
    
    # Download button for report
    st.download_button(
        label="📥 Download Report",
        data=report,
        file_name=f"cdss_quality_report_{datetime.now().strftime('%Y%m%d')}.md",
        mime="text/markdown"
    )
