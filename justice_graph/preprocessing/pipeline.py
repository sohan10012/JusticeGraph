import re
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from typing import List, Optional

class TextPreprocessor:
    """
    Preprocessing pipeline for legal text.
    """
    def __init__(self):
         self.stopwords = set(['the', 'and', 'is', 'in', 'to', 'of', 'a', 'for', 'on', 'with', 'as', 'by', 'at', 'an', 'be', 'this', 'that', 'which']) # Simple list, can be expanded

    def clean_text(self, text: str) -> str:
        """
        Clean raw legal text: lowercase, remove special chars, extra spaces.
        """
        if not isinstance(text, str):
            return ""
        
        # Lowercase
        text = text.lower()
        
        # Remove special chars and numbers (keep basic punctuation for now if needed, but usually strip for BoW)
        text = re.sub(r'[^a-z\s]', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove stopwords (basic)
        text = ' '.join([word for word in text.split() if word not in self.stopwords])
        
        return text

    def process_batch(self, texts: List[str]) -> List[str]:
        return [self.clean_text(t) for t in texts]

class FeatureEngineer:
    """
    Feature engineering for judicial data.
    """
    def calculate_case_duration(self, df: pd.DataFrame, filing_col: str, decision_col: str) -> pd.DataFrame:
        """
        Calculate case duration in days.
        """
        df[filing_col] = pd.to_datetime(df[filing_col], errors='coerce')
        df[decision_col] = pd.to_datetime(df[decision_col], errors='coerce')
        
        df['duration_days'] = (df[decision_col] - df[filing_col]).dt.days
        return df

    def extract_act_features(self, df: pd.DataFrame, act_col: str) -> pd.DataFrame:
        """
        One-hot encode or vectorise Act/Section information.
        For now, just a simple count of acts.
        """
        # Placeholder for more complex logic like extracting "IPC 302" vs "IPC 420"
        df['act_count'] = df[act_col].apply(lambda x: len(str(x).split(',')) if pd.notnull(x) else 0)
        return df

    def compute_court_risk_score(self, pending: int, disposal_rate: float, judge_strength: int) -> float:
        """
        Compute backlog risk score based on simple heuristics.
        """
        if judge_strength == 0:
            return 1.0 # Max risk
        
        # Heuristic: Years to clear backlog at current rate
        if disposal_rate <= 0:
            return 1.0
            
        years_to_clear = pending / (disposal_rate * 12)
        
        # Normalize: > 5 years is high risk (1.0)
        risk_score = min(max(years_to_clear / 5.0, 0.0), 1.0)
        return risk_score
