"""
Authentication Module for CDSS

Provides user authentication and role-based access control.
"""

import hashlib
import streamlit as st
from typing import Optional, Dict, Tuple
from dataclasses import dataclass
from enum import Enum


class UserRole(Enum):
    """User roles with access levels."""
    DOCTOR = "doctor"
    PHARMACIST = "pharmacist"
    ADMIN = "admin"


@dataclass
class User:
    """User data class."""
    username: str
    name: str
    role: UserRole
    
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN
    
    def can_view_logs(self) -> bool:
        return self.role == UserRole.ADMIN
    
    def can_make_predictions(self) -> bool:
        return self.role in [UserRole.DOCTOR, UserRole.PHARMACIST, UserRole.ADMIN]


def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


# Demo users for the system
# In production, this would be replaced with a database or LDAP integration
DEMO_USERS = {
    "doctor1": {
        "password_hash": hash_password("doctor123"),
        "name": "Dr. Sarah Smith",
        "role": UserRole.DOCTOR
    },
    "doctor2": {
        "password_hash": hash_password("doctor123"),
        "name": "Dr. James Wilson",
        "role": UserRole.DOCTOR
    },
    "pharmacist1": {
        "password_hash": hash_password("pharma123"),
        "name": "John Doe, PharmD",
        "role": UserRole.PHARMACIST
    },
    "pharmacist2": {
        "password_hash": hash_password("pharma123"),
        "name": "Emily Chen, PharmD",
        "role": UserRole.PHARMACIST
    },
    "admin": {
        "password_hash": hash_password("admin123"),
        "name": "System Administrator",
        "role": UserRole.ADMIN
    }
}


def authenticate(username: str, password: str) -> Tuple[bool, Optional[User]]:
    """
    Authenticate a user with username and password.
    
    Args:
        username: The username to authenticate
        password: The password to verify
        
    Returns:
        Tuple of (success, User object or None)
    """
    if username not in DEMO_USERS:
        return False, None
    
    user_data = DEMO_USERS[username]
    password_hash = hash_password(password)
    
    if password_hash != user_data["password_hash"]:
        return False, None
    
    user = User(
        username=username,
        name=user_data["name"],
        role=user_data["role"]
    )
    
    return True, user


def login_user(user: User) -> None:
    """Store user in session state after successful login."""
    st.session_state.authenticated = True
    st.session_state.user = user
    st.session_state.username = user.username


def logout_user() -> None:
    """Clear user session."""
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.username = None
    # Clear any prediction data
    if 'prediction_made' in st.session_state:
        st.session_state.prediction_made = False
    if 'last_assessment' in st.session_state:
        st.session_state.last_assessment = None


def is_authenticated() -> bool:
    """Check if user is currently authenticated."""
    return st.session_state.get('authenticated', False)


def get_current_user() -> Optional[User]:
    """Get the current logged-in user."""
    return st.session_state.get('user', None)


def require_auth(func):
    """Decorator to require authentication for a function."""
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            st.warning("⚠️ Please login to access this feature.")
            return None
        return func(*args, **kwargs)
    return wrapper


def require_role(allowed_roles: list):
    """Decorator to require specific roles for a function."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if not user or user.role not in allowed_roles:
                st.error("🚫 You don't have permission to access this feature.")
                return None
            return func(*args, **kwargs)
        return wrapper
    return decorator


def get_role_display_name(role: UserRole) -> str:
    """Get a display-friendly role name."""
    role_names = {
        UserRole.DOCTOR: "👨‍⚕️ Doctor",
        UserRole.PHARMACIST: "💊 Pharmacist",
        UserRole.ADMIN: "🔧 Administrator"
    }
    return role_names.get(role, "Unknown")


def get_role_color(role: UserRole) -> str:
    """Get the color associated with a role."""
    role_colors = {
        UserRole.DOCTOR: "#0077b6",      # Blue
        UserRole.PHARMACIST: "#2a9d8f",  # Teal
        UserRole.ADMIN: "#6c757d"        # Gray
    }
    return role_colors.get(role, "#333333")
