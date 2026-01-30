"""
Explainable AI (XAI) Module for CDSS

Provides transparency in ML predictions using SHAP and LIME
to explain why a patient was classified at a particular risk level.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    print("Warning: SHAP not available. Install with: pip install shap")

try:
    from lime.lime_tabular import LimeTabularExplainer
    LIME_AVAILABLE = True
except ImportError:
    LIME_AVAILABLE = False
    print("Warning: LIME not available. Install with: pip install lime")

from cdss_config import XAI_CONFIG, FEATURE_DISPLAY_NAMES


@dataclass
class FeatureContribution:
    """Represents a single feature's contribution to prediction."""
    feature_name: str
    display_name: str
    value: float
    contribution: float
    direction: str  # "increases_risk" or "decreases_risk"
    

@dataclass
class Explanation:
    """Complete explanation for a prediction."""
    method: str  # "shap" or "lime"
    risk_level: str
    confidence: float
    top_factors: List[FeatureContribution]
    all_contributions: Dict[str, float]
    narrative: str
    base_value: Optional[float] = None
    shap_values: Optional[np.ndarray] = None


class RiskExplainer:
    """
    Generates explanations for ML predictions using SHAP and LIME.
    
    This class provides transparency into why the model classified
    a patient at a particular risk level by identifying the most
    influential clinical factors.
    """
    
    def __init__(self, model, feature_names: List[str], 
                 background_data: Optional[pd.DataFrame] = None):
        """
        Initialize the explainer.
        
        Args:
            model: Trained sklearn model (must have predict_proba)
            feature_names: List of feature names used by the model
            background_data: Background dataset for SHAP (optional)
        """
        self.model = model
        self.feature_names = feature_names
        self.config = XAI_CONFIG
        self.background_data = background_data
        
        # Initialize explainers
        self.shap_explainer = None
        self.lime_explainer = None
        
        self._initialize_explainers()
    
    def _initialize_explainers(self):
        """Initialize SHAP and LIME explainers."""
        # Initialize SHAP
        if SHAP_AVAILABLE and self.model is not None:
            try:
                # Use TreeExplainer for tree-based models (Random Forest, XGBoost)
                if hasattr(self.model, 'estimators_') or hasattr(self.model, 'get_booster'):
                    self.shap_explainer = shap.TreeExplainer(self.model)
                else:
                    # Use KernelExplainer for other models
                    if self.background_data is not None:
                        # Sample background data for efficiency
                        sample_size = min(self.config['shap_max_samples'], 
                                        len(self.background_data))
                        background = self.background_data.sample(n=sample_size, 
                                                                  random_state=42)
                        self.shap_explainer = shap.KernelExplainer(
                            self.model.predict_proba, 
                            background
                        )
            except Exception as e:
                print(f"Warning: Could not initialize SHAP explainer: {e}")
        
        # Initialize LIME
        if LIME_AVAILABLE and self.background_data is not None:
            try:
                self.lime_explainer = LimeTabularExplainer(
                    training_data=self.background_data.values,
                    feature_names=self.feature_names,
                    class_names=['Low Risk', 'Medium Risk', 'High Risk'],
                    mode='classification',
                    discretize_continuous=True
                )
            except Exception as e:
                print(f"Warning: Could not initialize LIME explainer: {e}")
    
    def explain_with_shap(self, patient_data: Dict, 
                          predicted_class: int) -> Optional[Explanation]:
        """
        Generate SHAP-based feature contributions.
        
        Args:
            patient_data: Dictionary of patient features
            predicted_class: The predicted risk class (0, 1, or 2)
            
        Returns:
            Explanation object with SHAP analysis
        """
        if not SHAP_AVAILABLE or self.shap_explainer is None:
            return None
        
        try:
            # Prepare input data
            input_df = self._prepare_input(patient_data)
            
            # Get SHAP values
            shap_values = self.shap_explainer.shap_values(input_df)
            
            # Handle different SHAP output formats
            if isinstance(shap_values, list):
                # Multi-class: use values for predicted class
                class_shap_values = shap_values[predicted_class][0]
            else:
                class_shap_values = shap_values[0]
            
            # Get base value
            if hasattr(self.shap_explainer, 'expected_value'):
                if isinstance(self.shap_explainer.expected_value, (list, np.ndarray)):
                    base_value = self.shap_explainer.expected_value[predicted_class]
                else:
                    base_value = self.shap_explainer.expected_value
            else:
                base_value = 0.0
            
            # Create contributions dictionary
            contributions = dict(zip(self.feature_names, class_shap_values))
            
            # Get top contributing factors
            top_factors = self._get_top_factors(
                contributions, 
                input_df.iloc[0].to_dict(),
                n=self.config['top_features_count']
            )
            
            # Generate narrative
            risk_labels = ['Low', 'Medium', 'High']
            narrative = self._generate_narrative(
                top_factors, 
                risk_labels[predicted_class],
                method='SHAP'
            )
            
            return Explanation(
                method='shap',
                risk_level=risk_labels[predicted_class],
                confidence=self._get_prediction_confidence(patient_data, predicted_class),
                top_factors=top_factors,
                all_contributions=contributions,
                narrative=narrative,
                base_value=base_value,
                shap_values=class_shap_values
            )
            
        except Exception as e:
            print(f"Error generating SHAP explanation: {e}")
            return None
    
    def explain_with_lime(self, patient_data: Dict, 
                          predicted_class: int) -> Optional[Explanation]:
        """
        Generate LIME-based local explanation.
        
        Args:
            patient_data: Dictionary of patient features
            predicted_class: The predicted risk class (0, 1, or 2)
            
        Returns:
            Explanation object with LIME analysis
        """
        if not LIME_AVAILABLE or self.lime_explainer is None:
            return None
        
        try:
            # Prepare input data
            input_df = self._prepare_input(patient_data)
            input_array = input_df.values[0]
            
            # Generate LIME explanation
            lime_exp = self.lime_explainer.explain_instance(
                input_array,
                self.model.predict_proba,
                num_features=self.config['lime_num_features'],
                top_labels=1
            )
            
            # Extract feature weights for the predicted class
            feature_weights = dict(lime_exp.as_list(label=predicted_class))
            
            # Map feature indices back to names
            contributions = {}
            for feat_name in self.feature_names:
                # LIME returns features as "feature_name <= value" or similar
                for key, weight in feature_weights.items():
                    if feat_name in key:
                        contributions[feat_name] = weight
                        break
                else:
                    contributions[feat_name] = 0.0
            
            # Get top contributing factors
            top_factors = self._get_top_factors(
                contributions,
                input_df.iloc[0].to_dict(),
                n=self.config['top_features_count']
            )
            
            # Generate narrative
            risk_labels = ['Low', 'Medium', 'High']
            narrative = self._generate_narrative(
                top_factors,
                risk_labels[predicted_class],
                method='LIME'
            )
            
            return Explanation(
                method='lime',
                risk_level=risk_labels[predicted_class],
                confidence=self._get_prediction_confidence(patient_data, predicted_class),
                top_factors=top_factors,
                all_contributions=contributions,
                narrative=narrative
            )
            
        except Exception as e:
            print(f"Error generating LIME explanation: {e}")
            return None
    
    def explain(self, patient_data: Dict, predicted_class: int,
                method: Optional[str] = None) -> Optional[Explanation]:
        """
        Generate explanation using the specified or default method.
        
        Args:
            patient_data: Dictionary of patient features
            predicted_class: The predicted risk class
            method: Explanation method ('shap', 'lime', or None for default)
            
        Returns:
            Explanation object
        """
        method = method or self.config['default_method']
        
        if method == 'shap':
            return self.explain_with_shap(patient_data, predicted_class)
        elif method == 'lime':
            return self.explain_with_lime(patient_data, predicted_class)
        elif method == 'both':
            # Return SHAP as primary, with LIME as fallback
            exp = self.explain_with_shap(patient_data, predicted_class)
            if exp is None:
                exp = self.explain_with_lime(patient_data, predicted_class)
            return exp
        else:
            # Try SHAP first, then LIME
            exp = self.explain_with_shap(patient_data, predicted_class)
            if exp is None:
                exp = self.explain_with_lime(patient_data, predicted_class)
            return exp
    
    def _prepare_input(self, patient_data: Dict) -> pd.DataFrame:
        """Prepare patient data as DataFrame for model input."""
        # Ensure all features are present
        input_dict = {}
        for feat in self.feature_names:
            input_dict[feat] = patient_data.get(feat, 0)
        
        return pd.DataFrame([input_dict])
    
    def _get_top_factors(self, contributions: Dict[str, float],
                         values: Dict[str, Any],
                         n: int = 5) -> List[FeatureContribution]:
        """
        Get the top N contributing factors sorted by absolute contribution.
        
        Args:
            contributions: Dictionary mapping feature names to contribution values
            values: Dictionary mapping feature names to their actual values
            n: Number of top factors to return
            
        Returns:
            List of FeatureContribution objects
        """
        # Sort by absolute contribution
        sorted_features = sorted(
            contributions.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )[:n]
        
        top_factors = []
        for feat_name, contribution in sorted_features:
            display_name = FEATURE_DISPLAY_NAMES.get(feat_name, feat_name.replace('_', ' ').title())
            value = values.get(feat_name, 0)
            direction = "increases_risk" if contribution > 0 else "decreases_risk"
            
            top_factors.append(FeatureContribution(
                feature_name=feat_name,
                display_name=display_name,
                value=value,
                contribution=contribution,
                direction=direction
            ))
        
        return top_factors
    
    def _get_prediction_confidence(self, patient_data: Dict, 
                                    predicted_class: int) -> float:
        """Get the model's confidence in the prediction."""
        try:
            input_df = self._prepare_input(patient_data)
            probabilities = self.model.predict_proba(input_df)[0]
            return float(probabilities[predicted_class])
        except:
            return 0.0
    
    def _generate_narrative(self, top_factors: List[FeatureContribution],
                           risk_level: str, method: str) -> str:
        """
        Generate a human-readable narrative explanation.
        
        Args:
            top_factors: List of top contributing factors
            risk_level: The predicted risk level
            method: The explanation method used
            
        Returns:
            Natural language explanation string
        """
        if not top_factors:
            return f"Unable to determine the specific factors contributing to the {risk_level} risk classification."
        
        # Separate factors by direction
        increasing = [f for f in top_factors if f.direction == "increases_risk"]
        decreasing = [f for f in top_factors if f.direction == "decreases_risk"]
        
        narrative_parts = []
        
        # Opening
        narrative_parts.append(
            f"This patient was classified as **{risk_level} Risk** based on the following clinical factors:"
        )
        
        # Factors increasing risk
        if increasing:
            narrative_parts.append("\n\n**Factors increasing risk:**")
            for factor in increasing:
                if isinstance(factor.value, (int, float)):
                    value_str = f"{factor.value:.1f}" if isinstance(factor.value, float) else str(factor.value)
                else:
                    value_str = str(factor.value)
                narrative_parts.append(f"- {factor.display_name} ({value_str})")
        
        # Factors decreasing risk
        if decreasing:
            narrative_parts.append("\n\n**Protective factors (decreasing risk):**")
            for factor in decreasing:
                if isinstance(factor.value, (int, float)):
                    value_str = f"{factor.value:.1f}" if isinstance(factor.value, float) else str(factor.value)
                else:
                    value_str = str(factor.value)
                narrative_parts.append(f"- {factor.display_name} ({value_str})")
        
        # Add method note
        narrative_parts.append(f"\n\n*Analysis performed using {method} explainability method.*")
        
        return "\n".join(narrative_parts)
    
    def get_feature_importance_chart_data(self, 
                                          explanation: Explanation) -> Dict:
        """
        Prepare data for feature importance visualization.
        
        Args:
            explanation: The explanation object
            
        Returns:
            Dictionary with chart data
        """
        if not explanation or not explanation.top_factors:
            return {}
        
        labels = [f.display_name for f in explanation.top_factors]
        values = [f.contribution for f in explanation.top_factors]
        colors = ['#dc3545' if v > 0 else '#28a745' for v in values]
        
        return {
            'labels': labels,
            'values': values,
            'colors': colors,
            'title': f'Top Factors Contributing to {explanation.risk_level} Risk'
        }


def create_demo_explanation(risk_level: str = "Medium") -> Explanation:
    """
    Create a demo explanation for testing without a model.
    
    Used when the XAI libraries are not available or model is not loaded.
    """
    demo_factors = [
        FeatureContribution(
            feature_name="age",
            display_name="Patient Age",
            value=72,
            contribution=0.25,
            direction="increases_risk"
        ),
        FeatureContribution(
            feature_name="oxygen_saturation",
            display_name="Oxygen Saturation (SpO2)",
            value=91,
            contribution=0.18,
            direction="increases_risk"
        ),
        FeatureContribution(
            feature_name="symptom_count",
            display_name="Number of Symptoms",
            value=4,
            contribution=0.12,
            direction="increases_risk"
        ),
        FeatureContribution(
            feature_name="blood_pressure_systolic",
            display_name="Systolic Blood Pressure",
            value=115,
            contribution=-0.08,
            direction="decreases_risk"
        ),
        FeatureContribution(
            feature_name="heart_rate",
            display_name="Heart Rate",
            value=78,
            contribution=-0.05,
            direction="decreases_risk"
        ),
    ]
    
    narrative = f"""This patient was classified as **{risk_level} Risk** based on the following clinical factors:

**Factors increasing risk:**
- Patient Age (72) - Advanced age increases vulnerability
- Oxygen Saturation (91%) - Below normal range
- Number of Symptoms (4) - Multiple presenting symptoms

**Protective factors (decreasing risk):**
- Systolic Blood Pressure (115 mmHg) - Within normal range
- Heart Rate (78 bpm) - Within normal range

*This is a demonstration explanation. Connect a trained model for actual SHAP/LIME analysis.*"""
    
    return Explanation(
        method='demo',
        risk_level=risk_level,
        confidence=0.75,
        top_factors=demo_factors,
        all_contributions={f.feature_name: f.contribution for f in demo_factors},
        narrative=narrative
    )
