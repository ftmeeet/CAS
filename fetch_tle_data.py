import requests
import pandas as pd

# URLs for CelesTrak TLE data (active satellites and debris)
CELESTRAK_URLS = {
    "active": "http://www.celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle",
}

def fetch_tle(url):
    response = requests.get(url)
    response.raise_for_status()
    lines = response.text.strip().splitlines()
    tles = []
    for i in range(0, len(lines), 3):
        if i+2 < len(lines):
            name = lines[i].strip()
            tle1 = lines[i+1].strip()
            tle2 = lines[i+2].strip()
            tles.append({"Name": name, "TLE1": tle1, "TLE2": tle2})
    return tles

def main():
    all_tles = []
    for label, url in CELESTRAK_URLS.items():
        print(f"Fetching {label} TLEs...")
        tles = fetch_tle(url)
        for tle in tles:
            tle["Type"] = label
        all_tles.extend(tles)
    df = pd.DataFrame(all_tles)
    df.to_csv("tle_data.csv", index=False)
    print(f"Saved {len(df)} TLEs to tle_data.csv")

if __name__ == "__main__":
    main()