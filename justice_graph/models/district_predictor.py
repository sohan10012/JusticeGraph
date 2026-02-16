from typing import Dict, Any
import pandas as pd
import os
import numpy as np

class DistrictBacklogPredictor:
    """
    Lookups historical district data to estimate case duration.
    """
    def __init__(self, data_path: str = "data/raw/data2.csv"):
        self.data_path = data_path
        self.df = None
        
        if os.path.exists(data_path):
            try:
                # Load full dataset into memory (Optimization: could use SQLite for large data)
                self.df = pd.read_csv(data_path)
                # Normalize column names
                self.df = self.df.rename(columns={
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
                })
                # Ensure string matching is case-insensitive
                self.df['state_lower'] = self.df['state'].astype(str).str.lower().str.strip()
                self.df['district_lower'] = self.df['district'].astype(str).str.lower().str.strip()
                self.df['case_type_lower'] = self.df['case_type'].astype(str).str.lower().str.strip()
                
            except Exception as e:
                print(f"Failed to load district data: {e}")
        else:
            print(f"WARNING: District data not found at {data_path}")

    def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        if self.df is None:
             raise ValueError("District data not loaded.")

        state = str(input_data.get('state', '')).lower().strip()
        district = str(input_data.get('district', '')).lower().strip()
        case_type = str(input_data.get('case_type', '')).lower().strip()
        
        # Filter
        mask = (
            (self.df['state_lower'] == state) & 
            (self.df['district_lower'] == district) & 
            (self.df['case_type_lower'] == case_type)
        )
        subset = self.df[mask]
        
        if subset.empty:
            return {
                "estimated_duration_days": 0.0,
                "estimated_duration_years": 0.0,
                "confidence": "Low",
                "explanation": f"No data found for {state}/{district} ({case_type})"
            }
            
        # Buckets to Days Mapping (approx midpoints/estimates)
        bucket_days = {
            'pending_0_1': 180,
            'pending_1_3': 730,
            'pending_3_5': 1460,
            'pending_5_10': 2737,
            'pending_10_20': 5475,
            'pending_20_30': 9125,
            'pending_over_30': 12000
        }
        
        # Aggregate logic: in case there are multiple rows (e.g. yearly data), sum them up?
        # The dataset seems to have 'Year' column. We should probably take the latest year?
        # For simplicity, let's sum all rows assuming they might represent different courts in the district
        # OR just take the latest year if multiple years exist. 
        # Inspecting previous `head` showed Year=2021.
        # Let's sum buckets across all matching rows.
        
        total_cases = 0
        total_days = 0
        
        # for variance calc
        weighted_variance_sum = 0
        
        rows_aggregated = subset[list(bucket_days.keys())].sum()
        
        # Calculate Weighted Mean
        for col, days in bucket_days.items():
            count = rows_aggregated[col]
            total_cases += count
            total_days += count * days
            
        if total_cases == 0:
             return {
                "estimated_duration_days": 180.0, # Default: optimistic
                "estimated_duration_years": 0.5,
                "confidence": "Low",
                "explanation": "District found but no pending cases recorded."
            }
            
        mean_days = total_days / total_cases
        
        # Calculate Variance for Confidence
        # Var = sum(count * (days - mean)^2) / total
        for col, days in bucket_days.items():
            count = rows_aggregated[col]
            weighted_variance_sum += count * ((days - mean_days) ** 2)
            
        variance = weighted_variance_sum / total_cases
        std_dev = np.sqrt(variance)
        
        # Heuristic Confidence based on Coefficient of Variation (CV)
        # CV = std_dev / mean
        cv = std_dev / mean_days if mean_days > 0 else 0
        
        if total_cases < 100:
            confidence = "Low"
        elif cv < 0.5:
            confidence = "High"
        elif cv < 1.0:
            confidence = "Medium"
        else:
            confidence = "Low" # High spread
            
        estimated_years = round(mean_days / 365.25, 1)
        
        # Explanation logic
        # Find dominant bucket
        max_bucket_col = rows_aggregated.idxmax()
        # Clean bucket name for display "pending_1_3" -> "1-3 years"
        bucket_human = max_bucket_col.replace('pending_', '').replace('_', '-') + " years"
        # Special case
        if "over" in bucket_human: bucket_human = "over 30 years"
        
        explanation = f"Based on {int(total_cases)} cases. High proportion of cases are in the {bucket_human} range."

        return {
            "estimated_duration_days": round(mean_days, 1),
            "estimated_duration_years": estimated_years,
            "confidence": confidence,
            "explanation": explanation
        }
