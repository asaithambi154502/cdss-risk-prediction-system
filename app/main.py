"""
CDSS - Clinical Decision Support System
Main Streamlit Application

AI-Based Medical Error Risk Prediction System
Enhanced with XAI, Multi-Risk Engine, FHIR Support, and Hybrid Intelligence
"""

import streamlit as st
import sys
from pathlib import Path
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import PAGE_CONFIG, MODEL_PATH, ENCODER_PATH, XAI_CONFIG
from app.components.input_form import render_complete_form
from app.components.risk_display import (
    render_risk_summary, 
    render_feature_importance,
    render_recommendations
)
from app.components.alert_component import (
    render_alert, 
    render_no_alert_message,
    render_alert_fatigue_info
)
from app.components.login_page import render_login_page, render_user_info_sidebar
from app.components.log_viewer import render_log_viewer
from app.utils.validators import validate_patient_data, get_data_summary
from app.utils.logger import get_logger, log_prediction, log_alert
from ml.risk_classifier import RiskClassifier, AlertEngine
from app.auth import is_authenticated, get_current_user, UserRole

# New enhanced components
from app.components.explanation_display import render_explanation_section, render_compact_explanation
from app.components.multi_risk_dashboard import render_multi_risk_dashboard, render_compact_risk_summary
from app.components.fhir_import import render_fhir_import_section, render_fhir_data_preview
from ml.explainer import RiskExplainer, create_demo_explanation
from ml.multi_risk_engine import MultiRiskEngine
from ml.rules_engine import ClinicalRulesEngine, HybridDecisionEngine
from ml.alert_prioritization import SmartAlertEngine
from app.fhir.fhir_converter import FHIRConverter


def load_model():
    """Load the trained model or create a demo model."""
    try:
        from ml.model import RiskPredictionModel
        
        if MODEL_PATH.exists() and ENCODER_PATH.exists():
            return RiskPredictionModel.load()
        else:
            # Train a new model with sample data for demo
            st.sidebar.warning("⚠️ No trained model found. Training demo model...")
            from data.generate_data import generate_sample_data
            
            df = generate_sample_data(n_samples=500)
            model = RiskPredictionModel(model_type='random_forest')
            model.train(df)
            model.save()
            st.sidebar.success("✅ Demo model trained!")
            return model
    except Exception as e:
        st.error(f"Error loading model: {e}")
        return None


def render_sidebar():
    """Render the sidebar with app info and settings."""
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/hospital-2.png", width=80)
        st.title("CDSS")
        st.caption("Clinical Decision Support System")
        
        st.divider()
        
        # User info and logout
        if is_authenticated():
            render_user_info_sidebar()
            st.divider()
        
        st.subheader("ℹ️ About")
        st.markdown("""
        This AI-powered system helps healthcare professionals 
        assess the risk of medical errors based on:
        - Patient symptoms
        - Vital signs
        - Medical history
        
        **Note:** This is a decision support tool and 
        does not replace clinical judgment.
        """)
        
        st.divider()
        
        # Alert fatigue info
        render_alert_fatigue_info()
        
        st.divider()
        
        # Privacy notice
        st.markdown("""
        <div style="background: #e3f2fd; padding: 10px; border-radius: 8px; border: 1px solid #90caf9;">
            <p style="color: #1565c0; margin: 0; font-size: 0.8rem;">
                🔒 <strong>Privacy Notice:</strong> Patient data is not stored. 
                All information is processed in-session only.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        st.caption("© 2024 CDSS Risk Prediction System")
        st.caption("For educational purposes only")


def render_patient_summary(summary: dict):
    """Render patient data summary."""
    with st.expander("📋 Patient Summary", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            **Demographics:**
            - Age: {summary['age']} years
            - Gender: {summary['gender']}
            
            **Vital Signs:**
            - Heart Rate: {summary['heart_rate']} bpm
            - Blood Pressure: {summary['blood_pressure']} mmHg
            - Temperature: {summary['temperature']}°C
            - SpO2: {summary['oxygen_saturation']}%
            """)
        
        with col2:
            st.markdown(f"""
            **Symptoms ({summary['symptom_count']}):**
            {', '.join(summary['symptoms']) if summary['symptoms'] else 'None reported'}
            
            **Pre-existing Conditions ({summary['condition_count']}):**
            {', '.join(summary['conditions'])}
            """)


def render_navigation():
    """Render navigation tabs for different views."""
    user = get_current_user()
    
    if user and user.is_admin():
        # Admin sees additional tabs
        tab1, tab2 = st.tabs(["🏥 Risk Assessment", "📊 System Logs"])
        return tab1, tab2
    else:
        return None, None


def main():
    """Main application entry point."""
    # Page configuration
    st.set_page_config(**PAGE_CONFIG)
    
    # Custom CSS for healthcare-themed styling with animations
    st.markdown("""
    <style>
    /* ========================================
       HIDE STREAMLIT BRANDING
       Remove default menu, footer, header
    ======================================== */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* ========================================
       HEALTHCARE THEME - Color Palette
       Primary: #0077b6 (Medical Blue)
       Secondary: #28a745 (Health Green)
       Accent: #00b4d8 (Light Blue)
       Warning: #ffc107, Critical: #dc3545
    ======================================== */
    
    /* ========================================
       GLOBAL ANIMATIONS
    ======================================== */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes slideUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes slideInRight {
        from { opacity: 0; transform: translateX(30px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(0, 119, 182, 0.4); }
        70% { box-shadow: 0 0 0 15px rgba(0, 119, 182, 0); }
        100% { box-shadow: 0 0 0 0 rgba(0, 119, 182, 0); }
    }
    
    @keyframes glow {
        0%, 100% { box-shadow: 0 0 5px rgba(0, 180, 216, 0.5); }
        50% { box-shadow: 0 0 20px rgba(0, 180, 216, 0.8); }
    }
    
    @keyframes shimmer {
        0% { background-position: -200% 0; }
        100% { background-position: 200% 0; }
    }
    
    @keyframes successPop {
        0% { transform: scale(0.8); opacity: 0; }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); opacity: 1; }
    }
    
    /* NEW: Breathing effect for alerts */
    @keyframes breathe {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.9; transform: scale(1.01); }
    }
    
    /* NEW: Alert attention effect */
    @keyframes alertAttention {
        0%, 100% { box-shadow: 0 4px 15px rgba(220, 53, 69, 0.3); }
        50% { box-shadow: 0 4px 25px rgba(220, 53, 69, 0.6); }
    }
    
    /* NEW: Animated progress bar */
    @keyframes progressFill {
        from { width: 0%; }
        to { width: var(--progress-width, 100%); }
    }
    
    /* NEW: Counter animation for numbers */
    @keyframes countUp {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* NEW: Ripple effect */
    @keyframes ripple {
        0% { transform: scale(0.8); opacity: 1; }
        100% { transform: scale(2); opacity: 0; }
    }
    
    /* NEW: Heartbeat for critical alerts */
    @keyframes heartbeat {
        0%, 100% { transform: scale(1); }
        14% { transform: scale(1.1); }
        28% { transform: scale(1); }
        42% { transform: scale(1.1); }
        70% { transform: scale(1); }
    }
    
    /* ========================================
       MAIN CONTAINER & HEADINGS
    ======================================== */
    .main > div {
        padding-top: 2rem;
        animation: fadeIn 0.5s ease-out;
    }
    
    h1 {
        color: #023e8a;
        animation: slideUp 0.6s ease-out;
    }
    h2, h3 {
        color: #0077b6;
        animation: fadeIn 0.4s ease-out;
    }
    
    /* ========================================
       PROFESSIONAL BUTTON STYLING
    ======================================== */
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #0077b6 0%, #023e8a 100%);
        color: white;
        font-weight: bold;
        padding: 0.75rem 1.5rem;
        font-size: 1.1rem;
        border: none;
        border-radius: 12px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 15px rgba(0, 119, 182, 0.3);
        position: relative;
        overflow: hidden;
    }
    .stButton > button::after {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 0;
        height: 0;
        background: rgba(255, 255, 255, 0.2);
        border-radius: 50%;
        transform: translate(-50%, -50%);
        transition: width 0.4s, height 0.4s;
    }
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0, 119, 182, 0.5);
        background: linear-gradient(135deg, #0096c7 0%, #0077b6 100%);
    }
    .stButton > button:hover::after {
        width: 300px;
        height: 300px;
    }
    .stButton > button:active {
        transform: translateY(-1px);
    }
    
    /* ========================================
       GLASSMORPHISM CARDS
    ======================================== */
    .glass-card {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.3);
        box-shadow: 0 8px 32px rgba(0, 119, 182, 0.1);
        padding: 1.5rem;
        animation: fadeIn 0.5s ease-out;
    }
    
    /* ========================================
       HEALTHCARE INFO BOXES
    ======================================== */
    .healthcare-box {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        border-left: 4px solid #0077b6;
        border-radius: 0 12px 12px 0;
        padding: 1rem 1.5rem;
        margin: 1rem 0;
        animation: slideUp 0.4s ease-out;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .healthcare-box:hover {
        transform: translateX(5px);
        box-shadow: -4px 0 15px rgba(0, 119, 182, 0.2);
    }
    
    /* Success State */
    .success-indicator {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border-left: 4px solid #28a745;
        border-radius: 0 12px 12px 0;
        padding: 1rem 1.5rem;
        animation: successPop 0.5s ease-out;
    }
    
    /* ========================================
       RISK LEVEL ANIMATIONS
    ======================================== */
    .risk-low {
        animation: successPop 0.5s ease-out;
    }
    .risk-medium {
        animation: glow 2s infinite, breathe 3s infinite;
    }
    .risk-high {
        animation: pulse 1.5s infinite, alertAttention 2s infinite;
    }
    .risk-critical {
        animation: heartbeat 1.5s infinite, alertAttention 1s infinite;
    }
    
    /* ========================================
       ANIMATED PROGRESS BARS
    ======================================== */
    .progress-container {
        background: #e9ecef;
        border-radius: 10px;
        height: 12px;
        overflow: hidden;
        margin: 0.5rem 0;
    }
    .progress-bar {
        height: 100%;
        border-radius: 10px;
        animation: progressFill 1s ease-out forwards;
        background: linear-gradient(90deg, #0077b6, #00b4d8);
        box-shadow: 0 0 10px rgba(0, 119, 182, 0.5);
    }
    .progress-bar.low {
        background: linear-gradient(90deg, #28a745, #20c997);
    }
    .progress-bar.medium {
        background: linear-gradient(90deg, #ffc107, #fd7e14);
    }
    .progress-bar.high {
        background: linear-gradient(90deg, #dc3545, #c82333);
    }
    
    /* ========================================
       RESULT CARDS WITH FADE-IN
    ======================================== */
    .result-card {
        animation: slideInRight 0.6s ease-out;
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        margin: 1rem 0;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .result-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
    }
    
    /* ========================================
       TAB STYLING WITH SMOOTH TRANSITIONS
    ======================================== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
        border-radius: 12px 12px 0 0;
        padding: 12px 24px;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid #dee2e6;
        border-bottom: none;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background: linear-gradient(135deg, #e3f2fd, #bbdefb);
        transform: translateY(-3px);
        box-shadow: 0 4px 12px rgba(0, 119, 182, 0.15);
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #0077b6, #023e8a);
        color: white;
        box-shadow: 0 4px 15px rgba(0, 119, 182, 0.4);
        transform: translateY(-2px);
    }
    
    /* ========================================
       INPUT FIELD STYLING
    ======================================== */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div {
        border-radius: 10px;
        border: 2px solid #e0e0e0;
        transition: all 0.3s ease;
    }
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #0077b6;
        box-shadow: 0 0 0 4px rgba(0, 119, 182, 0.1);
    }
    
    /* ========================================
       EXPANDER STYLING
    ======================================== */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #f8f9fa, #ffffff);
        border-radius: 10px;
        transition: all 0.3s ease;
    }
    .streamlit-expanderHeader:hover {
        background: linear-gradient(135deg, #e3f2fd, #f8f9fa);
        box-shadow: 0 2px 8px rgba(0, 119, 182, 0.1);
    }
    
    /* ========================================
       DIVIDER WITH MEDICAL STYLING
    ======================================== */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #0077b6, transparent);
        margin: 1.5rem 0;
    }
    
    /* ========================================
       LOADING ANIMATION ENHANCEMENT
    ======================================== */
    .stSpinner > div {
        border-color: #0077b6 transparent transparent transparent;
    }
    
    /* Custom loading overlay */
    .loading-overlay {
        background: rgba(255, 255, 255, 0.9);
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 16px;
        padding: 2rem;
    }
    .loading-pulse {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: linear-gradient(135deg, #0077b6, #00b4d8);
        animation: pulse 1.5s infinite;
    }
    
    /* ========================================
       METRIC CARDS
    ======================================== */
    [data-testid="stMetricValue"] {
        color: #023e8a;
        font-weight: 700;
        animation: countUp 0.6s ease-out;
    }
    [data-testid="stMetricDelta"] {
        animation: fadeIn 0.4s ease-out 0.2s both;
    }
    
    /* ========================================
       SCROLLBAR STYLING
    ======================================== */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #0077b6, #023e8a);
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, #0096c7, #0077b6);
    }
    
    /* ========================================
       ACCESSIBILITY - Reduced Motion
    ======================================== */
    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
        }
    }
    
    /* ========================================
       ALERT ENHANCEMENTS
    ======================================== */
    .alert-critical {
        animation: heartbeat 1.5s infinite, alertAttention 1s infinite;
        border-left: 4px solid #dc3545;
    }
    .alert-warning {
        animation: breathe 2s infinite;
        border-left: 4px solid #ffc107;
    }
    .alert-info {
        animation: fadeIn 0.5s ease-out;
        border-left: 4px solid #0077b6;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Check authentication
    if not is_authenticated():
        render_login_page()
        return
    
    # Render sidebar
    render_sidebar()
    
    # Get current user
    user = get_current_user()
    
    # Main content header
    st.title("🏥 Medical Risk Prediction System")
    
    # Welcome message
    st.markdown(f"""
    <p style="font-size: 1.1rem; color: #666;">
    Welcome, <strong>{user.name}</strong>! Enter patient information below to receive an AI-powered 
    risk assessment with intelligent alerts for potential medical errors.
    </p>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # Enhanced navigation with new features
    if user.is_admin():
        tabs = st.tabs([
            "🏥 Risk Assessment", 
            "🎯 Multi-Risk Dashboard",
            "📥 FHIR Import",
            "📊 System Logs"
        ])
        
        with tabs[0]:
            render_risk_assessment_view(user)
        
        with tabs[1]:
            render_multi_risk_view(user)
        
        with tabs[2]:
            render_fhir_import_view()
        
        with tabs[3]:
            render_log_viewer()
    else:
        tabs = st.tabs([
            "🏥 Risk Assessment",
            "🎯 Multi-Risk Dashboard",
            "📥 FHIR Import"
        ])
        
        with tabs[0]:
            render_risk_assessment_view(user)
        
        with tabs[1]:
            render_multi_risk_view(user)
        
        with tabs[2]:
            render_fhir_import_view()


def render_risk_assessment_view(user):
    """Render the main risk assessment view."""
    # Initialize session state
    if 'prediction_made' not in st.session_state:
        st.session_state.prediction_made = False
    if 'last_assessment' not in st.session_state:
        st.session_state.last_assessment = None
    
    # Two-column layout
    col_input, col_result = st.columns([1, 1])
    
    with col_input:
        st.header("📝 Patient Information")
        
        # Privacy reminder
        st.info("🔒 Patient data is processed in-session only and is not stored.")
        
        # Render input form
        patient_data = render_complete_form()
        
        st.divider()
        
        # Predict button
        predict_clicked = st.button("🔍 Analyze Risk", type="primary", use_container_width=True)
    
    with col_result:
        st.header("📊 Risk Assessment")
        
        if predict_clicked:
            # Validate input
            is_valid, errors, warnings = validate_patient_data(patient_data)
            
            # Show warnings
            for warning in warnings:
                if warning.startswith("🚨"):
                    st.error(warning)
                elif warning.startswith("⚠️"):
                    st.warning(warning)
                else:
                    st.info(warning)
            
            if not is_valid:
                for error in errors:
                    st.error(f"❌ {error}")
            else:
                # Load model and make prediction
                with st.spinner("Analyzing patient data..."):
                    model = load_model()
                    
                    if model is not None:
                        try:
                            # Make prediction
                            risk_level, probabilities = model.predict(patient_data)
                            
                            # Classify and generate alerts
                            classifier = RiskClassifier()
                            assessment = classifier.classify(risk_level, probabilities)
                            summary = classifier.get_risk_summary(assessment)
                            patient_summary = get_data_summary(patient_data)
                            
                            # Log the prediction
                            try:
                                log_prediction(
                                    user=user.username,
                                    user_role=user.role.value,
                                    risk_level=assessment.risk_label,
                                    risk_probability=max(probabilities.values()) if probabilities else 0,
                                    alert_generated=assessment.should_alert,
                                    alert_type=assessment.risk_label if assessment.should_alert else None,
                                    vital_signs=patient_data,
                                    symptom_count=patient_summary.get('symptom_count', 0),
                                    condition_count=patient_summary.get('condition_count', 0)
                                )
                                
                                # Log alert if generated
                                if assessment.should_alert:
                                    log_alert(
                                        user=user.username,
                                        risk_level=assessment.risk_label,
                                        alert_message=assessment.alert_message,
                                        recommendations=assessment.recommendations or []
                                    )
                            except Exception as log_error:
                                # Don't break the app if logging fails
                                pass
                            
                            # Store in session state
                            st.session_state.prediction_made = True
                            st.session_state.last_assessment = {
                                'assessment': assessment,
                                'summary': summary,
                                'patient_summary': patient_summary,
                                'feature_importance': model.get_feature_importance()
                            }
                            
                        except Exception as e:
                            st.error(f"Prediction error: {e}")
                            st.session_state.prediction_made = False
        
        # Display results if available
        if st.session_state.prediction_made and st.session_state.last_assessment:
            data = st.session_state.last_assessment
            assessment = data['assessment']
            summary = data['summary']
            
            # Render risk summary with gauge
            render_risk_summary(summary)
            
            # Smart Alert Integration
            smart_engine = SmartAlertEngine()
            smart_alert = smart_engine.prioritize_alert(
                risk_level=assessment.risk_label,
                risk_score=assessment.confidence,
                message=assessment.alert_message or f"{assessment.risk_label} risk detected",
                recommendations=assessment.recommendations or [],
                patient_id=None,
                source="ml"
            )
            
            # Render alert with priority information
            if assessment.should_alert and not smart_alert.was_suppressed:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, {smart_alert.color}22, {smart_alert.color}11); 
                            border-left: 4px solid {smart_alert.color}; padding: 15px; border-radius: 8px; margin: 10px 0;">
                    <strong>{smart_alert.icon} {smart_alert.priority.name} PRIORITY ALERT</strong><br>
                    <span style="color: #666;">Priority Score: {smart_alert.priority.value}/4</span>
                </div>
                """, unsafe_allow_html=True)
                render_alert(
                    assessment.risk_label,
                    assessment.alert_message,
                    assessment.confidence,
                    assessment.recommendations
                )
            elif smart_alert.was_suppressed:
                st.info(f"ℹ️ Alert suppressed: {smart_alert.suppression_reason}")
            else:
                render_no_alert_message()
            
            # XAI Explanation Section
            st.divider()
            st.subheader("🧠 AI Explanation: Why This Risk Level?")
            
            # Generate XAI explanation
            explanation = create_demo_explanation(assessment.risk_label)
            render_explanation_section(explanation)
            
            # Patient summary
            render_patient_summary(data['patient_summary'])
            
            # Feature importance (now enhanced with XAI context)
            if data.get('feature_importance'):
                with st.expander("📊 Model Feature Importance", expanded=False):
                    render_feature_importance(data['feature_importance'])
            
            # Recommendations
            if assessment.recommendations:
                render_recommendations(assessment.recommendations)
        else:
            st.info("👆 Enter patient information and click 'Analyze Risk' to get a risk assessment.")



def render_multi_risk_view(user):
    """Render the multi-risk assessment dashboard."""
    st.header("🎯 Comprehensive Multi-Risk Assessment")
    st.markdown("""
    This dashboard provides a **unified assessment** across multiple risk categories:
    - 💊 Medication Error Risk
    - 📈 Disease Progression Risk  
    - ⚠️ Adverse Event Risk
    - 🏥 Hospital Readmission Risk
    """)
    
    # Initialize session state
    if 'multi_risk_assessment' not in st.session_state:
        st.session_state.multi_risk_assessment = None
    
    # Input form
    with st.expander("📝 Enter Patient Data", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            age = st.number_input("Age", min_value=0, max_value=120, value=65)
            heart_rate = st.number_input("Heart Rate (bpm)", 40, 200, 80)
            bp_systolic = st.number_input("Systolic BP (mmHg)", 70, 250, 120)
            temperature = st.number_input("Temperature (°C)", 35.0, 42.0, 37.0)
            oxygen_sat = st.number_input("SpO2 (%)", 70, 100, 97)
        
        with col2:
            num_medications = st.number_input("Number of Medications", 0, 30, 3)
            symptom_count = st.number_input("Number of Symptoms", 0, 20, 2)
            
            st.markdown("**Conditions:**")
            has_diabetes = st.checkbox("Diabetes")
            has_heart_disease = st.checkbox("Heart Disease")
            has_kidney_disease = st.checkbox("Kidney Disease")
    
    # Compile patient data
    patient_data = {
        'age': age,
        'heart_rate': heart_rate,
        'blood_pressure_systolic': bp_systolic,
        'temperature': temperature,
        'oxygen_saturation': oxygen_sat,
        'num_medications': num_medications,
        'symptom_count': symptom_count,
        'condition_diabetes': 1 if has_diabetes else 0,
        'condition_heart_disease': 1 if has_heart_disease else 0,
        'condition_kidney_disease': 1 if has_kidney_disease else 0,
        'medications': [],
        'allergies': []
    }
    
    if st.button("🔍 Run Multi-Risk Analysis", type="primary", use_container_width=True):
        with st.spinner("Analyzing all risk dimensions..."):
            try:
                multi_engine = MultiRiskEngine()
                assessment = multi_engine.predict_all_risks(patient_data)
                st.session_state.multi_risk_assessment = assessment
            except Exception as e:
                st.error(f"Analysis error: {e}")
    
    # Display results
    if st.session_state.multi_risk_assessment:
        st.divider()
        render_multi_risk_dashboard(st.session_state.multi_risk_assessment)
        
        # Hybrid intelligence section
        st.divider()
        st.markdown("### 🧠 Hybrid Intelligence Analysis")
        st.markdown("*Combining ML predictions with clinical safety rules*")
        
        with st.spinner("Running clinical rules checks..."):
            try:
                rules_engine = ClinicalRulesEngine()
                rules_result = rules_engine.run_all_checks(patient_data)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Rules Passed", f"{rules_result.passed_rules}/{rules_result.total_rules}")
                with col2:
                    pass_rate = rules_result.pass_rate * 100
                    st.metric("Compliance Rate", f"{pass_rate:.1f}%")
                
                st.markdown(f"**Status:** {rules_result.summary}")
                
                if rules_result.violations:
                    with st.expander("⚠️ View Rule Violations", expanded=rules_result.has_critical):
                        for violation in rules_result.violations:
                            st.markdown(f"""
                            <div style="border-left: 3px solid {violation.color}; padding-left: 10px; margin: 10px 0;">
                                <strong>{violation.icon} {violation.rule_name}</strong><br>
                                {violation.message}<br>
                                <em>Recommendation: {violation.recommendation}</em>
                            </div>
                            """, unsafe_allow_html=True)
            except Exception as e:
                st.warning(f"Could not run clinical rules: {e}")


def render_fhir_import_view():
    """Render the FHIR data import view."""
    st.header("📥 FHIR Patient Data Import")
    st.markdown("""
    Import patient data from **FHIR R4** formatted bundles for seamless EHR integration.
    Supported resources: Patient, Observation, Condition, MedicationStatement, AllergyIntolerance
    """)
    
    # Initialize session state
    if 'fhir_data' not in st.session_state:
        st.session_state.fhir_data = None
    if 'fhir_patient_data' not in st.session_state:
        st.session_state.fhir_patient_data = None
    
    def handle_import(bundle):
        """Handle FHIR bundle import."""
        try:
            converter = FHIRConverter()
            patient_data = converter.bundle_to_patient_data(bundle)
            st.session_state.fhir_data = bundle
            st.session_state.fhir_patient_data = patient_data
            st.success("✅ FHIR data imported successfully!")
        except Exception as e:
            st.error(f"Import error: {e}")
    
    render_fhir_import_section(handle_import)
    
    # Display imported data
    if st.session_state.fhir_patient_data:
        st.divider()
        render_fhir_data_preview(st.session_state.fhir_patient_data)
        
        # Option to analyze imported data
        st.divider()
        if st.button("🔍 Analyze Imported Patient", type="primary", use_container_width=True):
            with st.spinner("Analyzing patient data..."):
                try:
                    # Convert FHIR patient data to dict format
                    patient_data = st.session_state.fhir_patient_data.to_prediction_dict()
                    
                    # Run multi-risk analysis
                    multi_engine = MultiRiskEngine()
                    assessment = multi_engine.predict_all_risks(patient_data)
                    
                    st.divider()
                    render_multi_risk_dashboard(assessment)
                except Exception as e:
                    st.error(f"Analysis error: {e}")


if __name__ == "__main__":
    main()

