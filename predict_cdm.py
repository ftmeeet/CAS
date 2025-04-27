import pandas as pd
import joblib
from utils import *

data = pd.read_csv("new_tle_data.csv")  # your new incoming TLEs
clf = joblib.load("conjunction_predictor.pkl")

for i in range(len(data)):
    for j in range(i+1, len(data)):
        tle1 = TLE(data.iloc[i]["TLE1"], data.iloc[i]["TLE2"])
        tle2 = TLE(data.iloc[j]["TLE1"], data.iloc[j]["TLE2"])

        features = extract_features(tle1, tle2)
        pred = clf.predict([features])[0]

        if pred == 1:
            min_dist, tca = propagate_and_find_closest(tle1, tle2, AbsoluteDate.now())
            if min_dist < 10:
                print(f"Potential Conjunction between {data.iloc[i]['Name']} and {data.iloc[j]['Name']} at {tca} with distance {min_dist:.2f} km")


print("Prediction complete ✅")