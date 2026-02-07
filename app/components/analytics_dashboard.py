"""
Analytics Dashboard Component for CDSS

Displays prediction statistics, trends, and historical data
from the SQLite database.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, List, Any
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.database.db import (
    get_statistics,
    get_predictions,
    get_alerts,
    get_prediction_trends,
    export_predictions_csv,
    export_predictions_excel,
    get_total_records
)


def render_analytics_dashboard() -> None:
    """Render the main analytics dashboard."""
    st.header("📊 System Analytics Dashboard")
    st.markdown("""
    Monitor system performance, prediction statistics, and historical trends.
    All data is anonymized - no patient identifiers are stored.
    """)
    
    # Get statistics
    try:
        stats = get_statistics()
    except Exception as e:
        st.error(f"Error loading statistics: {e}")
        return
    
    # Key metrics row
    render_key_metrics(stats)
    
    st.divider()
    
    # Charts row
    col1, col2 = st.columns(2)
    
    with col1:
        render_risk_distribution_chart(stats.get('risk_distribution', {}))
    
    with col2:
        render_alert_distribution_chart(stats.get('alert_distribution', {}))
    
    st.divider()
    
    # Trends chart
    render_prediction_trends_chart()
    
    st.divider()
    
    # Recent predictions table
    render_recent_predictions()
    
    st.divider()
    
    # Export section
    render_export_section()


def render_key_metrics(stats: Dict[str, Any]) -> None:
    """Render the key metrics cards."""
    st.subheader("📈 Key Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #0077b6, #023e8a);
                    padding: 1.5rem; border-radius: 16px; text-align: center;
                    box-shadow: 0 4px 15px rgba(0, 119, 182, 0.3);">
            <p style="color: rgba(255,255,255,0.8); margin: 0; font-size: 0.9rem;">Total Predictions</p>
            <h2 style="color: white; margin: 0.5rem 0; font-size: 2.5rem;">{}</h2>
            <p style="color: rgba(255,255,255,0.7); margin: 0; font-size: 0.8rem;">All time</p>
        </div>
        """.format(stats.get('total_predictions', 0)), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #28a745, #20c997);
                    padding: 1.5rem; border-radius: 16px; text-align: center;
                    box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);">
            <p style="color: rgba(255,255,255,0.8); margin: 0; font-size: 0.9rem;">Today's Predictions</p>
            <h2 style="color: white; margin: 0.5rem 0; font-size: 2.5rem;">{}</h2>
            <p style="color: rgba(255,255,255,0.7); margin: 0; font-size: 0.8rem;">{}</p>
        </div>
        """.format(
            stats.get('today_predictions', 0),
            datetime.now().strftime('%b %d, %Y')
        ), unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #dc3545, #c82333);
                    padding: 1.5rem; border-radius: 16px; text-align: center;
                    box-shadow: 0 4px 15px rgba(220, 53, 69, 0.3);">
            <p style="color: rgba(255,255,255,0.8); margin: 0; font-size: 0.9rem;">High Risk Rate</p>
            <h2 style="color: white; margin: 0.5rem 0; font-size: 2.5rem;">{}%</h2>
            <p style="color: rgba(255,255,255,0.7); margin: 0; font-size: 0.8rem;">Of all predictions</p>
        </div>
        """.format(stats.get('high_risk_rate', 0)), unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #ffc107, #fd7e14);
                    padding: 1.5rem; border-radius: 16px; text-align: center;
                    box-shadow: 0 4px 15px rgba(255, 193, 7, 0.3);">
            <p style="color: rgba(255,255,255,0.8); margin: 0; font-size: 0.9rem;">Total Alerts</p>
            <h2 style="color: white; margin: 0.5rem 0; font-size: 2.5rem;">{}</h2>
            <p style="color: rgba(255,255,255,0.7); margin: 0; font-size: 0.8rem;">Alert rate: {}%</p>
        </div>
        """.format(
            stats.get('total_alerts', 0),
            stats.get('alert_rate', 0)
        ), unsafe_allow_html=True)


def render_risk_distribution_chart(risk_distribution: Dict[str, int]) -> None:
    """Render a pie chart of risk level distribution."""
    st.subheader("🎯 Risk Level Distribution")
    
    if not risk_distribution:
        st.info("No prediction data available yet.")
        return
    
    colors = {
        'Low': '#28a745',
        'Medium': '#ffc107',
        'High': '#dc3545'
    }
    
    labels = list(risk_distribution.keys())
    values = list(risk_distribution.values())
    chart_colors = [colors.get(label, '#6c757d') for label in labels]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        marker=dict(colors=chart_colors),
        textinfo='label+percent',
        textposition='outside',
        pull=[0.05 if l == 'High' else 0 for l in labels]
    )])
    
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=-0.2),
        height=350,
        margin=dict(t=20, b=60, l=20, r=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_alert_distribution_chart(alert_distribution: Dict[str, int]) -> None:
    """Render a bar chart of alerts by risk level."""
    st.subheader("🔔 Alerts by Risk Level")
    
    if not alert_distribution:
        st.info("No alert data available yet.")
        return
    
    colors = {
        'Low': '#28a745',
        'Medium': '#ffc107',
        'High': '#dc3545'
    }
    
    labels = list(alert_distribution.keys())
    values = list(alert_distribution.values())
    chart_colors = [colors.get(label, '#6c757d') for label in labels]
    
    fig = go.Figure(data=[go.Bar(
        x=labels,
        y=values,
        marker_color=chart_colors,
        text=values,
        textposition='auto'
    )])
    
    fig.update_layout(
        xaxis_title="Risk Level",
        yaxis_title="Number of Alerts",
        height=350,
        margin=dict(t=20, b=40, l=40, r=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_prediction_trends_chart() -> None:
    """Render a line chart of prediction trends over time."""
    st.subheader("📈 Prediction Trends (Last 7 Days)")
    
    try:
        trends = get_prediction_trends(days=7)
    except Exception as e:
        st.error(f"Error loading trends: {e}")
        return
    
    if not trends:
        st.info("Not enough data to show trends. Make some predictions first!")
        return
    
    dates = [t['date'] for t in trends]
    
    fig = go.Figure()
    
    # Add traces for each risk level
    fig.add_trace(go.Scatter(
        x=dates,
        y=[t['low_risk'] for t in trends],
        name='Low Risk',
        line=dict(color='#28a745', width=3),
        mode='lines+markers',
        fill='tozeroy',
        fillcolor='rgba(40, 167, 69, 0.1)'
    ))
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=[t['medium_risk'] for t in trends],
        name='Medium Risk',
        line=dict(color='#ffc107', width=3),
        mode='lines+markers'
    ))
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=[t['high_risk'] for t in trends],
        name='High Risk',
        line=dict(color='#dc3545', width=3),
        mode='lines+markers'
    ))
    
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Number of Predictions",
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        height=400,
        margin=dict(t=60, b=40, l=40, r=20),
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_recent_predictions() -> None:
    """Render a table of recent predictions."""
    st.subheader("📋 Recent Predictions")
    
    # Filter options
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        limit = st.selectbox("Show", [10, 25, 50, 100], index=0, key="analytics_pred_limit")
    
    with col2:
        risk_filter = st.selectbox(
            "Risk Level",
            ["All", "Low", "Medium", "High"],
            index=0,
            key="analytics_pred_risk_filter"
        )
    
    try:
        predictions = get_predictions(
            limit=limit,
            risk_level=None if risk_filter == "All" else risk_filter
        )
    except Exception as e:
        st.error(f"Error loading predictions: {e}")
        return
    
    if not predictions:
        st.info("No predictions found.")
        return
    
    # Format for display
    display_data = []
    for pred in predictions:
        risk_color = {
            'Low': '🟢',
            'Medium': '🟡',
            'High': '🔴'
        }.get(pred.get('risk_level', ''), '⚪')
        
        display_data.append({
            'Patient ID': pred.get('patient_id', '-') or '-',
            'Doctor ID': pred.get('doctor_id', '-') or '-',
            'Time': pred.get('timestamp', '')[:19] if pred.get('timestamp') else '-',
            'Risk': f"{risk_color} {pred.get('risk_level', '')}",
            'Confidence': f"{pred.get('risk_probability', 0):.1%}" if pred.get('risk_probability') else 'N/A',
            'HR': pred.get('heart_rate', '-'),
            'BP': f"{pred.get('blood_pressure_systolic', '-')}/{pred.get('blood_pressure_diastolic', '-')}",
            'SpO2': f"{pred.get('oxygen_saturation', '-')}%",
            'Alert': '🔔' if pred.get('alert_generated') else '-'
        })
    
    st.dataframe(
        display_data,
        use_container_width=True,
        hide_index=True
    )


def render_export_section() -> None:
    """Render the data export section."""
    st.subheader("📥 Export Data")
    
    # Show total records count
    total_records = get_total_records()
    st.markdown(f"**Total Records in Database:** {total_records}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Excel Export Button
        excel_data = export_predictions_excel()
        if excel_data:
            st.download_button(
                label="📊 Download All Records (Excel)",
                data=excel_data,
                file_name="patient_records.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                type="primary"
            )
        else:
            st.info("No records to export yet.")
    
    with col2:
        # CSV Export with date range
        start_date = st.date_input(
            "Start Date",
            value=datetime.now() - timedelta(days=30),
            key="analytics_export_start"
        )
        
        end_date = st.date_input(
            "End Date",
            value=datetime.now(),
            key="analytics_export_end"
        )
        
        if st.button("📄 Export Date Range (CSV)", use_container_width=True):
            try:
                csv_data = export_predictions_csv(
                    start_date=start_date.isoformat(),
                    end_date=end_date.isoformat()
                )
                
                if csv_data:
                    st.download_button(
                        label="⬇️ Download CSV",
                        data=csv_data,
                        file_name=f"cdss_predictions_{start_date}_{end_date}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                else:
                    st.warning("No data found for the selected date range.")
            except Exception as e:
                st.error(f"Export error: {e}")
    
    # Privacy notice
    st.markdown("""
    <div style="background: #e3f2fd; padding: 1rem; border-radius: 8px; 
                border: 1px solid #90caf9; margin-top: 1rem;">
        <p style="color: #1565c0; margin: 0; font-size: 0.85rem;">
            🔒 <strong>Privacy Notice:</strong> Exported data includes Patient ID and Doctor ID 
            for tracking purposes. All clinical data is stored securely.
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_high_risk_vitals_summary(vitals: Dict[str, float]) -> None:
    """Render average vital signs for high-risk cases."""
    if not vitals:
        return
    
    st.subheader("🏥 High-Risk Case Vital Signs (Averages)")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Avg Heart Rate", f"{vitals.get('avg_heart_rate', 0)} bpm")
    
    with col2:
        st.metric("Avg Systolic BP", f"{vitals.get('avg_bp_systolic', 0)} mmHg")
    
    with col3:
        st.metric("Avg Temperature", f"{vitals.get('avg_temperature', 0)}°C")
    
    with col4:
        st.metric("Avg SpO2", f"{vitals.get('avg_spo2', 0)}%")
