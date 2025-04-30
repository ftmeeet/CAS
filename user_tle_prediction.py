import pandas as pd
import numpy as np
import joblib
from utils import extract_features_from_tles, propagate_and_find_closest, are_orbits_close, perigee_apogee_overlap, is_tle_recent
import os
from datetime import datetime, timedelta
import orekit
from orekit.pyhelpers import setup_orekit_curdir
from org.orekit.time import AbsoluteDate, TimeScalesFactory
from org.orekit.propagation.analytical.tle import TLE
from tqdm import tqdm

# Initialize Orekit
orekit.initVM()
setup_orekit_curdir(from_pip_library=True)

def read_user_tle():
    """
    Read TLE from the user_tle.txt file.
    Returns:
        tuple: (satellite_name, TLE line 1, TLE line 2)
    """
    try:
        with open('data/user_tle.txt', 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
            
            if len(lines) != 3:
                raise ValueError(f"Invalid TLE file format. Expected 3 lines, got {len(lines)}")
            
            # Validate TLE format
            satellite_name = lines[0]
            tle1 = lines[1]
            tle2 = lines[2]
            
            # Add line numbers if missing
            if not tle1.startswith('1 '):
                tle1 = '1 ' + tle1
            if not tle2.startswith('2 '):
                tle2 = '2 ' + tle2
            
            # Try to create TLE object to validate format
            try:
                TLE(tle1, tle2)
            except Exception as e:
                raise ValueError(f"Invalid TLE format: {str(e)}")
            
            return satellite_name, tle1, tle2
            
    except Exception as e:
        print(f"Error reading TLE file: {str(e)}")
        print("\nExpected TLE format:")
        print("Satellite Name")
        print("1 25544U 98067A   08264.51782528 -.00002182  00000-0 -11606-4 0  2927")
        print("2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.72125391563537")
        return None, None, None

def predict_from_tle(tle1_line1, tle1_line2, tle2_line1, tle2_line2, model_path='models/conjunction_model.pkl', date=None):
    """
    Make a prediction for a pair of TLEs at a specific date.
    """
    try:
        # Load model and scaler
        model = joblib.load(model_path)
        scaler = joblib.load(model_path.replace('.pkl', '_scaler.pkl'))
        
        # Extract features
        features = extract_features_from_tles(tle1_line1, tle1_line2, tle2_line1, tle2_line2)
        if features is None:
            return None, None, None
            
        # Scale features
        features_scaled = scaler.transform([features])
        
        # Make prediction
        pred = model.predict(features_scaled)[0]
        prob = model.predict_proba(features_scaled)[0][1]
        
        # Calculate minimum distance
        utc = TimeScalesFactory.getUTC()
        if date is None:
            date = datetime.utcnow()
        current_date = AbsoluteDate(date.year, date.month, date.day, 
                                  date.hour, date.minute, float(date.second), utc)
        
        tle1_obj = TLE(tle1_line1, tle1_line2)
        tle2_obj = TLE(tle2_line1, tle2_line2)
        min_dist, _ = propagate_and_find_closest(tle1_obj, tle2_obj, current_date)
        
        return pred, prob, min_dist
        
    except Exception as e:
        print(f"Error in prediction: {str(e)}")
        return None, None, None

def compare_with_tle_data(user_tle1, user_tle2, tle_data_file, model_path='models/conjunction_model.pkl'):
    """
    Compare user's TLE with all TLEs in the data file and save all predictions.
    """
    try:
        # Read TLE data
        df = pd.read_csv(tle_data_file)
        
        results = []
        total_satellites = len(df)
        print(f"\nComparing with {total_satellites} satellites in the database...")
        
        # Create user TLE object
        user_tle_obj = TLE(user_tle1, user_tle2)
        
        # Create progress bar
        with tqdm(total=total_satellites, desc="Processing satellites", unit="satellite") as pbar:
            for _, row in df.iterrows():
                other_tle1 = row['TLE1']
                other_tle2 = row['TLE2']
                
                # Create other TLE object
                other_tle_obj = TLE(other_tle1, other_tle2)
                
                # Get current time
                current_time = datetime.utcnow()
                
                # Make predictions for next 2 days
                time_points = []
                probabilities = []
                distances = []
                
                for hours in range(0, 49, 6):  # Every 6 hours for 2 days
                    check_time = current_time + timedelta(hours=hours)
                    pred, prob, min_dist = predict_from_tle(
                        user_tle1, user_tle2,
                        other_tle1, other_tle2,
                        model_path,
                        check_time
                    )
                    
                    if pred is not None:
                        time_points.append(check_time)
                        probabilities.append(prob)
                        distances.append(min_dist)
                
                if time_points:
                    # Find maximum probability and corresponding distance
                    max_prob_idx = np.argmax(probabilities)
                    results.append({
                        'Satellite': row['Name'],
                        'Max_Probability': max(probabilities),
                        'Time_of_Max_Probability': time_points[max_prob_idx],
                        'Distance_at_Max_Probability': distances[max_prob_idx],
                        'TLE1': other_tle1,
                        'TLE2': other_tle2
                    })
                
                # Update progress bar
                pbar.update(1)
        
        # Sort results by probability
        results.sort(key=lambda x: x['Max_Probability'], reverse=True)
        
        # Print results
        print("\nTop 5 Most Likely Conjunctions in Next 2 Days:")
        for idx, result in enumerate(results[:5], 1):
            print(f"{idx}. {result['Satellite']}")
            print(f"   Max Probability: {result['Max_Probability']:.3f}")
            print(f"   Time: {result['Time_of_Max_Probability']}")
            print(f"   Distance: {result['Distance_at_Max_Probability']:.2f} km")
        
        # Save all results to CSV
        results_df = pd.DataFrame(results)
        output_file = 'data/user_tle_predictions.csv'
        results_df.to_csv(output_file, index=False)
        print(f"\nAll predictions saved to {output_file}")
        
    except Exception as e:
        print(f"Error processing TLE data: {str(e)}")