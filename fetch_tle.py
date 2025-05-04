import requests
import pandas as pd
from datetime import datetime
import time
import os
from urllib3.exceptions import InsecureRequestWarning
import warnings

# Suppress SSL warnings
warnings.filterwarnings('ignore', category=InsecureRequestWarning)

def fetch_tle_data(max_retries=3, retry_delay=5):
    """
    Fetch TLE data from Celestrak with retry logic.
    
    Args:
        max_retries (int): Maximum number of retry attempts
        retry_delay (int): Delay between retries in seconds
        
    Returns:
        list: List of TLE data
    """
    urls = [
        "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle",
    ]
    
    all_tles = []
    
    for url in urls:
        for attempt in range(max_retries):
            try:
                print(f"Fetching from {url} (attempt {attempt + 1}/{max_retries})...")
                
                # Create a session with retry logic
                session = requests.Session()
                session.verify = False  # Disable SSL verification
                
                response = session.get(url, timeout=30)
                response.raise_for_status()
                
                # Parse TLEs
                lines = response.text.strip().split('\n')
                for i in range(0, len(lines), 3):
                    if i + 2 < len(lines):
                        name = lines[i].strip()
                        line1 = lines[i + 1].strip()
                        line2 = lines[i + 2].strip()
                        all_tles.append({
                            'Name': name,
                            'TLE1': line1,
                            'TLE2': line2
                        })
                
                print(f"Successfully fetched {len(all_tles)} TLEs from {url}")
                break  # Success, exit retry loop
                
            except requests.exceptions.RequestException as e:
                print(f"Error fetching from {url}: {e}")
                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print(f"Failed to fetch from {url} after {max_retries} attempts")
    
    return all_tles

def save_tle_data(tles, file_path='data/tle_data.csv'):
    """
    Save TLE data to CSV file.
    
    Args:
        tles (list): List of TLE data
        file_path (str): Path to save the data
    """
    try:
        # Create DataFrame
        df = pd.DataFrame(tles)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Save to CSV
        df.to_csv(file_path, index=False)
        print(f"TLE data saved to {file_path}")
        
    except Exception as e:
        print(f"Error saving TLE data: {e}")
        raise

def fetch_and_save_tle_data():
    """
    Fetch TLE data and save it to a CSV file.
    """
    try:
        print("Fetching TLE data from Celestrak...")
        tles = fetch_tle_data()
        
        if not tles:
            print("No TLE data was fetched successfully")
            return
            
        save_tle_data(tles)
        print("TLE data update completed successfully")
        
    except Exception as e:
        print(f"Error in fetch_and_save_tle_data: {e}")
        raise

if __name__ == "__main__":
    fetch_and_save_tle_data() 