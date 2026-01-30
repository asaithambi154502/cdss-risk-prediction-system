"""
XAI Explanation Display Component for CDSS

Displays SHAP/LIME explanations with interactive visualizations
to help clinicians understand why the AI made its prediction.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from cdss_config import XAI_CONFIG


def render_explanation_section(explanation, show_chart: bool = True,
                               show_narrative: bool = True):
    """
    Render the XAI explanation section.
    
    Args:
        explanation: Explanation object from the explainer module
        show_chart: Whether to show the feature importance chart
        show_narrative: Whether to show the narrative explanation
    """
    if explanation is None:
        st.info("🔍 No explanation available. Click 'Generate Explanation' to analyze this prediction.")
        return
    
    st.markdown("### 🧠 AI Explanation")
    st.markdown(f"*Analysis method: {explanation.method.upper()}*")
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["📊 Visual Analysis", "📝 Narrative", "📋 Details"])
    
    with tab1:
        if show_chart and explanation.top_factors:
            render_feature_importance_chart(explanation)
    
    with tab2:
        if show_narrative and explanation.narrative:
            render_narrative_explanation(explanation)
    
    with tab3:
        render_explanation_details(explanation)


def render_feature_importance_chart(explanation):
    """
    Render horizontal bar chart showing feature contributions.
    
    Args:
        explanation: Explanation object with top_factors
    """
    if not explanation.top_factors:
        st.info("No feature contributions available.")
        return
    
    # Prepare data
    factors = explanation.top_factors
    labels = [f.display_name for f in factors]
    values = [f.contribution for f in factors]
    colors = ['#dc3545' if v > 0 else '#28a745' for v in values]
    
    # Create horizontal bar chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=labels,
        x=values,
        orientation='h',
        marker_color=colors,
        text=[f"{abs(v):.3f}" for v in values],
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Contribution: %{x:.4f}<extra></extra>'
    ))
    
    fig.update_layout(
        title={
            'text': f'Top Factors Contributing to {explanation.risk_level} Risk',
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis_title='Contribution to Risk Score',
        yaxis_title='Clinical Factor',
        height=300 + len(factors) * 30,
        showlegend=False,
        xaxis=dict(zeroline=True, zerolinewidth=2, zerolinecolor='gray'),
        margin=dict(l=20, r=20, t=60, b=40)
    )
    
    # Add annotations
    fig.add_annotation(
        x=max(values) * 0.5 if max(values) > 0 else 0.1,
        y=-0.5,
        text="→ Increases Risk",
        showarrow=False,
        font=dict(color='#dc3545', size=10)
    )
    fig.add_annotation(
        x=min(values) * 0.5 if min(values) < 0 else -0.1,
        y=-0.5,
        text="← Decreases Risk",
        showarrow=False,
        font=dict(color='#28a745', size=10)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Add legend
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("🔴 **Red bars**: Factors that **increase** risk")
    with col2:
        st.markdown("🟢 **Green bars**: Factors that **decrease** risk")


def render_narrative_explanation(explanation):
    """
    Render the natural language explanation.
    
    Args:
        explanation: Explanation object with narrative
    """
    st.markdown("#### Understanding This Prediction")
    
    # Display narrative with appropriate styling
    st.markdown(explanation.narrative)
    
    # Add confidence indicator
    confidence_pct = int(explanation.confidence * 100)
    
    st.markdown("---")
    st.markdown(f"**Model Confidence:** {confidence_pct}%")
    
    # Progress bar for confidence
    st.progress(explanation.confidence)
    
    if confidence_pct >= 80:
        st.success("High confidence prediction")
    elif confidence_pct >= 60:
        st.info("Moderate confidence - consider additional review")
    else:
        st.warning("Lower confidence - exercise clinical judgment")


def render_explanation_details(explanation):
    """
    Render detailed explanation data.
    
    Args:
        explanation: Explanation object
    """
    st.markdown("#### Detailed Factor Analysis")
    
    # Table of all contributing factors
    if explanation.top_factors:
        for factor in explanation.top_factors:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"**{factor.display_name}**")
                
                with col2:
                    # Display value
                    if isinstance(factor.value, float):
                        st.markdown(f"Value: `{factor.value:.2f}`")
                    else:
                        st.markdown(f"Value: `{factor.value}`")
                
                with col3:
                    # Display contribution with color
                    if factor.direction == "increases_risk":
                        st.markdown(f"🔺 +{abs(factor.contribution):.4f}")
                    else:
                        st.markdown(f"🔻 -{abs(factor.contribution):.4f}")
                
                st.markdown("---")
    
    # Show all contributions in expander
    with st.expander("View All Feature Contributions"):
        if explanation.all_contributions:
            sorted_contribs = sorted(
                explanation.all_contributions.items(),
                key=lambda x: abs(x[1]),
                reverse=True
            )
            for feature, contrib in sorted_contribs:
                direction = "↑" if contrib > 0 else "↓"
                st.text(f"{feature}: {direction} {contrib:.6f}")


def render_explanation_button(on_click_callback):
    """
    Render button to generate explanation on demand.
    
    Args:
        on_click_callback: Function to call when button is clicked
    """
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("🔍 Generate AI Explanation", 
                     use_container_width=True,
                     help="Analyze the factors contributing to this prediction"):
            on_click_callback()


def render_compact_explanation(explanation):
    """
    Render a compact version of the explanation for inline display.
    
    Args:
        explanation: Explanation object
    """
    if explanation is None:
        return
    
    st.markdown("##### Key Factors:")
    
    # Show top 3 factors only
    top_3 = explanation.top_factors[:3] if explanation.top_factors else []
    
    for factor in top_3:
        icon = "🔺" if factor.direction == "increases_risk" else "🔻"
        color = "#dc3545" if factor.direction == "increases_risk" else "#28a745"
        st.markdown(
            f"{icon} **{factor.display_name}**: "
            f"<span style='color:{color}'>{abs(factor.contribution):.3f}</span>",
            unsafe_allow_html=True
        )


def render_shap_waterfall(explanation):
    """
    Render SHAP waterfall chart if SHAP values are available.
    
    Args:
        explanation: Explanation object with SHAP data
    """
    if explanation.method != 'shap' or explanation.shap_values is None:
        st.info("Waterfall chart requires SHAP explanation")
        return
    
    # Create waterfall chart using plotly
    factors = explanation.top_factors
    
    if not factors:
        return
    
    # Prepare data for waterfall
    labels = ['Base'] + [f.display_name for f in factors] + ['Final']
    
    # Calculate cumulative values
    base_value = explanation.base_value or 0
    contributions = [f.contribution for f in factors]
    
    values = [base_value]
    cumulative = base_value
    for c in contributions:
        cumulative += c
        values.append(c)
    values.append(cumulative - sum(contributions))  # Difference for final
    
    fig = go.Figure(go.Waterfall(
        orientation='v',
        measure=['absolute'] + ['relative'] * len(contributions) + ['total'],
        x=labels,
        y=values,
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        decreasing={"marker": {"color": "#28a745"}},
        increasing={"marker": {"color": "#dc3545"}},
        totals={"marker": {"color": "#007bff"}}
    ))
    
    fig.update_layout(
        title="SHAP Waterfall Chart",
        showlegend=False,
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
