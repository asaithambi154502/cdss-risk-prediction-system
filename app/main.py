"""
CDSS - Clinical Decision Support System
Main Streamlit Application

AI-Based Medical Error Risk Prediction System
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
from app.utils.validators import validate_patient_data, get_data_summary
from ml.risk_classifier import RiskClassifier, AlertEngine


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


def main():
    """Main application entry point."""
    # Page configuration
    st.set_page_config(**PAGE_CONFIG)
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main > div {
        padding-top: 2rem;
    }
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: bold;
        padding: 0.75rem 1.5rem;
        font-size: 1.1rem;
        border: none;
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    h1 {
        color: #1e3a8a;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Render sidebar
    render_sidebar()
    
    # Main content
    st.title("🏥 Medical Risk Prediction System")
    st.markdown("""
    <p style="font-size: 1.1rem; color: #666;">
    Enter patient information below to receive an AI-powered risk assessment
    with intelligent alerts for potential medical errors.
    </p>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # Initialize session state
    if 'prediction_made' not in st.session_state:
        st.session_state.prediction_made = False
    if 'last_assessment' not in st.session_state:
        st.session_state.last_assessment = None
    
    # Two-column layout
    col_input, col_result = st.columns([1, 1])
    
    with col_input:
        st.header("📝 Patient Information")
        
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
                            
                            # Store in session state
                            st.session_state.prediction_made = True
                            st.session_state.last_assessment = {
                                'assessment': assessment,
                                'summary': summary,
                                'patient_summary': get_data_summary(patient_data),
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
