import requests
import pandas as pd
from datetime import datetime
import os
import time
from tqdm import tqdm

def fetch_tle_data(satellite_names=None, norad_ids=None, output_file='data/tle_data.csv'):
    """
    Fetch TLE data for specified satellites from Celestrak.
    
    Args:
        satellite_names (list): List of satellite names to fetch
        norad_ids (list): List of NORAD IDs to fetch
        output_file (str): Path to save the TLE data
        
    Returns:
        str: Path to the saved TLE data file
    """
    try:
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Base URL for Celestrak
        base_url = "https://celestrak.org/NORAD/elements/gp.php"
        
        # Prepare the query parameters
        params = {}
        if satellite_names:
            params['NAME'] = ','.join(satellite_names)
        if norad_ids:
            params['CATNR'] = ','.join(map(str, norad_ids))
        
        # Add format parameter
        params['FORMAT'] = 'tle'
        
        print("Fetching TLE data from Celestrak...")
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        
        # Parse the TLE data
        lines = response.text.strip().split('\n')
        tle_data = []
        
        print("Processing TLE data...")
        with tqdm(total=len(lines)//3, desc="Processing TLEs", unit="satellite") as pbar:
            for i in range(0, len(lines), 3):
                if i + 2 < len(lines):
                    name = lines[i].strip()
                    line1 = lines[i+1].strip()
                    line2 = lines[i+2].strip()
                    
                    tle_data.append({
                        'Name': name,
                        'TLE1': line1,
                        'TLE2': line2,
                        'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                pbar.update(1)
        
        # Convert to DataFrame and save
        df = pd.DataFrame(tle_data)
        df.to_csv(output_file, index=False)
        
        print(f"\nTLE data saved to {output_file}")
        print(f"Total satellites processed: {len(tle_data)}")
        
        return output_file
        
    except Exception as e:
        print(f"Error fetching TLE data: {e}")
        return None

if __name__ == "__main__":
    # Example usage
    satellites = [
        "CALSPHERE 1",
        "CALSPHERE 2",
        "LCS 1",
        "TDRS 3",
        "USA 153"
    ]
    
    fetch_tle_data(satellite_names=satellites) 