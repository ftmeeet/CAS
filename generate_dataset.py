import pandas as pd
import numpy as np
from utils import create_propagator, extract_features, are_orbits_close, propagate_and_find_closest, is_tle_recent, perigee_apogee_overlap
from org.orekit.time import AbsoluteDate, TimeScalesFactory
import datetime
from tqdm import tqdm

# Load TLEs
tle_df = pd.read_csv('tle_data.csv')

samples = []
labels = []

utc = TimeScalesFactory.getUTC()
now = datetime.datetime.utcnow()
start_date = AbsoluteDate(now.year, now.month, now.day, now.hour, now.minute, float(now.second), utc)

# User-configurable propagation duration (e.g., 1 day = 86400 seconds)
PROPAGATION_DURATION_SEC = 86400
PROPAGATION_STEP_SEC = 180        # Smart sieve: large step

n = len(tle_df)
total_pairs = n * (n - 1) // 2  # Number of unique pairs

with tqdm(total=total_pairs, desc="Processing pairs") as pbar:
    for i in range(n):
        for j in range(i+1, n):
            tle1 = create_propagator(tle_df.iloc[i]['TLE1'], tle_df.iloc[i]['TLE2']).getTLE()
            tle2 = create_propagator(tle_df.iloc[j]['TLE1'], tle_df.iloc[j]['TLE2']).getTLE()

            # Out-of-date TLE filter
            if not (is_tle_recent(tle1) and is_tle_recent(tle2)):
                pbar.update(1)
                continue

            # Perigee/Apogee filter
            if not perigee_apogee_overlap(tle1, tle2, dth_km=100):
                pbar.update(1)
                continue

            # Filter by close orbits
            if not are_orbits_close(tle1, tle2):
                continue

            # Get feature vector
            feature = extract_features(tle1, tle2)

            # Propagate and find minimum distance
            min_dist, _ = propagate_and_find_closest(
                tle1, tle2, start_date,
                duration_sec=PROPAGATION_DURATION_SEC,
                coarse_step=PROPAGATION_STEP_SEC,
                fine_step=60,
                threshold_km=10
            )

            samples.append(feature)

            # If min distance < 10 km, mark as conjunction
            label = 1 if min_dist < 10 else 0
            labels.append(label)
            pbar.update(1)  # Update progress bar

print(f"Generated {len(samples)} samples.")

# Save the dataset
df = pd.DataFrame(samples, columns=['mm_diff', 'ecc_diff', 'inc_diff', 'raan_diff', 'argp_diff', 'mnan_diff'])
df['label'] = labels
df.to_csv('training_dataset.csv', index=False)
print("Saved training dataset to 'training_dataset.csv'")
