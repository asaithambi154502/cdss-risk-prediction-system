"""
CDSS - Clinical Decision Support System
Main Streamlit Application

AI-Based Medical Error Risk Prediction System
Enhanced with Security, Logging, and Professional UI
"""

import streamlit as st
import sys
from pathlib import Path
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import PAGE_CONFIG, MODEL_PATH, ENCODER_PATH
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
       HEALTHCARE THEME - Color Palette
       Primary: #0077b6 (Medical Blue)
       Secondary: #28a745 (Health Green)
       Accent: #00b4d8 (Light Blue)
       Warning: #ffc107, Critical: #dc3545
    ======================================== */
    
    /* Global Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes slideUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
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
    
    /* Main Container */
    .main > div {
        padding-top: 2rem;
        animation: fadeIn 0.5s ease-out;
    }
    
    /* Healthcare-themed headings */
    h1 {
        color: #023e8a;
        animation: slideUp 0.6s ease-out;
    }
    h2, h3 {
        color: #0077b6;
        animation: fadeIn 0.4s ease-out;
    }
    
    /* Professional Button Styling */
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
    }
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0, 119, 182, 0.5);
        background: linear-gradient(135deg, #0096c7 0%, #0077b6 100%);
    }
    .stButton > button:active {
        transform: translateY(-1px);
    }
    
    /* Glassmorphism Cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.3);
        box-shadow: 0 8px 32px rgba(0, 119, 182, 0.1);
        padding: 1.5rem;
        animation: fadeIn 0.5s ease-out;
    }
    
    /* Healthcare Info Boxes */
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
    
    /* Risk Level Animations */
    .risk-low {
        animation: successPop 0.5s ease-out;
    }
    .risk-medium {
        animation: glow 2s infinite;
    }
    .risk-high {
        animation: pulse 1.5s infinite;
    }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
        border-radius: 12px 12px 0 0;
        padding: 12px 24px;
        transition: all 0.3s ease;
        border: 1px solid #dee2e6;
        border-bottom: none;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background: linear-gradient(135deg, #e9ecef, #dee2e6);
        transform: translateY(-2px);
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #0077b6, #023e8a);
        color: white;
        box-shadow: 0 4px 15px rgba(0, 119, 182, 0.3);
    }
    
    /* Input Field Styling */
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
        box-shadow: 0 0 0 3px rgba(0, 119, 182, 0.1);
    }
    
    /* Expander Styling */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #f8f9fa, #ffffff);
        border-radius: 10px;
        transition: all 0.3s ease;
    }
    .streamlit-expanderHeader:hover {
        background: linear-gradient(135deg, #e3f2fd, #f8f9fa);
    }
    
    /* Divider with medical styling */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #0077b6, transparent);
        margin: 1.5rem 0;
    }
    
    /* Loading Animation Enhancement */
    .stSpinner > div {
        border-color: #0077b6 transparent transparent transparent;
    }
    
    /* Metric Cards */
    [data-testid="stMetricValue"] {
        color: #023e8a;
        font-weight: 700;
    }
    
    /* Scrollbar Styling */
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
    
    # Navigation for admin
    if user.is_admin():
        tab_assessment, tab_logs = st.tabs(["🏥 Risk Assessment", "📊 System Logs"])
        
        with tab_logs:
            render_log_viewer()
        
        with tab_assessment:
            render_risk_assessment_view(user)
    else:
        render_risk_assessment_view(user)


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
            
            # Render alert
            if assessment.should_alert:
                render_alert(
                    assessment.risk_label,
                    assessment.alert_message,
                    assessment.confidence,
                    assessment.recommendations
                )
            else:
                render_no_alert_message()
            
            # Patient summary
            render_patient_summary(data['patient_summary'])
            
            # Feature importance
            if data.get('feature_importance'):
                render_feature_importance(data['feature_importance'])
            
            # Recommendations
            if assessment.recommendations:
                render_recommendations(assessment.recommendations)
        else:
            st.info("👆 Enter patient information and click 'Analyze Risk' to get a risk assessment.")


if __name__ == "__main__":
    main()
