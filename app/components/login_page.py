"""
Login Page Component for CDSS

Provides the login interface for user authentication.
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.auth import (
    authenticate, 
    login_user, 
    get_role_display_name,
    get_role_color,
    UserRole
)


def render_login_page() -> bool:
    """
    Render the login page.
    
    Returns:
        True if login was successful, False otherwise
    """
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Header with logo - animated
        st.markdown("""
        <style>
        @keyframes floatIn {
            0% { opacity: 0; transform: translateY(-20px); }
            100% { opacity: 1; transform: translateY(0); }
        }
        @keyframes pulse-soft {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }
        .login-header {
            animation: floatIn 0.8s ease-out;
        }
        .login-icon {
            animation: pulse-soft 3s infinite ease-in-out;
            display: inline-block;
        }
        </style>
        <div class="login-header" style="text-align: center; padding: 2rem 0;">
            <div class="login-icon" style="font-size: 4rem; margin-bottom: 1rem;">🏥</div>
            <h1 style="color: #0077b6; margin-bottom: 0.5rem; font-size: 2.5rem;">CDSS</h1>
            <p style="color: #666; font-size: 1.2rem; margin: 0.5rem 0;">Clinical Decision Support System</p>
            <p style="color: #888; font-size: 0.9rem; margin: 0;">AI-Based Medical Error Risk Prediction</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Login card with glassmorphism
        st.markdown("""
        <style>
        .login-container {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            padding: 2rem;
            border-radius: 20px;
            box-shadow: 0 8px 32px rgba(0, 119, 182, 0.15);
            border: 1px solid rgba(255, 255, 255, 0.5);
            animation: floatIn 0.8s ease-out 0.2s both;
        }
        </style>
        """, unsafe_allow_html=True)
        
        with st.container():
            st.subheader("🔐 Login")
            st.caption("Please enter your credentials to access the system")
            
            # Login form
            with st.form("login_form"):
                username = st.text_input(
                    "Username",
                    placeholder="Enter your username",
                    key="login_username"
                )
                
                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter your password",
                    key="login_password"
                )
                
                col_btn1, col_btn2 = st.columns([1, 1])
                with col_btn1:
                    submitted = st.form_submit_button(
                        "🔓 Login",
                        use_container_width=True,
                        type="primary"
                    )
            
            if submitted:
                if not username or not password:
                    st.error("❌ Please enter both username and password")
                    return False
                
                success, user = authenticate(username, password)
                
                if success and user:
                    login_user(user)
                    st.success(f"✅ Welcome, {user.name}!")
                    st.rerun()
                    return True
                else:
                    st.error("❌ Invalid username or password")
                    return False
        
        # Demo credentials info
        st.divider()
        
        with st.expander("ℹ️ Demo Credentials", expanded=False):
            st.markdown("""
            **For testing purposes, use these credentials:**
            
            | Role | Username | Password |
            |------|----------|----------|
            | 👨‍⚕️ Doctor | `doctor1` | `doctor123` |
            | 💊 Pharmacist | `pharmacist1` | `pharma123` |
            | 🔧 Admin | `admin` | `admin123` |
            
            *Note: In production, credentials would be managed by hospital IT systems.*
            """)
        
        # Security notice
        st.markdown("""
        <div style="text-align: center; margin-top: 2rem; padding: 1rem; 
                    background: #e3f2fd; border-radius: 8px; border: 1px solid #90caf9;">
            <p style="color: #1565c0; margin: 0; font-size: 0.85rem;">
                🔒 This system uses secure authentication to protect patient data privacy.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Footer
        st.markdown("""
        <div style="text-align: center; margin-top: 2rem;">
            <p style="color: #999; font-size: 0.8rem;">
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
