"""
Machine Learning Model Module for CDSS

Handles model training, evaluation, and inference for
medical error risk prediction.
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional, List
from pathlib import Path
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from cdss_config import MODEL_PATH, ENCODER_PATH
from ml.preprocessing import DataPreprocessor
from ml.feature_encoder import FeatureEncoder


class RiskPredictionModel:
    """Machine Learning model for medical error risk prediction."""
    
    def __init__(self, model_type: str = 'random_forest'):
        """
        Initialize the model.
        
        Args:
            model_type: Type of model ('random_forest', 'logistic_regression', 'decision_tree')
        """
        self.model_type = model_type
        self.model = self._create_model(model_type)
        self.preprocessor = DataPreprocessor()
        self.encoder = FeatureEncoder()
        self.is_trained = False
        self.training_metrics = {}
        
    def _create_model(self, model_type: str):
        """Create the specified model type."""
        models = {
            'random_forest': RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            ),
            'logistic_regression': LogisticRegression(
                max_iter=1000,
                random_state=42
            ),
            'decision_tree': DecisionTreeClassifier(
                max_depth=8,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42
            )
        }
        return models.get(model_type, models['random_forest'])
    
    def train(self, df: pd.DataFrame, target_col: str = 'risk_level') -> Dict:
        """
        Train the model on the provided data.
        
        Args:
            df: Training DataFrame with features and target
            target_col: Name of target column
            
        Returns:
            Dictionary with training metrics
        """
        # Preprocess data
        df_clean = self.preprocessor.clean_data(df)
        df_processed = self.preprocessor.prepare_features(df_clean.to_dict('records')[0] if len(df_clean) == 1 else df_clean.iloc[0].to_dict())
        
        # For batch processing, prepare all features
        features_list = []
        for _, row in df_clean.iterrows():
            row_dict = row.to_dict()
            processed = self.preprocessor.prepare_features(row_dict)
            features_list.append(processed)
        
        df_features = pd.concat(features_list, ignore_index=True)
        
        # Encode features
        X = self.encoder.fit_transform(df_features)
        y = df_clean[target_col].values
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Train model
        self.model.fit(X_train, y_train)
        self.is_trained = True
        
        # Evaluate
        y_pred = self.model.predict(X_test)
        
        self.training_metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, average='weighted'),
            'recall': recall_score(y_test, y_pred, average='weighted'),
            'f1_score': f1_score(y_test, y_pred, average='weighted'),
            'classification_report': classification_report(y_test, y_pred, output_dict=True)
        }
        
        # Cross-validation score
        cv_scores = cross_val_score(self.model, X, y, cv=5)
        self.training_metrics['cv_mean'] = cv_scores.mean()
        self.training_metrics['cv_std'] = cv_scores.std()
        
        return self.training_metrics
    
    def predict(self, patient_data: Dict) -> Tuple[int, np.ndarray]:
        """
        Predict risk level for a patient.
        
        Args:
            patient_data: Dictionary with patient information
            
        Returns:
            Tuple of (predicted risk level, probability array)
        """
        if not self.is_trained:
            raise ValueError("Model has not been trained yet!")
            
        # Encode patient features
        X = self.encoder.encode_patient(patient_data)
        
        # Predict
        risk_level = self.model.predict(X)[0]
        probabilities = self.model.predict_proba(X)[0]
        
        return int(risk_level), probabilities
    
    def predict_proba(self, patient_data: Dict) -> np.ndarray:
        """Get prediction probabilities for each risk level."""
        if not self.is_trained:
            raise ValueError("Model has not been trained yet!")
            
        X = self.encoder.encode_patient(patient_data)
        return self.model.predict_proba(X)[0]
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance scores (for tree-based models)."""
        if not self.is_trained:
            return {}
            
        if hasattr(self.model, 'feature_importances_'):
            importances = self.model.feature_importances_
            labels = self.encoder.get_feature_importance_labels()
            return dict(zip(labels, importances))
        return {}
    
    def save(self, model_path: Optional[str] = None, encoder_path: Optional[str] = None):
        """Save model and encoder to files."""
        model_path = Path(model_path) if model_path else MODEL_PATH
        encoder_path = Path(encoder_path) if encoder_path else ENCODER_PATH
        
        # Create directories if needed
        model_path.parent.mkdir(parents=True, exist_ok=True)
        encoder_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save model
        joblib.dump({
            'model': self.model,
            'model_type': self.model_type,
            'is_trained': self.is_trained,
            'training_metrics': self.training_metrics
        }, model_path)
        
        # Save encoder
        self.encoder.save(str(encoder_path))
        
        print(f"Model saved to: {model_path}")
        print(f"Encoder saved to: {encoder_path}")
        
    @classmethod
    def load(cls, model_path: Optional[str] = None, encoder_path: Optional[str] = None) -> 'RiskPredictionModel':
        """Load model and encoder from files."""
        model_path = Path(model_path) if model_path else MODEL_PATH
        encoder_path = Path(encoder_path) if encoder_path else ENCODER_PATH
        
        # Load model data
        model_data = joblib.load(model_path)
        
        # Create instance
        instance = cls(model_type=model_data['model_type'])
        instance.model = model_data['model']
        instance.is_trained = model_data['is_trained']
        instance.training_metrics = model_data['training_metrics']
        
        # Load encoder
        instance.encoder = FeatureEncoder.load(str(encoder_path))
        
        return instance


def train_and_compare_models(df: pd.DataFrame) -> Dict:
    """
    Train and compare multiple model types.
    
    Args:
        df: Training DataFrame
        
    Returns:
        Dictionary with results for each model type
    """
    results = {}
    
    for model_type in ['random_forest', 'logistic_regression', 'decision_tree']:
        print(f"\nTraining {model_type}...")
        model = RiskPredictionModel(model_type=model_type)
        metrics = model.train(df)
        results[model_type] = {
            'model': model,
            'metrics': metrics
        }
        print(f"  Accuracy: {metrics['accuracy']:.4f}")
        print(f"  F1 Score: {metrics['f1_score']:.4f}")
        print(f"  CV Mean: {metrics['cv_mean']:.4f} (+/- {metrics['cv_std']:.4f})")
        
    return results


if __name__ == "__main__":
    # Example: Train model on generated data
    from data.generate_data import generate_sample_data
    
    print("Generating training data...")
    df = generate_sample_data(n_samples=1000)
    
    print("\nComparing models...")
    results = train_and_compare_models(df)
    
    # Select best model based on F1 score
    best_model_type = max(results, key=lambda x: results[x]['metrics']['f1_score'])
    best_model = results[best_model_type]['model']
    
    print(f"\n✅ Best model: {best_model_type}")
    print(f"   F1 Score: {results[best_model_type]['metrics']['f1_score']:.4f}")
    
    # Save best model
    best_model.save()
    print("\n✅ Model saved successfully!")
