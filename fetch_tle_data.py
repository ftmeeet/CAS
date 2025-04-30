import requests
import pandas as pd
from datetime import datetime, timedelta
import os
import time
from tqdm import tqdm

def fetch_tle_data(output_file='data/tle_data.csv'):
    """
    Fetch TLE data for active satellites from Celestrak.
    Filters out satellites with TLEs older than 20 days.
    
    Args:
        output_file (str): Path to save the TLE data
        
    Returns:
        str: Path to the saved TLE data file
    """
    try:
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # URL for active satellites
        url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle"
        
        # Fetch TLE data
        response = requests.get(url)
        response.raise_for_status()
        
        # Parse the TLE data
        lines = response.text.strip().split('\n')
        tle_data = []
        
        # Process TLEs with progress bar
        with tqdm(total=len(lines)//3, desc="Processing TLEs", unit="satellite") as pbar:
            for i in range(0, len(lines), 3):
                if i + 2 < len(lines):
                    name = lines[i].strip()
                    line1 = lines[i+1].strip()
                    line2 = lines[i+2].strip()
                    
                    # Extract epoch from TLE line 1
                    epoch_str = line1[18:32]  # TLE epoch is in YYDDD.DDDDDDDD format
                    year = int(epoch_str[:2])
                    day = float(epoch_str[2:])
                    
                    # Convert to datetime
                    epoch = datetime.strptime(f"{year:02d}{int(day):03d}", "%y%j")
                    epoch = epoch + timedelta(days=day - int(day))
                    
                    # Calculate age in days
                    age_days = (datetime.utcnow() - epoch).total_seconds() / 86400
                    
                    # Only include if TLE is less than 20 days old
                    if age_days <= 20:
                        tle_data.append({
                            'Name': name,
                            'TLE1': line1,
                            'TLE2': line2,
                            'Epoch': epoch,
                            'Age_Days': age_days,
                            'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                pbar.update(1)
        
        # Convert to DataFrame and save
        df = pd.DataFrame(tle_data)
        df.to_csv(output_file, index=False)
        
        return output_file
        
    except Exception:
        return None

if __name__ == "__main__":
    # Fetch TLE data for all active satellites
    fetch_tle_data() 