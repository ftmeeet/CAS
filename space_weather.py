import requests
import pandas as pd
from datetime import datetime, timedelta
import os
from urllib3.exceptions import InsecureRequestWarning
import warnings
import time

# Suppress SSL warnings
warnings.filterwarnings('ignore', category=InsecureRequestWarning)

def fetch_space_weather_data(max_retries=3, retry_delay=5):
    """
    Fetch space weather data from GFZ Potsdam.
    
    Args:
        max_retries (int): Maximum number of retry attempts
        retry_delay (int): Delay between retries in seconds
        
    Returns:
        pd.DataFrame: DataFrame containing space weather data
    """
    url = "https://www-app3.gfz-potsdam.de/kp_index/Kp_ap_Ap_SN_F107_since_1932.txt"
    
    for attempt in range(max_retries):
        try:
            
            # Create a session with retry logic
            session = requests.Session()
            session.verify = False  # Disable SSL verification
            
            response = session.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse the data
            lines = response.text.strip().split('\n')
            data = []
            
            for line in lines:
                if line.startswith('#'):
                    continue
                    
                parts = line.split()
                if len(parts) >= 28:  # Ensure we have all required fields
                    data.append({
                        'Date': f"{parts[0]}-{parts[1].zfill(2)}-{parts[2].zfill(2)}",
                        'Kp1': float(parts[6]),
                        'Kp2': float(parts[7]),
                        'Kp3': float(parts[8]),
                        'Kp4': float(parts[9]),
                        'Kp5': float(parts[10]),
                        'Kp6': float(parts[11]),
                        'Kp7': float(parts[12]),
                        'Kp8': float(parts[13]),
                        'Ap': int(parts[22]),
                        'SN': int(parts[23]),
                        'F10.7obs': float(parts[24]),
                        'F10.7adj': float(parts[25])
                    })
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            df['Date'] = pd.to_datetime(df['Date'])
            
            # Calculate daily average Kp
            kp_columns = [f'Kp{i}' for i in range(1, 9)]
            df['Kp_avg'] = df[kp_columns].mean(axis=1)
            return df
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching space weather data: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f"Failed to fetch space weather data after {max_retries} attempts")
                raise

def save_space_weather_data(df, file_path='data/space_weather.csv'):
    """
    Save space weather data to CSV file.
    
    Args:
        df (pd.DataFrame): DataFrame containing space weather data
        file_path (str): Path to save the data
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Save to CSV
        df.to_csv(file_path, index=False)
        print(f"Space weather data saved to {file_path}")
        
    except Exception as e:
        print(f"Error saving space weather data: {e}")
        raise

def get_latest_space_weather_data():
    """
    Get the latest space weather data and save it to a CSV file.
    """
    try:
        print("Fetching latest space weather data...")
        df = fetch_space_weather_data()
        
        if df is not None:
            save_space_weather_data(df)
            print("Space weather data update completed successfully")
            
    except Exception as e:
        print(f"Error in get_latest_space_weather_data: {e}")
        raise

if __name__ == "__main__":
    get_latest_space_weather_data() 