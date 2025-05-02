import os
import pandas as pd
from datetime import datetime, timedelta
from fetch_tle import fetch_and_save_tle_data
from train_model import train_and_save_model
from predict_from_tle import process_tle_file

def check_tle_data_freshness(tle_file='data/tle_data.csv', max_age_hours=24):
    """
    Check if the TLE data file exists and is recent enough.
    
    Args:
        tle_file (str): Path to the TLE data file
        max_age_hours (int): Maximum age of TLE data in hours
        
    Returns:
        bool: True if data is fresh, False if needs updating
    """
    if not os.path.exists(tle_file):
        return False
        
    # Get file modification time
    file_time = datetime.fromtimestamp(os.path.getmtime(tle_file))
    current_time = datetime.now()
    
    # Check if file is older than max_age_hours
    if current_time - file_time > timedelta(hours=max_age_hours):
        return False
        
    return True

def main():
    try:
        # Check if TLE data needs updating
        if not check_tle_data_freshness():
            print("TLE data is either missing or older than 24 hours.")
            print("Fetching fresh TLE data...")
            fetch_and_save_tle_data()
        else:
            print("Using existing TLE data (less than 24 hours old)")
        
        # Check if model exists and is recent
        model_path = 'models/conjunction_model.pkl'
        if not os.path.exists(model_path):
            print("\nModel not found. Training new model...")
            train_and_save_model()
        else:
            # Check model age
            model_time = datetime.fromtimestamp(os.path.getmtime(model_path))
            current_time = datetime.now()
            if current_time - model_time > timedelta(days=7):  # Retrain model weekly
                print("\nModel is older than 7 days. Retraining...")
                train_and_save_model()
            else:
                print("\nUsing existing model")
        
        # Process TLE data and make predictions
        print("\nProcessing TLE data and making predictions...")
        process_tle_file('data/tle_data.csv', max_pairs=50, threshold_km=10)
        
    except Exception as e:
        print(f"Error in main process: {e}")
        raise

if __name__ == "__main__":
    main() 