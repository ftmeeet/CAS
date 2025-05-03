import os
import pandas as pd
from datetime import datetime, timedelta
from fetch_tle import fetch_and_save_tle_data
from train_model import train_and_save_model
from predict_from_tle import process_tle_file
import warnings

# Suppress all warnings
warnings.filterwarnings('ignore')

def check_tle_freshness(tle_file='data/tle_data.csv', max_age_hours=24):
    """
    Check if TLE data is fresh enough.
    
    Args:
        tle_file (str): Path to the TLE data file
        max_age_hours (int): Maximum age in hours before data is considered stale
        
    Returns:
        bool: True if data is fresh, False otherwise
    """
    if not os.path.exists(tle_file):
        return False
        
    file_time = datetime.fromtimestamp(os.path.getmtime(tle_file))
    age_hours = (datetime.now() - file_time).total_seconds() / 3600
    
    return age_hours <= max_age_hours

def check_model_freshness(model_file='models/conjunction_model.pkl', max_age_days=7):
    """
    Check if the model is fresh enough.
    
    Args:
        model_file (str): Path to the model file
        max_age_days (int): Maximum age in days before model is considered stale
        
    Returns:
        bool: True if model is fresh, False otherwise
    """
    if not os.path.exists(model_file):
        return False
        
    file_time = datetime.fromtimestamp(os.path.getmtime(model_file))
    age_days = (datetime.now() - file_time).days
    
    return age_days <= max_age_days

def main():
    """
    Main function to run the conjunction analysis.
    """
    try:
        # Check TLE data freshness
        if not check_tle_freshness():
            print("Warning: TLE data is stale or missing. Please update the data.")
            return
            
        # Check model freshness
        if not check_model_freshness():
            print("Warning: Model is stale or missing. Please retrain the model.")
            return
            
        # Process TLE file
        process_tle_file(
            user_tle_file='data/user_tle.csv',
            tle_data_file='data/tle_data.csv',
            model_path='models/conjunction_model.pkl',
            threshold_km=100
        )
        
    except Exception as e:
        print(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    main() 