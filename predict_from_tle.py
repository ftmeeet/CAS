import pandas as pd
import numpy as np
import joblib
from utils import (
    extract_features_from_tles,
    propagate_and_find_closest,
    calculate_relative_velocity_components,
    calculate_time_to_closest_approach,
    calculate_collision_probability,
    calculate_miss_distance
)
import os
from tqdm import tqdm
import warnings
from org.orekit.time import TimeScalesFactory, AbsoluteDate
from org.orekit.frames import FramesFactory
from org.orekit.propagation.analytical.tle import TLEPropagator, TLE
from org.hipparchus.geometry.euclidean.threed import Vector3D
import datetime

# Suppress all warnings
warnings.filterwarnings('ignore')

def distance_to_probability(distance_km, threshold_km=10, steepness=0.5):
    """
    Convert distance to probability using a sigmoid function.
    Closer distances have higher probability of conjunction.
    
    Args:
        distance_km (float): Distance in kilometers
        threshold_km (float): Distance threshold for conjunction
        steepness (float): Controls how quickly probability changes with distance
        
    Returns:
        float: Probability between 0 and 1
    """
    # Sigmoid function centered at threshold
    # Higher steepness means sharper transition
    return 1 / (1 + np.exp(steepness * (distance_km - threshold_km)))

def predict_from_tle(tle1, tle2, model_path='models/conjunction_model.pkl', threshold_km=10):
    """
    Calculate actual distance between two satellites using Orekit and get model prediction.
    Propagates over 2 days to find potential conjunctions.
    
    Args:
        tle1 (str): First TLE (both lines combined with newline)
        tle2 (str): Second TLE (both lines combined with newline)
        model_path (str): Path to the trained model
        threshold_km (float): Distance threshold in kilometers for conjunction detection
        
    Returns:
        tuple: (prediction, distance_km, risk_value, collision_probability, conjunction_time, relative_velocity_km_s)
    """
    try:
        # Split TLEs into separate lines
        tle1_lines = tle1.strip().split('\n')
        tle2_lines = tle2.strip().split('\n')
        
        if len(tle1_lines) != 2 or len(tle2_lines) != 2:
            return None, None, None, None, None, None
            
        # Load model and scaler
        model = joblib.load(model_path)
        scaler = joblib.load(model_path.replace('.pkl', '_scaler.pkl'))
        
        # Create TLE objects
        tle1_obj = TLE(tle1_lines[0], tle1_lines[1])
        tle2_obj = TLE(tle2_lines[0], tle2_lines[1])
        
        # Get current time
        utc = TimeScalesFactory.getUTC()
        now = datetime.datetime.utcnow()
        current_date = AbsoluteDate(now.year, now.month, now.day, 
                                  now.hour, now.minute, float(now.second), utc)
        
        # Propagate over 2 days (172800 seconds) with coarse step of 1 hour (3600 seconds)
        # If a potential conjunction is found, use fine step of 1 minute (60 seconds)
        min_dist, conjunction_time, relative_velocity_km_s = propagate_and_find_closest(
            tle1_obj, tle2_obj, current_date,
            duration_sec=172800,  # 2 days
            coarse_step=3600,     # 1 hour
            fine_step=60,         # 1 minute
            threshold_km=threshold_km
        )
        
        # If no conjunction found, return early
        if min_dist == float('inf'):
            return 0, min_dist, 0.0, 0.0, None, None
            
        # Propagate to conjunction time for detailed analysis
        propagator1 = TLEPropagator.selectExtrapolator(tle1_obj)
        propagator2 = TLEPropagator.selectExtrapolator(tle2_obj)
        
        pv1 = propagator1.propagate(conjunction_time).getPVCoordinates(FramesFactory.getTEME())
        pv2 = propagator2.propagate(conjunction_time).getPVCoordinates(FramesFactory.getTEME())
        
        # Calculate relative velocity components in RTN frame
        v_radial, v_transverse, v_normal = calculate_relative_velocity_components(pv1, pv2)
        
        # Calculate time to closest approach
        time_to_closest = calculate_time_to_closest_approach(pv1, pv2)
        if time_to_closest is None:
            # If objects are stationary relative to each other, use current distance
            time_to_closest = 0.0
        
        # Extract orbital parameters
        t_sma = tle1_obj.getMeanMotion()  # Semi-major axis
        t_ecc = tle1_obj.getE()  # Eccentricity
        t_inc = tle1_obj.getI()  # Inclination
        
        c_sma = tle2_obj.getMeanMotion()  # Semi-major axis
        c_ecc = tle2_obj.getE()  # Eccentricity
        c_inc = tle2_obj.getI()  # Inclination
        
        # Calculate apogee and perigee heights
        t_h_apo = t_sma * (1 + t_ecc) - 6378.137  # Earth radius in km
        t_h_per = t_sma * (1 - t_ecc) - 6378.137
        c_h_apo = c_sma * (1 + c_ecc) - 6378.137
        c_h_per = c_sma * (1 - c_ecc) - 6378.137
        
        # Get relative position components
        r_rel = pv2.getPosition().subtract(pv1.getPosition())
        r_rel_x = r_rel.getX() / 1000.0  # Convert to km
        r_rel_y = r_rel.getY() / 1000.0
        r_rel_z = r_rel.getZ() / 1000.0
        
        # Create feature vector with exactly 18 features
        features = np.array([
            # Distance and velocity features (6)
            min_dist, relative_velocity_km_s,
            v_radial, v_transverse, v_normal,
            time_to_closest,
            
            # Relative position components (3)
            r_rel_x, r_rel_y, r_rel_z,
            
            # Target orbital elements (3)
            t_sma, t_ecc, t_inc,
            
            # Chaser orbital elements (3)
            c_sma, c_ecc, c_inc,
            
            # Height features (3)
            t_h_apo, t_h_per, c_h_apo
        ]).reshape(1, -1)
        
        # Scale features
        features_scaled = scaler.transform(features)
        
        # Get model prediction (risk value)
        risk_value = model.predict(features_scaled)[0]
        
        # Calculate collision probability using the new function
        collision_probability = calculate_collision_probability(
            min_dist, relative_velocity_km_s, threshold_km, risk_value
        )
        
        # Convert to binary prediction based on threshold
        pred = 1 if min_dist < threshold_km else 0
        
        return pred, min_dist, risk_value, collision_probability, conjunction_time, relative_velocity_km_s
        
    except Exception as e:
        print(f"Error in prediction: {e}")
        return None, None, None, None, None, None

def process_tle_file(user_tle_file='data/user_tle.csv', tle_data_file='data/tle_data.csv', model_path='models/conjunction_model.pkl', threshold_km=10):
    """
    Process TLE pairs between user satellites and database satellites.
    
    Args:
        user_tle_file (str): Path to the user's TLE file (format: Name,TLE1,TLE2)
        tle_data_file (str): Path to the TLE database file (format: Name,TLE1,TLE2)
        model_path (str): Path to the trained model
        threshold_km (float): Distance threshold in kilometers for conjunction detection
    """
    try:
        # Ensure threshold_km is a float
        threshold_km = float(threshold_km)
        
        # Check if model exists
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at {model_path}")
            
        # Read user TLE data
        user_df = pd.read_csv(user_tle_file)
        # Read database TLE data
        db_df = pd.read_csv(tle_data_file)
        
        # Create output directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        # Process all pairs
        results = []
        total_pairs = len(user_df) * len(db_df)
        
        print(f"Processing {total_pairs} pairs...")
        with tqdm(total=total_pairs, desc="Processing satellite pairs", unit="pair") as pbar:
            for i in range(len(user_df)):
                for j in range(len(db_df)):
                    tle1 = f"{user_df.iloc[i]['TLE1']}\n{user_df.iloc[i]['TLE2']}"
                    tle2 = f"{db_df.iloc[j]['TLE1']}\n{db_df.iloc[j]['TLE2']}"
                    
                    pred, actual_distance, risk_value, probability, conjunction_time, relative_velocity = predict_from_tle(
                        tle1, tle2, model_path, threshold_km
                    )
                    
                    if pred is not None and actual_distance is not None and risk_value is not None:
                        results.append({
                            'User_Satellite': str(user_df.iloc[i]['Name']),
                            'Database_Satellite': str(db_df.iloc[j]['Name']),
                            'Prediction': int(pred),
                            'Actual_Distance_km': float(actual_distance),
                            'Risk_Value': float(risk_value),
                            'Collision_Probability': float(probability),
                            'Risk_Level': 'High' if probability > 0.7 else 'Medium' if probability > 0.3 else 'Low',
                            'Conjunction_Time': conjunction_time.toString() if conjunction_time else None,
                            'Relative_Velocity_km_s': float(relative_velocity) if relative_velocity is not None else None
                        })
                    
                    pbar.update(1)
        
        # Save results to CSV
        results_df = pd.DataFrame(results)
        output_file = 'data/predictions.csv'
        results_df.to_csv(output_file, index=False)
        
        print(f"\nPredictions saved to {output_file}")
        print(f"Total pairs processed: {total_pairs}")
        print(f"Successful predictions: {len(results)}")
        
        # Print summary statistics
        if len(results) > 0:
            print("\nDistance Summary:")
            print(f"Number of potential conjunctions (distance < {threshold_km}km): {sum(r['Prediction'] for r in results)}")
            print(f"Average actual distance: {sum(r['Actual_Distance_km'] for r in results)/len(results):.2f} km")
            print(f"Minimum actual distance: {min(r['Actual_Distance_km'] for r in results):.2f} km")
            print(f"Maximum actual distance: {max(r['Actual_Distance_km'] for r in results):.2f} km")
            
            # Calculate velocity statistics only for non-None values
            valid_velocities = [r['Relative_Velocity_km_s'] for r in results if r['Relative_Velocity_km_s'] is not None]
            if valid_velocities:
                print("\nVelocity Summary:")
                print(f"Average relative velocity: {sum(valid_velocities)/len(valid_velocities):.2f} km/s")
                print(f"Maximum relative velocity: {max(valid_velocities):.2f} km/s")
            
            print("\nRisk Summary:")
            print(f"Average risk value: {sum(r['Risk_Value'] for r in results)/len(results):.4f}")
            print(f"Average collision probability: {sum(r['Collision_Probability'] for r in results)/len(results):.2%}")
            print(f"High risk pairs: {sum(1 for r in results if r['Risk_Level'] == 'High')}")
            print(f"Medium risk pairs: {sum(1 for r in results if r['Risk_Level'] == 'Medium')}")
            print(f"Low risk pairs: {sum(1 for r in results if r['Risk_Level'] == 'Low')}")
            
            # Print details of potential conjunctions
            conjunctions = [r for r in results if r['Prediction'] == 1]
            if conjunctions:
                print("\nPotential Conjunctions:")
                for conj in conjunctions:
                    print(f"{conj['User_Satellite']} - {conj['Database_Satellite']}:")
                    print(f"  Actual Distance: {conj['Actual_Distance_km']:.2f} km")
                    if conj['Relative_Velocity_km_s'] is not None:
                        print(f"  Relative Velocity: {conj['Relative_Velocity_km_s']:.2f} km/s")
                    print(f"  Risk Value: {conj['Risk_Value']:.4f}")
                    print(f"  Collision Probability: {conj['Collision_Probability']:.2%}")
                    print(f"  Risk Level: {conj['Risk_Level']}")
                    if conj['Conjunction_Time']:
                        print(f"  Conjunction Time: {conj['Conjunction_Time']}")
        
    except Exception as e:
        print(f"Error processing TLE files: {e}")
        raise  # Re-raise the exception to see the full traceback

if __name__ == "__main__":
    process_tle_file('data/user_tle.csv', 'data/tle_data.csv', threshold_km=10) 