"""
Multi-Risk Dashboard Component for CDSS

Displays unified risk assessment across multiple risk types
with interactive visualizations and recommendations.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import MULTI_RISK_CONFIG


def render_multi_risk_dashboard(assessment):
    """
    Render the complete multi-risk dashboard.
    
    Args:
        assessment: MultiRiskAssessment object from the multi-risk engine
    """
    st.markdown("## 🎯 Multi-Risk Assessment Dashboard")
    
    # Overall risk header
    render_overall_risk_header(assessment)
    
    st.markdown("---")
    
    # Risk breakdown
    col1, col2 = st.columns([1, 1])
    
    with col1:
        render_risk_radar_chart(assessment)
    
    with col2:
        render_risk_cards(assessment)
    
    st.markdown("---")
    
    # Detailed analysis
    render_detailed_analysis(assessment)
    
    # Recommendations
    render_recommendations(assessment)


def render_overall_risk_header(assessment):
    """
    Render the overall risk summary header.
    
    Args:
        assessment: MultiRiskAssessment object
    """
    level = assessment.overall_risk_level
    score = assessment.overall_risk_score
    
    # Color coding
    colors = {
        "Low": {"bg": "#d4edda", "text": "#155724", "icon": "✅"},
        "Medium": {"bg": "#fff3cd", "text": "#856404", "icon": "⚠️"},
        "High": {"bg": "#f8d7da", "text": "#721c24", "icon": "🚨"}
    }
    
    style = colors.get(level, colors["Medium"])
    
    # Header card
    st.markdown(f"""
    <div style="
        background: {style['bg']};
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        margin-bottom: 20px;
    ">
        <h2 style="color: {style['text']}; margin: 0;">
            {style['icon']} Overall Risk: {level.upper()}
        </h2>
        <p style="color: {style['text']}; font-size: 1.2em; margin: 10px 0 0 0;">
            Combined Risk Score: {score*100:.1f}%
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Summary message
    if assessment.requires_immediate_attention:
        st.error(f"🚨 **{assessment.summary}**")
    else:
        st.info(assessment.summary)


def render_risk_radar_chart(assessment):
    """
    Render radar/spider chart of all risk types.
    
    Args:
        assessment: MultiRiskAssessment object
    """
    st.markdown("### 📊 Risk Profile")
    
    if not assessment.risk_results:
        st.info("No risk data available")
        return
    
    # Prepare data
    categories = []
    values = []
    colors_list = []
    
    for risk_type, result in assessment.risk_results.items():
        config = MULTI_RISK_CONFIG['risk_types'].get(risk_type, {})
        categories.append(config.get('display_name', risk_type))
        values.append(result.risk_score * 100)
        colors_list.append(config.get('color', '#6c757d'))
    
    # Close the radar
    categories_closed = categories + [categories[0]]
    values_closed = values + [values[0]]
    
    # Create radar chart
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=categories_closed,
        fill='toself',
        fillcolor='rgba(52, 152, 219, 0.3)',
        line=dict(color='#3498db', width=2),
        name='Risk Score'
    ))
    
    # Add threshold lines
    fig.add_trace(go.Scatterpolar(
        r=[30] * len(categories_closed),
        theta=categories_closed,
        line=dict(color='#28a745', width=1, dash='dot'),
        name='Low Threshold'
    ))
    
    fig.add_trace(go.Scatterpolar(
        r=[60] * len(categories_closed),
        theta=categories_closed,
        line=dict(color='#ffc107', width=1, dash='dot'),
        name='Medium Threshold'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                ticksuffix='%'
            )
        ),
        showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=-0.2),
        height=350,
        margin=dict(l=60, r=60, t=40, b=60)
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_risk_cards(assessment):
    """
    Render individual risk type cards.
    
    Args:
        assessment: MultiRiskAssessment object
    """
    st.markdown("### 📋 Risk Breakdown")
    
    for risk_type, result in assessment.risk_results.items():
        config = MULTI_RISK_CONFIG['risk_types'].get(risk_type, {})
        
        # Determine card styling
        if result.risk_level == "High":
            border_color = "#dc3545"
            bg_color = "#fff5f5"
        elif result.risk_level == "Medium":
            border_color = "#ffc107"
            bg_color = "#fffbeb"
        else:
            border_color = "#28a745"
            bg_color = "#f0fff4"
        
        with st.container():
            st.markdown(f"""
            <div style="
                border-left: 4px solid {border_color};
                background: {bg_color};
                padding: 12px 16px;
                margin-bottom: 10px;
                border-radius: 0 8px 8px 0;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 1.1em;">
                        {config.get('icon', '⚠️')} <strong>{config.get('display_name', risk_type)}</strong>
                    </span>
                    <span style="
                        background: {border_color};
                        color: white;
                        padding: 2px 10px;
                        border-radius: 12px;
                        font-size: 0.85em;
                    ">
                        {result.risk_level}
                    </span>
                </div>
                <div style="margin-top: 8px;">
                    <div style="
                        background: #e0e0e0;
                        border-radius: 4px;
                        height: 8px;
                        overflow: hidden;
                    ">
                        <div style="
                            background: {border_color};
                            width: {result.risk_score * 100}%;
                            height: 100%;
                        "></div>
                    </div>
                    <small style="color: #666;">Score: {result.risk_score*100:.1f}%</small>
                </div>
            </div>
            """, unsafe_allow_html=True)


def render_detailed_analysis(assessment):
    """
    Render detailed analysis with expandable sections.
    
    Args:
        assessment: MultiRiskAssessment object
    """
    st.markdown("### 🔍 Detailed Analysis")
    
    for risk_type, result in assessment.risk_results.items():
        config = MULTI_RISK_CONFIG['risk_types'].get(risk_type, {})
        
        with st.expander(f"{config.get('icon', '⚠️')} {config.get('display_name', risk_type)} Analysis"):
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("**Contributing Factors:**")
                if result.contributing_factors:
                    for factor in result.contributing_factors:
                        st.markdown(f"- {factor}")
                else:
                    st.markdown("_No significant risk factors identified_")
            
            with col2:
                st.markdown("**Recommendations:**")
                if result.recommendations:
                    for rec in result.recommendations:
                        st.markdown(f"- {rec}")
                else:
                    st.markdown("_Continue standard care protocol_")
            
            # Confidence indicator
            st.markdown(f"**Prediction Confidence:** {result.confidence*100:.0f}%")
            st.progress(result.confidence)


def render_recommendations(assessment):
    """
    Render consolidated recommendations from all risk types.
    
    Args:
        assessment: MultiRiskAssessment object
    """
    st.markdown("### 📝 Action Recommendations")
    
    # Prioritize by risk level
    high_risk_recs = []
    medium_risk_recs = []
    low_risk_recs = []
    
    for result in assessment.risk_results.values():
        if result.risk_level == "High":
            high_risk_recs.extend(result.recommendations)
        elif result.risk_level == "Medium":
            medium_risk_recs.extend(result.recommendations)
        else:
            low_risk_recs.extend(result.recommendations)
    
    # Remove duplicates while preserving order
    def dedupe(lst):
        seen = set()
        return [x for x in lst if not (x in seen or seen.add(x))]
    
    high_risk_recs = dedupe(high_risk_recs)
    medium_risk_recs = dedupe(medium_risk_recs)
    low_risk_recs = dedupe(low_risk_recs)
    
    if high_risk_recs:
        st.error("🚨 **Priority Actions:**")
        for rec in high_risk_recs[:5]:  # Limit to top 5
            st.markdown(f"- {rec}")
    
    if medium_risk_recs:
        st.warning("⚠️ **Recommended Actions:**")
        for rec in medium_risk_recs[:5]:
            st.markdown(f"- {rec}")
    
    if low_risk_recs and not (high_risk_recs or medium_risk_recs):
        st.success("✅ **Routine Actions:**")
        for rec in low_risk_recs[:3]:
            st.markdown(f"- {rec}")


def render_risk_comparison_chart(assessment):
    """
    Render bar chart comparing all risk types.
    
    Args:
        assessment: MultiRiskAssessment object
    """
    if not assessment.risk_results:
        return
    
    names = []
    scores = []
    colors = []
    
    for risk_type, result in assessment.risk_results.items():
        config = MULTI_RISK_CONFIG['risk_types'].get(risk_type, {})
        names.append(config.get('display_name', risk_type))
        scores.append(result.risk_score * 100)
        
        if result.risk_level == "High":
            colors.append('#dc3545')
        elif result.risk_level == "Medium":
            colors.append('#ffc107')
        else:
            colors.append('#28a745')
    
    fig = px.bar(
        x=names,
        y=scores,
        color=names,
        color_discrete_sequence=colors,
        labels={'x': 'Risk Type', 'y': 'Risk Score (%)'},
        title='Risk Comparison'
    )
    
    fig.update_layout(
        showlegend=False,
        height=300,
        yaxis_range=[0, 100]
    )
    
    # Add threshold lines
    fig.add_hline(y=30, line_dash="dot", line_color="#28a745", 
                  annotation_text="Low threshold")
    fig.add_hline(y=60, line_dash="dot", line_color="#ffc107",
                  annotation_text="Medium threshold")
    
    st.plotly_chart(fig, use_container_width=True)


def render_compact_risk_summary(assessment):
    """
    Render a compact summary suitable for sidebar or header.
    
    Args:
        assessment: MultiRiskAssessment object
    """
    level = assessment.overall_risk_level
    
    colors = {"Low": "#28a745", "Medium": "#ffc107", "High": "#dc3545"}
    icons = {"Low": "✅", "Medium": "⚠️", "High": "🚨"}
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {colors.get(level, '#6c757d')}22, white);
        border: 2px solid {colors.get(level, '#6c757d')};
        border-radius: 8px;
        padding: 10px;
        text-align: center;
    ">
        <span style="font-size: 1.5em;">{icons.get(level, '⚠️')}</span>
        <p style="margin: 5px 0 0 0; font-weight: bold; color: {colors.get(level, '#6c757d')};">
            {level} Risk
        </p>
        <small>{assessment.overall_risk_score*100:.0f}% combined score</small>
    </div>
    """, unsafe_allow_html=True)
