from typing import Dict
import pandas as pd
import joblib
import os

class BacklogPredictor:
    """
    Predicts court backlog risk using Gradient Boosting (XGBoost).
    Inference-only.
    """
    def __init__(self, model_path: str = "models/backlog_model.pkl"):
        self.model_path = model_path
        if os.path.exists(model_path):
            self.model = joblib.load(model_path)
        else:
            print(f"WARNING: Model not found at {model_path}. Prediction will fail.")
            self.model = None

    def predict(self, X: pd.DataFrame):
        """
        Predict risk probability.
        """
        if self.model is None:
             raise ValueError("Model not loaded.")
        return self.model.predict_proba(X)[:, 1] # Return probability of high risk

    def explain(self, X_sample: pd.DataFrame) -> Dict[str, float]:
        """
        Explain prediction using feature importance.
        """
        if self.model is None:
             raise ValueError("Model not loaded.")
            
        importances = self.model.feature_importances_
        features = X_sample.columns
        # distinct: map numpy float32 to python float
        return {f: float(imp) for f, imp in zip(features, importances)}
