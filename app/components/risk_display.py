"""
Risk Display Component for CDSS

Displays risk assessment results with visual indicators,
gauges, and probability charts.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import RISK_COLORS


def render_risk_gauge(risk_score: float, risk_label: str) -> None:
    """
    Render a gauge chart showing the risk score.
    
    Args:
        risk_score: Risk score between 0 and 1
        risk_label: Risk label (Low, Medium, High)
    """
    color = RISK_COLORS.get(risk_label, "#6c757d")
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=risk_score * 100,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Risk Score", 'font': {'size': 20}},
        number={'suffix': "%", 'font': {'size': 40}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 30], 'color': RISK_COLORS['Low']},
                {'range': [30, 60], 'color': RISK_COLORS['Medium']},
                {'range': [60, 100], 'color': RISK_COLORS['High']}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': risk_score * 100
            }
        }
    ))
    
    fig.update_layout(
        height=250,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        font={'color': "#333", 'family': "Arial"}
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_risk_badge(risk_label: str, confidence: float) -> None:
    """
    Render a prominent risk level badge.
    
    Args:
        risk_label: Risk label (Low, Medium, High)
        confidence: Model confidence (0-1)
    """
    color = RISK_COLORS.get(risk_label, "#6c757d")
    
    # Emoji based on risk level
    emoji = {"Low": "✅", "Medium": "⚠️", "High": "🚨"}.get(risk_label, "❓")
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {color}22, {color}44);
        border-left: 5px solid {color};
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        margin: 10px 0;
    ">
        <h1 style="color: {color}; margin: 0; font-size: 2.5rem;">
            {emoji} {risk_label.upper()} RISK
        </h1>
        <p style="color: #666; margin: 10px 0 0 0; font-size: 1.1rem;">
            Model Confidence: <strong>{confidence:.1%}</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_probability_chart(probabilities: Dict[str, float]) -> None:
    """
    Render a bar chart showing probabilities for each risk level.
    
    Args:
        probabilities: Dictionary with risk level probabilities
    """
    st.subheader("📊 Risk Probability Distribution")
    
    fig = go.Figure(data=[
        go.Bar(
            x=list(probabilities.keys()),
            y=[v * 100 for v in probabilities.values()],
            marker_color=[RISK_COLORS.get(k, "#6c757d") for k in probabilities.keys()],
            text=[f"{v*100:.1f}%" for v in probabilities.values()],
            textposition='auto',
        )
    ])
    
    fig.update_layout(
        xaxis_title="Risk Level",
        yaxis_title="Probability (%)",
        yaxis_range=[0, 100],
        height=300,
        margin=dict(l=20, r=20, t=20, b=40),
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_feature_importance(importance_dict: Dict[str, float], top_n: int = 10) -> None:
    """
    Render feature importance chart.
    
    Args:
        importance_dict: Dictionary of feature names to importance scores
        top_n: Number of top features to display
    """
    if not importance_dict:
        return
        
    st.subheader("🔍 Key Contributing Factors")
    
    # Sort and get top features
    sorted_features = sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)[:top_n]
    features, importances = zip(*sorted_features)
    
    fig = go.Figure(data=[
        go.Bar(
            x=list(importances),
            y=list(features),
            orientation='h',
            marker_color='#3498db',
            text=[f"{v:.1%}" for v in importances],
            textposition='outside'
        )
    ])
    
    fig.update_layout(
        xaxis_title="Importance",
        yaxis_title="",
        height=max(300, len(features) * 30),
        margin=dict(l=20, r=60, t=20, b=40),
        yaxis={'categoryorder': 'total ascending'}
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_risk_summary(assessment_summary: Dict) -> None:
    """
    Render a complete risk summary with all components.
    
    Args:
        assessment_summary: Dictionary from RiskClassifier.get_risk_summary()
    """
    col1, col2 = st.columns([1, 1])
    
    with col1:
        render_risk_badge(
            assessment_summary['risk_level'],
            assessment_summary['confidence'] / 100
        )
        
    with col2:
        render_risk_gauge(
            assessment_summary['risk_score'],
            assessment_summary['risk_level']
        )
    
    # Probability distribution
    render_probability_chart(
        {k: v/100 for k, v in assessment_summary['probabilities'].items()}
    )


def render_recommendations(recommendations: list) -> None:
    """
    Render clinical recommendations.
    
    Args:
        recommendations: List of recommendation strings
    """
    if not recommendations:
        return
        
    st.subheader("📋 Recommendations")
    
    for rec in recommendations:
        if rec.startswith("🚨"):
            st.error(rec)
        elif rec.startswith("⚠️"):
            st.warning(rec)
        else:
            st.info(f"• {rec}")
