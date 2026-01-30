"""
Login Page Component for CDSS

Provides the login interface for user authentication.
"""

import streamlit as st
import sys
import requests
from streamlit_lottie import st_lottie
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.auth import (
    authenticate, 
    login_user, 
    get_role_display_name,
    get_role_color,
    UserRole
)
from cdss_config import UI_STYLE


def load_lottieurl(url: str):
    """Load Lottie animation from URL."""
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None


def load_lottiefile(filepath: str):
    """Load Lottie animation from local JSON file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading local Lottie file: {e}")
        return None


def render_login_page() -> bool:
    """
    Render the login page with enhanced animations and healthcare theming.
    
    Returns:
        True if login was successful, False otherwise
    """
    # Initialize session state for login animation
    if 'login_error' not in st.session_state:
        st.session_state.login_error = False
    
    # Enhanced CSS with animated gradient background, shake effect, and success animation
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600&display=swap');

    /* Animated Gradient Background */
    @keyframes gradientShift {{
        0% {{ background-position: 0% 50%; }}
        50% {{ background-position: 100% 50%; }}
        100% {{ background-position: 0% 50%; }}
    }}
    
    /* Float in animation */
    @keyframes floatIn {{
        0% {{ opacity: 0; transform: translateY(-30px); }}
        100% {{ opacity: 1; transform: translateY(0); }}
    }}
    
    /* Soft pulse for icon */
    @keyframes pulse-soft {{
        0%, 100% {{ transform: scale(1); }}
        50% {{ transform: scale(1.08); }}
    }}
    
    /* Shake animation for login failure */
    @keyframes shake {{
        0%, 100% {{ transform: translateX(0); }}
        10%, 30%, 50%, 70%, 90% {{ transform: translateX(-8px); }}
        20%, 40%, 60%, 80% {{ transform: translateX(8px); }}
    }}
    
    /* Success checkmark animation */
    @keyframes successPop {{
        0% {{ transform: scale(0); opacity: 0; }}
        50% {{ transform: scale(1.2); }}
        100% {{ transform: scale(1); opacity: 1; }}
    }}
    
    /* Glow effect */
    @keyframes glow {{
        0%, 100% {{ box-shadow: 0 0 20px rgba(96, 165, 250, 0.2); }}
        50% {{ box-shadow: 0 0 40px rgba(96, 165, 250, 0.4); }}
    }}
    
    /* Animated background wrapper */
    .login-bg {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: {UI_STYLE['background_gradient']};
        background-size: 400% 400%;
        animation: gradientShift 15s ease infinite;
        z-index: -1;
    }}
    
    /* Login header styling */
    .login-header {{
        animation: floatIn 0.8s ease-out;
        text-align: center;
        padding: 2rem 0;
    }}
    
    .login-icon {{
        animation: pulse-soft 3s infinite ease-in-out;
        display: inline-block;
        font-size: 5rem;
        margin-bottom: 1rem;
        filter: drop-shadow(0 4px 8px rgba(0, 119, 182, 0.3));
    }}
    
    .login-title {{
        color: #0077b6;
        margin-bottom: 0.5rem;
        font-size: 2.8rem;
        font-weight: 700;
        text-shadow: 0 2px 4px rgba(0, 119, 182, 0.1);
    }}
    
    .login-subtitle {{
        color: #555;
        font-size: 1.2rem;
        margin: 0.5rem 0;
        font-weight: 500;
    }}
    
    .login-tagline {{
        color: #777;
        font-size: 0.95rem;
        margin: 0;
    }}
    
    /* Login card with glassmorphism */
    .login-card {{
        background: {UI_STYLE['glass_bg']};
        backdrop-filter: {UI_STYLE['glass_blur']};
        -webkit-backdrop-filter: {UI_STYLE['glass_blur']};
        padding: 3rem;
        border-radius: 28px;
        box-shadow: {UI_STYLE['card_shadow']};
        border: {UI_STYLE['glass_border']};
        animation: floatIn 0.8s ease-out 0.2s both, glow 4s ease-in-out infinite;
        color: {UI_STYLE['text_primary']};
    }}
    
    /* Shake animation class for error */
    .shake-error {{
        animation: shake 0.6s ease-in-out;
    }}
    
    /* Success animation */
    .success-checkmark {{
        animation: successPop 0.5s ease-out;
        display: inline-block;
    }}
    
    /* Demo credentials styling */
    .demo-creds {{
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 12px;
        padding: 1rem;
        border: 1px solid #dee2e6;
    }}
    
    .demo-creds table {{
        width: 100%;
        border-collapse: collapse;
    }}
    
    .demo-creds th, .demo-creds td {{
        padding: 0.5rem;
        text-align: left;
        border-bottom: 1px solid #dee2e6;
    }}
    
    /* Security notice with subtle animation */
    .security-notice {{
        text-align: center;
        margin-top: 2rem;
        padding: 1rem 1.5rem;
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        border-radius: 12px;
        border: 1px solid #90caf9;
        animation: floatIn 1s ease-out 0.4s both;
    }}
    
    .security-notice p {{
        color: #1565c0;
        margin: 0;
        font-size: 0.9rem;
        font-weight: 500;
    }}
    
    /* Footer styling */
    .login-footer {{
        text-align: center;
        margin-top: 2rem;
        animation: floatIn 1s ease-out 0.6s both;
    }}
    
    .login-footer p {{
        color: #888;
        font-size: 0.8rem;
    }}
    
    /* Medical icons decoration */
    .medical-icons {{
        display: flex;
        justify-content: center;
        gap: 1.5rem;
        margin-top: 1rem;
        opacity: 0.6;
    }}
    
    .medical-icons span {{
        font-size: 1.5rem;
    }}
    </style>
    
    <!-- Animated gradient background -->
    <div class="login-bg"></div>
    """, unsafe_allow_html=True)
    
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Header with animated logo
        # Use local animation - Medical Doctor Animation (User Provided)
        project_root = Path(__file__).parent.parent.parent
        lottie_path = project_root / "app" / "assets" / "login_doctor_animation.json"
        lottie_medical = load_lottiefile(str(lottie_path))
        
        # Fallback to URL if local file fails
        if lottie_medical is None:
            lottie_medical = load_lottieurl("https://lottie.host/80182ce5-e406-4b24-9f87-345037d0c36b/vH4V0G9U0D.json")
        
        st.markdown("""
        <div class="login-header">
        """, unsafe_allow_html=True)
        
        if lottie_medical:
            st_lottie(lottie_medical, height=180, key="login_logo")
        else:
            st.markdown('<div class="login-icon">🏥</div>', unsafe_allow_html=True)
            
        st.markdown("""
            <h1 class="login-title">CDSS</h1>
            <p class="login-subtitle">Clinical Decision Support System</p>
            <p class="login-tagline">AI-Based Medical Error Risk Prediction</p>
            <div class="medical-icons">
                <span>💉</span>
                <span>🩺</span>
                <span>💊</span>
                <span>🔬</span>
                <span>❤️</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Apply shake animation if there was an error
        card_class = "login-card shake-error" if st.session_state.login_error else "login-card"
        
        with st.container():
            st.subheader("🔐 Secure Login")
            st.caption("Please enter your credentials to access the system")
            
            # Login form
            with st.form("login_form"):
                username = st.text_input(
                    "👤 Username",
                    placeholder="Enter your username",
                    key="login_username"
                )
                
                password = st.text_input(
                    "🔑 Password",
                    type="password",
                    placeholder="Enter your password",
                    key="login_password"
                )
                
                # Remember me checkbox
                remember_me = st.checkbox("Remember me", value=False)
                
                col_btn1, col_btn2 = st.columns([1, 1])
                with col_btn1:
                    submitted = st.form_submit_button(
                        "🔓 Login",
                        use_container_width=True,
                        type="primary"
                    )
            
            if submitted:
                if not username or not password:
                    st.session_state.login_error = True
                    st.markdown("""
                    <div class="shake-error">
                        <p style="color: #dc3545; font-weight: 500;">❌ Please enter both username and password</p>
                    </div>
                    """, unsafe_allow_html=True)
                    st.rerun()
                    return False
                
                success, user = authenticate(username, password)
                
                if success and user:
                    st.session_state.login_error = False
                    login_user(user)
                    # Show success animation
                    st.markdown(f"""
                    <div style="text-align: center; padding: 1rem;">
                        <span class="success-checkmark" style="font-size: 3rem;">✅</span>
                        <h3 style="color: #28a745; margin-top: 0.5rem;">Welcome, {user.name}!</h3>
                        <p style="color: #666;">Redirecting to dashboard...</p>
                    </div>
                    """, unsafe_allow_html=True)
                    import time
                    time.sleep(0.5)
                    st.rerun()
                    return True
                else:
                    st.session_state.login_error = True
                    st.error("❌ Invalid username or password")
                    st.rerun()
                    return False
            else:
                # Reset error state when not submitting
                if st.session_state.login_error:
                    st.session_state.login_error = False
        
        # Demo credentials info
        st.divider()
        
        with st.expander("ℹ️ Demo Credentials", expanded=False):
            st.markdown("""
            <div class="demo-creds">
            <p style="margin-bottom: 0.5rem;"><strong>For testing purposes, use these credentials:</strong></p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            | Role | Username | Password |
            |:-----|:---------|:---------|
            | 👨‍⚕️ **Doctor** | `doctor1` | `doctor123` |
            | 💊 **Pharmacist** | `pharmacist1` | `pharma123` |
            | 🔧 **Admin** | `admin` | `admin123` |
            
            > 💡 *In production, credentials would be managed by hospital IT systems.*
            """)
        
        # Security notice with animation
        st.markdown("""
        <div class="security-notice">
            <p>🔒 This system uses secure authentication to protect patient data privacy.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Footer
        st.markdown("""
        <div class="login-footer">
            <p>
                © 2024 CDSS Risk Prediction System<br>
                For educational and demonstration purposes only
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    return False


def render_user_info_sidebar() -> None:
    """Render user info and logout button in sidebar."""
    from app.auth import get_current_user, logout_user, get_role_display_name, get_role_color
    
    user = get_current_user()
    
    if user:
        role_color = get_role_color(user.role)
        role_display = get_role_display_name(user.role)
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {role_color}15 0%, {role_color}25 100%);
                    padding: 1rem; border-radius: 12px; margin-bottom: 1rem;
                    border: 1px solid {role_color}40;">
            <p style="margin: 0; font-size: 0.85rem; color: #666;">Logged in as</p>
            <p style="margin: 0.25rem 0; font-size: 1.1rem; font-weight: 600; color: #333;">
                {user.name}
            </p>
            <p style="margin: 0; font-size: 0.9rem; color: {role_color};">
                {role_display}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚪 Logout", use_container_width=True):
            logout_user()
            st.rerun()
