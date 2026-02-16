import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import joblib
import os

# Config
DATA_PATH = "data/raw/data2.csv"
MODEL_PATH = "models/district_model.joblib"

def load_and_preprocess():
    print("Loading data...")
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Data not found at {DATA_PATH}")
    
    df = pd.read_csv(DATA_PATH)
    
    # Rename columns for easier access
    column_map = {
        'srcStateName': 'state',
        'srcDistrictName': 'district',
        'District and Taluk Court Case type': 'case_type',
        'Pending cases for a period of 0 to 1 Years': 'pending_0_1',
        'Pending cases for a period of 1 to 3 Years': 'pending_1_3',
        'Pending cases for a period of 3 to 5 Years': 'pending_3_5',
        'Pending cases for a period of 5 to 10 Years': 'pending_5_10',
        'Pending cases for a period of 10 to 20 Years': 'pending_10_20',
        'Pending cases for a period of 20 to 30 Years': 'pending_20_30',
        'Pending cases over 30 Years': 'pending_over_30'
    }
    df = df.rename(columns=column_map)
    
    # Fill NA
    features = ['pending_0_1', 'pending_1_3', 'pending_3_5', 
                'pending_5_10', 'pending_10_20', 'pending_20_30', 'pending_over_30']
    
    for f in features:
        # creating numeric convert in case of bad string formatting (e.g. "1,200")
        df[f] = pd.to_numeric(df[f], errors='coerce').fillna(0)

    # --- Feature Engineering ---
    print("Engineering features...")
    
    # Total Pending
    df['total_pending'] = df[features].sum(axis=1)
    
    # Avoid division by zero - Filter HERE before creating Y
    mask = df['total_pending'] > 0
    df = df[mask].copy()

    # Long Pending Share (>10 years)
    long_pending_cols = ['pending_10_20', 'pending_20_30', 'pending_over_30']
    df['long_pending_share'] = df[long_pending_cols].sum(axis=1) / df['total_pending']
    
    # Delay Severity Index (Weighted sum)
    # Weights: 0-1: 1, 1-3: 2, 3-5: 3, 5-10: 5, 10-20: 10, 20-30: 20, >30: 50
    weights = {
        'pending_0_1': 1,
        'pending_1_3': 2,
        'pending_3_5': 3,
        'pending_5_10': 5,
        'pending_10_20': 10,
        'pending_20_30': 20,
        'pending_over_30': 50
    }
    
    df['severity_index'] = 0
    for col, w in weights.items():
        df['severity_index'] += df[col] * w
        
    # Normalize Severity by total cases to get "Average Severity per Case"
    df['avg_severity'] = df['severity_index'] / df['total_pending']

    # --- Target Creation ---
    # Define Risk Categories based on Average Severity Quartiles
    df['risk_category'] = pd.qcut(df['avg_severity'], q=4, labels=['Low', 'Medium', 'High', 'Critical'])
    
    # Encode Categoricals
    le_state = LabelEncoder()
    le_district = LabelEncoder()
    le_type = LabelEncoder()
    
    df['state_enc'] = le_state.fit_transform(df['state'].astype(str))
    df['district_enc'] = le_district.fit_transform(df['district'].astype(str))
    df['type_enc'] = le_type.fit_transform(df['case_type'].astype(str))
    
    X = df[['state_enc', 'district_enc', 'type_enc', 'total_pending', 'long_pending_share', 'avg_severity'] + features]
    y = df['risk_category']
    
    print(f"DEBUG: X shape: {X.shape}, y shape: {y.shape}")
    return X, y, le_state, le_district, le_type

def train():
    X, y, le_s, le_d, le_t = load_and_preprocess()
    
    print(f"Training on {len(X)} records...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train) # Fix: match target size to feature size
    
    print("Model trained.")
    
    # Save artifacts
    artifacts = {
        'model': clf,
        'encoders': {
            'state': le_s,
            'district': le_d,
            'case_type': le_t
        }
    }
    
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(artifacts, MODEL_PATH)
    print(f"Saved to {MODEL_PATH}")

if __name__ == "__main__":
    train()
