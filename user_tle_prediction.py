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
            
        # Create feature names array
        feature_names = [f'feature_{i}' for i in range(len(features))]
        
        # Convert to DataFrame with feature names
        features_df = pd.DataFrame([features], columns=feature_names)
        
        # Scale features
        features_scaled = scaler.transform(features_df)
        
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
        
    except Exception:
        return None, None, None

def compare_with_tle_data(user_tle1, user_tle2, tle_data_file, model_path='models/conjunction_model.pkl'):
    """
    Compare user's TLE with all TLEs in the data file and save all predictions.
    Uses distance thresholds based on training data to filter out distant satellites.
    """
    try:
        # Read TLE data
        df = pd.read_csv(tle_data_file)
        
        # Limit to first 100 satellites for testing
        df = df.head(100)
        
        # Create user TLE object
        user_tle_obj = TLE(user_tle1, user_tle2)
        
        results = []
        total_satellites = len(df)
        
        # Distance thresholds (in km) based on training data
        # These values are typical for conjunction events
        MIN_DISTANCE_THRESHOLD = 100  # Minimum distance to consider
        MAX_DISTANCE_THRESHOLD = 1000  # Maximum distance to consider
        
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
                    try:
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
                    except Exception:
                        continue
                
                # Add result even if no probabilities (mark as not potential conjunction)
                if not probabilities:
                    result = {
                        'Satellite1': user_tle_obj.getSatelliteNumber(),
                        'Satellite2': row['Name'],
                        'Max_Probability': 0.0,
                        'Time_of_Max_Probability': current_time,
                        'Distance_at_Max_Probability': float('inf'),
                        'All_Probabilities': '[]',
                        'All_Times': '[]',
                        'All_Distances': '[]',
                        'Potential_Conjunction': False
                    }
                else:
                    # Check if this is a potential conjunction
                    is_potential = any(p > 0.5 for p in probabilities) and any(d <= MAX_DISTANCE_THRESHOLD for d in distances)
                    
                    result = {
                        'Satellite1': user_tle_obj.getSatelliteNumber(),
                        'Satellite2': row['Name'],
                        'Max_Probability': max(probabilities),
                        'Time_of_Max_Probability': time_points[np.argmax(probabilities)],
                        'Distance_at_Max_Probability': distances[np.argmax(probabilities)],
                        'All_Probabilities': str(probabilities),
                        'All_Times': str(time_points),
                        'All_Distances': str(distances),
                        'Potential_Conjunction': is_potential
                    }
                
                results.append(result)
                pbar.update(1)
        
        # Sort results by probability
        results.sort(key=lambda x: x['Max_Probability'], reverse=True)
        
        # Convert results to DataFrame
        results_df = pd.DataFrame(results)
        
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        # Save to CSV with proper formatting
        output_file = 'data/user_tle_predictions_test.csv'  # Changed filename for test run
        results_df.to_csv(output_file, index=False, float_format='%.6f')
        
        # Print summary statistics
        print(f"\nResults saved to {output_file}")
        print(f"Total satellites processed: {total_satellites}")
        print(f"Satellites with potential conjunctions: {sum(1 for r in results if r['Potential_Conjunction'])}")
        
        # Print top 5 potential conjunctions
        potential_results = [r for r in results if r['Potential_Conjunction']]
        if potential_results:
            print("\nTop 5 potential conjunctions:")
            for i, result in enumerate(potential_results[:5]):
                print(f"{i+1}. {result['Satellite1']} - {result['Satellite2']}")
                print(f"   Max Probability: {result['Max_Probability']:.6f}")
                print(f"   Time: {result['Time_of_Max_Probability']}")
                print(f"   Distance: {result['Distance_at_Max_Probability']:.2f} km")
        
    except Exception as e:
        print(f"Error processing TLE data: {str(e)}")
        raise