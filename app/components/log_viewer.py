"""
Log Viewer Component for CDSS

Provides admin dashboard for viewing prediction and alert logs.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.utils.logger import get_logger
from app.auth import get_current_user, UserRole


def render_log_viewer():
    """Render the log viewer dashboard (admin only)."""
    user = get_current_user()
    
    if not user or not user.is_admin():
        st.error("🚫 Access Denied: Only administrators can view logs.")
        return
    
    st.header("📊 System Logs & Analytics")
    st.caption("View prediction history and system statistics")
    
    logger = get_logger()
    
    # Statistics overview
    stats = logger.get_statistics()
    
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
        high_risk_pct = stats.get('risk_percentages', {}).get('High', 0)
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
            risk_data = pd.DataFrame({
                'Risk Level': ['Low', 'Medium', 'High'],
                'Count': [
                    stats['risk_distribution']['Low'],
                    stats['risk_distribution']['Medium'],
                    stats['risk_distribution']['High']
                ],
                'Color': ['#28a745', '#ffc107', '#dc3545']
            })
            
            st.bar_chart(risk_data.set_index('Risk Level')['Count'])
        
        with col_chart2:
            st.markdown("**Distribution Breakdown:**")
            for level in ['Low', 'Medium', 'High']:
                count = stats['risk_distribution'][level]
                pct = stats['risk_percentages'][level]
                color = {'Low': '🟢', 'Medium': '🟡', 'High': '🔴'}[level]
                st.markdown(f"{color} **{level}**: {count} ({pct}%)")
    
    st.divider()
    
    # Tabs for different log views
    tab1, tab2 = st.tabs(["📋 Prediction History", "🚨 Alert History"])
    
    with tab1:
        render_prediction_logs(logger)
    
    with tab2:
        render_alert_logs(logger)
    
    st.divider()
    
    # Admin actions
    st.subheader("⚙️ Admin Actions")
    
    col_action1, col_action2, col_action3 = st.columns(3)
    
    with col_action1:
        if st.button("🔄 Refresh Logs", use_container_width=True):
            st.rerun()
    
    with col_action3:
        with st.expander("⚠️ Danger Zone"):
            st.warning("This action cannot be undone!")
            if st.button("🗑️ Clear All Logs", type="secondary"):
                logger.clear_logs()
                st.success("✅ All logs cleared")
                st.rerun()


def render_prediction_logs(logger):
    """Render prediction logs table."""
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
    
    # Get filtered predictions
    risk_level = None if risk_filter == "All" else risk_filter
    predictions = logger.get_predictions(limit=limit, risk_level=risk_level)
    
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
        
        # Select and rename columns for display
        display_columns = ['timestamp', 'user', 'risk_level', 'risk_probability', 
                          'alert_generated', 'symptom_count', 'condition_count']
        display_columns = [c for c in display_columns if c in df.columns]
        
        column_names = {
            'timestamp': 'Time',
            'user': 'User',
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


def render_alert_logs(logger):
    """Render alert logs table."""
    st.subheader("🚨 Recent Alerts")
    
    alerts = logger.get_alerts(limit=50)
    
    if alerts:
        df = pd.DataFrame(alerts)
        
        # Format columns
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
        
        if 'recommendations' in df.columns:
            df['recommendations'] = df['recommendations'].apply(
                lambda x: f"{len(x)} recommendations" if isinstance(x, list) else "N/A"
            )
        
        # Select columns for display
        display_columns = ['timestamp', 'user', 'risk_level', 'alert_message']
        display_columns = [c for c in display_columns if c in df.columns]
        
        column_names = {
            'timestamp': 'Time',
            'user': 'User',
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
