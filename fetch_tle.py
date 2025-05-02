import requests
import pandas as pd
import os
from datetime import datetime

def fetch_and_save_tle_data():
    """
    Fetch TLE data from Celestrak and save it to CSV file.
    """
    try:
        # URL for active satellites TLE data
        url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle"
        
        # Fetch the data
        print("Fetching TLE data from Celestrak...")
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Parse the TLE data
        tle_data = []
        lines = response.text.strip().split('\n')
        
        for i in range(0, len(lines), 3):
            if i + 2 < len(lines):
                name = lines[i].strip()
                tle1 = lines[i + 1].strip()
                tle2 = lines[i + 2].strip()
                
                tle_data.append({
                    'Name': name,
                    'TLE1': tle1,
                    'TLE2': tle2
                })
        
        # Create DataFrame
        df = pd.DataFrame(tle_data)
        
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        # Save to CSV
        output_file = 'data/tle_data.csv'
        df.to_csv(output_file, index=False)
        
        print(f"\nSuccessfully fetched {len(df)} satellite TLEs")
        print(f"Data saved to {output_file}")
        
        # Print some statistics
        print("\nDataset Statistics:")
        print(f"Total satellites: {len(df)}")
        print(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"Error fetching TLE data: {e}")
        raise

if __name__ == "__main__":
    fetch_and_save_tle_data() 