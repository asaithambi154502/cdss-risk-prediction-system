"""
Alert Component for CDSS

Displays clinical alerts with appropriate styling based on
risk severity, implementing alert fatigue reduction.
"""

import streamlit as st
from typing import Optional, List
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import RISK_COLORS, ALERT_CONFIG


def render_alert(
    risk_level: str,
    message: str,
    confidence: float,
    recommendations: Optional[List[str]] = None
) -> None:
    """
    Render a clinical alert based on risk level.
    
    Args:
        risk_level: Risk level (Low, Medium, High)
        message: Alert message to display
        confidence: Model confidence (0-1)
        recommendations: Optional list of recommendations
    """
    # Check if alert should be shown based on configuration
    should_show = _should_display_alert(risk_level)
    
    if not should_show:
        return
    
    color = RISK_COLORS.get(risk_level, "#6c757d")
    
    if risk_level == "High":
        _render_high_risk_alert(message, confidence, recommendations)
    elif risk_level == "Medium":
        _render_medium_risk_alert(message, confidence, recommendations)
    else:
        _render_low_risk_alert(message, confidence)


def _should_display_alert(risk_level: str) -> bool:
    """Check if alert should be displayed based on config."""
    if risk_level == "Low":
        return ALERT_CONFIG['show_low_risk']
    elif risk_level == "Medium":
        return ALERT_CONFIG['show_medium_risk']
    else:
        return ALERT_CONFIG['show_high_risk']


def _render_high_risk_alert(message: str, confidence: float, recommendations: Optional[List[str]]) -> None:
    """Render a high-risk critical alert."""
    st.markdown("""
    <style>
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(220, 53, 69, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(220, 53, 69, 0); }
        100% { box-shadow: 0 0 0 0 rgba(220, 53, 69, 0); }
    }
    .high-risk-alert {
        animation: pulse 2s infinite;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="high-risk-alert" style="
        background: linear-gradient(135deg, #dc354533, #dc354566);
        border: 2px solid #dc3545;
        border-radius: 10px;
        padding: 20px;
        margin: 15px 0;
    ">
        <h2 style="color: #dc3545; margin: 0 0 10px 0;">
            🚨 CRITICAL ALERT - HIGH RISK DETECTED
        </h2>
        <p style="color: #333; font-size: 1.1rem; margin: 10px 0;">
            {message}
        </p>
        <p style="color: #666; font-size: 0.9rem;">
            Confidence: <strong>{confidence:.1%}</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Show recommendations in an expander
    if recommendations:
        with st.expander("🔴 Recommended Actions", expanded=True):
            for rec in recommendations:
                if rec.startswith("🚨"):
                    st.error(rec)
                else:
                    st.warning(f"• {rec}")


def _render_medium_risk_alert(message: str, confidence: float, recommendations: Optional[List[str]]) -> None:
    """Render a medium-risk warning alert."""
    st.markdown("""
    <style>
    @keyframes glowWarning {
        0%, 100% { box-shadow: 0 0 5px rgba(255, 193, 7, 0.5); }
        50% { box-shadow: 0 0 20px rgba(255, 193, 7, 0.8), 0 0 30px rgba(255, 193, 7, 0.4); }
    }
    .medium-risk-alert {
        animation: glowWarning 2.5s infinite, fadeIn 0.5s ease-out;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="medium-risk-alert" style="
        background: linear-gradient(135deg, #ffc10733, #ffc10755);
        border: 2px solid #ffc107;
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
    ">
        <h3 style="color: #856404; margin: 0 0 10px 0;">
            ⚠️ WARNING - MEDIUM RISK DETECTED
        </h3>
        <p style="color: #333; font-size: 1rem; margin: 10px 0;">
            {message}
        </p>
        <p style="color: #666; font-size: 0.9rem;">
            Confidence: <strong>{confidence:.1%}</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Show recommendations in an expander
    if recommendations:
        with st.expander("🟡 Recommended Actions", expanded=False):
            for rec in recommendations:
                st.info(f"• {rec}")


def _render_low_risk_alert(message: str, confidence: float) -> None:
    """Render a low-risk informational alert (normally hidden)."""
    st.success(f"""
    ✅ **Low Risk** - {message}
    
    Confidence: {confidence:.1%}
    """)


def render_no_alert_message() -> None:
    """Render a message when no alert is needed."""
    st.markdown("""
    <style>
    @keyframes successGlow {
        0% { opacity: 0; transform: scale(0.95); }
        50% { transform: scale(1.02); }
        100% { opacity: 1; transform: scale(1); }
    }
    .success-alert {
        animation: successGlow 0.6s ease-out;
    }
    </style>
    <div class="success-alert" style="
        background: linear-gradient(135deg, #28a74522, #28a74540);
        border-left: 4px solid #28a745;
        border-radius: 0 12px 12px 0;
        padding: 15px 20px;
        margin: 10px 0;
        box-shadow: 0 4px 15px rgba(40, 167, 69, 0.15);
    ">
        <p style="color: #155724; margin: 0; font-size: 1.05rem;">
            ✅ <strong>No alerts generated</strong> - Risk level is within acceptable range.
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_alert_fatigue_info() -> None:
    """Render information about alert fatigue reduction."""
    with st.expander("ℹ️ About Alert Fatigue Reduction"):
        st.markdown("""
        This system is designed to **reduce alert fatigue** by only showing alerts when necessary:
        
        - **Low Risk**: No alert shown (reduces unnecessary notifications)
        - **Medium Risk**: Warning alert with recommendations
        - **High Risk**: Critical alert requiring immediate attention
        
        This approach helps healthcare professionals focus on truly important cases
        and reduces the risk of ignoring alerts due to notification overload.
        """)


def render_alert_statistics(stats: dict) -> None:
    """
    Render alert statistics.
    
    Args:
        stats: Dictionary with alert statistics
    """
    if not stats or stats.get('total_alerts', 0) == 0:
        return
        
    st.subheader("📈 Alert Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Alerts", stats['total_alerts'])
    
    with col2:
        st.metric("High Risk Alerts", stats.get('high_risk_alerts', 0))
    
    with col3:
        st.metric("Medium Risk Alerts", stats.get('medium_risk_alerts', 0))
