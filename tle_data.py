import requests
import pandas as pd
import os

# URLs for CelesTrak data
general_tle_url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle"
debris_tle_url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=debris&FORMAT=tle"

# File path for storing the merged CSV
csv_filename = "satellite_data.csv"

def fetch_tle_data(url):
    """Fetch TLE data from a given URL."""
    response = requests.get(url)
    if response.status_code == 200:
        return response.text.strip().split("\n")
    else:
        print(f"Failed to fetch data from {url}")
        return []

def parse_tle(lines):
    """Parse TLE data into a dictionary."""
    satellites = []
    for i in range(0, len(lines), 3):
        if i + 2 < len(lines):
            name = lines[i].strip()
            tle_1 = lines[i + 1].strip()
            tle_2 = lines[i + 2].strip()
            satellites.append({"Name": name, "TLE1": tle_1, "TLE2": tle_2})
    return satellites

# Fetch and parse TLE data
general_tle_data = parse_tle(fetch_tle_data(general_tle_url))
debris_tle_data = parse_tle(fetch_tle_data(debris_tle_url))

# Combine both datasets
merged_data = general_tle_data + debris_tle_data
new_df = pd.DataFrame(merged_data)

# Check if the CSV file exists
if os.path.exists(csv_filename):
    old_df = pd.read_csv(csv_filename)
    
    # Merge old and new data, keeping only the latest version
    updated_df = pd.concat([old_df, new_df]).drop_duplicates(subset=["Name"], keep="last")

    # Check if there are any changes
    if not new_df.equals(old_df):
        updated_df.to_csv(csv_filename, index=False)
        print("CSV file updated with new data.")
    else:
        print("No new data found. CSV remains unchanged.")
else:
    new_df.to_csv(csv_filename, index=False)
    print("New CSV file created.")

print("Process completed.")
