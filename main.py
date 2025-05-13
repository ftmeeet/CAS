import os
import pandas as pd
from datetime import datetime, timedelta
from fetch_tle import fetch_and_save_tle_data
from train_model import train_and_save_model
from predict_from_tle import process_tle_file
import warnings
from space_weather import get_latest_space_weather_data

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
        # Create necessary directories
        os.makedirs('data', exist_ok=True)
        os.makedirs('models', exist_ok=True)
        
        # Check and update TLE data if needed
        if not check_tle_freshness():
            print("TLE data is stale or missing. Fetching new data...")
            fetch_and_save_tle_data()
            print("TLE data updated successfully.")
            
        # Check and retrain model if needed
        if not check_model_freshness():
            print("Model is stale or missing. Training new model...")
            train_and_save_model()
            print("Model trained successfully.")

        # First fetch the latest space weather data
        print("Updating space weather data...")
        get_latest_space_weather_data()
            
        # Process TLE file
        print("Processing TLE data for conjunction analysis...")
        process_tle_file(
            user_tle_file='data/user_tle.csv',
            tle_data_file='data/tle_data.csv',
            model_path='models/conjunction_model.pkl',
            threshold_km=100
        )
        print("Conjunction analysis completed successfully.")
        
    except Exception as e:
        print(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    main()