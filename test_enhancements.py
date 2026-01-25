"""
Test script for CDSS enhancements
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_auth():
    """Test authentication module."""
    print("Testing Authentication Module...")
    from app.auth import authenticate, UserRole, get_role_display_name
    
    # Test valid login
    success, user = authenticate('doctor1', 'doctor123')
    assert success == True, "Doctor login should succeed"
    assert user.name == "Dr. Sarah Smith", f"Expected Dr. Sarah Smith, got {user.name}"
    assert user.role == UserRole.DOCTOR, "Role should be DOCTOR"
    print(f"  ✓ Doctor login: {user.name}")
    
    # Test invalid login
    success, user = authenticate('doctor1', 'wrongpass')
    assert success == False, "Invalid password should fail"
    print("  ✓ Invalid password rejected")
    
    # Test admin login
    success, user = authenticate('admin', 'admin123')
    assert success == True, "Admin login should succeed"
    assert user.is_admin() == True, "Admin should have admin privileges"
    print(f"  ✓ Admin login: {user.name}")
    
    # Test pharmacist login
    success, user = authenticate('pharmacist1', 'pharma123')
    assert success == True, "Pharmacist login should succeed"
    assert user.role == UserRole.PHARMACIST, "Role should be PHARMACIST"
    print(f"  ✓ Pharmacist login: {user.name}")
    
    print("✅ Authentication tests passed!")
    return True

def test_logger():
    """Test logging module."""
    print("\nTesting Logging Module...")
    from app.utils.logger import get_logger
    
    logger = get_logger()
    
    # Test prediction logging
    logger.log_prediction(
        user="test_user",
        user_role="doctor",
        risk_level="Medium",
        risk_probability=0.45,
        alert_generated=True,
        alert_type="Medium",
        vital_signs={
            "heart_rate": 85,
            "temperature": 37.5,
            "blood_pressure_systolic": 130,
            "blood_pressure_diastolic": 85,
            "oxygen_saturation": 96,
            "respiratory_rate": 18
        },
        symptom_count=3,
        condition_count=1
    )
    print("  ✓ Prediction logged")
    
    # Test alert logging
    logger.log_alert(
        user="test_user",
        risk_level="Medium",
        alert_message="Moderate risk detected",
        recommendations=["Review medication", "Monitor vital signs"]
    )
    print("  ✓ Alert logged")
    
    # Test statistics
    stats = logger.get_statistics()
    assert 'total_predictions' in stats, "Stats should have total_predictions"
    assert 'risk_distribution' in stats, "Stats should have risk_distribution"
    print(f"  ✓ Statistics: {stats['total_predictions']} predictions logged")
    
    print("✅ Logger tests passed!")
    return True

def test_imports():
    """Test that all new modules can be imported."""
    print("\nTesting Module Imports...")
    
    try:
        from app.auth import (
            authenticate, login_user, logout_user, 
            is_authenticated, get_current_user, UserRole
        )
        print("  ✓ app.auth imported")
    except Exception as e:
        print(f"  ✗ app.auth failed: {e}")
        return False
    
    try:
        from app.components.login_page import render_login_page, render_user_info_sidebar
        print("  ✓ app.components.login_page imported")
    except Exception as e:
        print(f"  ✗ app.components.login_page failed: {e}")
        return False
    
    try:
        from app.utils.logger import get_logger, log_prediction, log_alert
        print("  ✓ app.utils.logger imported")
    except Exception as e:
        print(f"  ✗ app.utils.logger failed: {e}")
        return False
    
    try:
        from app.components.log_viewer import render_log_viewer
        print("  ✓ app.components.log_viewer imported")
    except Exception as e:
        print(f"  ✗ app.components.log_viewer failed: {e}")
        return False
    
    print("✅ All imports successful!")
    return True

def main():
    print("=" * 50)
    print("CDSS Enhancement Test Suite")
    print("=" * 50)
    
    all_passed = True
    
    # Run tests
    all_passed &= test_imports()
    all_passed &= test_auth()
    all_passed &= test_logger()
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 50)
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
