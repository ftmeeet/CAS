import pandas as pd
import numpy as np
import joblib
from utils import extract_features_from_tles
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
    
    Args:
        tle1 (str): First TLE (both lines combined with newline)
        tle2 (str): Second TLE (both lines combined with newline)
        model_path (str): Path to the trained model
        threshold_km (float): Distance threshold in kilometers for conjunction detection
        
    Returns:
        tuple: (prediction, distance_km, risk_value, collision_probability)
    """
    try:
        # Split TLEs into separate lines
        tle1_lines = tle1.strip().split('\n')
        tle2_lines = tle2.strip().split('\n')
        
        if len(tle1_lines) != 2 or len(tle2_lines) != 2:
            return None, None, None, None
            
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
        
        # Propagate to current time
        propagator1 = TLEPropagator.selectExtrapolator(tle1_obj)
        propagator2 = TLEPropagator.selectExtrapolator(tle2_obj)
        
        pv1 = propagator1.propagate(current_date).getPVCoordinates(FramesFactory.getTEME())
        pv2 = propagator2.propagate(current_date).getPVCoordinates(FramesFactory.getTEME())
        
        # Calculate actual distance and relative velocity
        pos1 = pv1.getPosition()
        pos2 = pv2.getPosition()
        vel1 = pv1.getVelocity()
        vel2 = pv2.getVelocity()
        
        # Calculate relative position and velocity
        rel_pos = pos2.subtract(pos1)
        rel_vel = vel2.subtract(vel1)
        
        # Calculate distance and speed
        distance_m = Vector3D.distance(pos1, pos2)
        distance_km = distance_m / 1000.0
        relative_speed = Vector3D.distance(rel_vel, Vector3D.ZERO)
        
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
        
        # Create feature vector
        features = np.array([
            distance_km, relative_speed,
            rel_pos.getX(), rel_pos.getY(), rel_pos.getZ(),
            rel_vel.getX(), rel_vel.getY(), rel_vel.getZ(),
            t_sma, t_ecc, t_inc,
            c_sma, c_ecc, c_inc,
            t_h_apo, t_h_per, c_h_apo, c_h_per
        ]).reshape(1, -1)
        
        # Scale features
        features_scaled = scaler.transform(features)
        
        # Get model prediction (risk value)
        risk_value = model.predict(features_scaled)[0]
        
        # Convert risk value to normalized collision probability (0 to 1)
        # Using a combination of distance-based probability and risk value
        # Distance-based probability decreases exponentially with distance
        distance_prob = np.exp(-distance_km / threshold_km)
        
        # Risk-based probability from model
        risk_prob = 1 / (1 + np.exp(risk_value))
        
        # Combined probability (weighted average)
        # Give more weight to distance when it's large
        if distance_km > threshold_km:
            weight = 0.8  # More weight to distance
        else:
            weight = 0.5  # Equal weight
            
        collision_probability = weight * distance_prob + (1 - weight) * risk_prob
        
        # Ensure probability is between 0 and 1
        collision_probability = max(0.0, min(1.0, collision_probability))
        
        # Convert to binary prediction based on threshold
        pred = 1 if distance_km < threshold_km else 0
        
        return pred, distance_km, risk_value, collision_probability
        
    except Exception as e:
        print(f"Error in prediction: {e}")
        return None, None, None, None

def process_tle_file(tle_file, model_path='models/conjunction_model.pkl', max_pairs=50, threshold_km=10):
    """
    Process TLE pairs from a CSV file and calculate actual distances and collision probabilities.
    
    Args:
        tle_file (str): Path to the TLE data file
        model_path (str): Path to the trained model
        max_pairs (int): Maximum number of pairs to process
        threshold_km (float): Distance threshold in kilometers for conjunction detection
    """
    try:
        # Ensure max_pairs is an integer
        max_pairs = int(max_pairs)
        threshold_km = float(threshold_km)
        
        # Check if model exists
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at {model_path}")
            
        # Read TLE data
        df = pd.read_csv(tle_file)
        
        # Create output directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        # Process pairs up to max_pairs
        results = []
        total_pairs = min(max_pairs, len(df) * (len(df) - 1) // 2)
        
        print(f"Processing first {total_pairs} pairs...")
        with tqdm(total=total_pairs, desc="Processing satellite pairs", unit="pair") as pbar:
            pair_count = 0
            for i in range(len(df)):
                for j in range(i + 1, len(df)):
                    if pair_count >= max_pairs:
                        break
                        
                    tle1 = f"{df.iloc[i]['TLE1']}\n{df.iloc[i]['TLE2']}"
                    tle2 = f"{df.iloc[j]['TLE1']}\n{df.iloc[j]['TLE2']}"
                    
                    pred, actual_distance, risk_value, probability = predict_from_tle(
                        tle1, tle2, model_path, threshold_km
                    )
                    
                    if pred is not None and actual_distance is not None and risk_value is not None:
                        results.append({
                            'Satellite1': str(df.iloc[i]['Name']),
                            'Satellite2': str(df.iloc[j]['Name']),
                            'Prediction': int(pred),
                            'Actual_Distance_km': float(actual_distance),
                            'Risk_Value': float(risk_value),
                            'Collision_Probability': float(probability),
                            'Risk_Level': 'High' if probability > 0.7 else 'Medium' if probability > 0.3 else 'Low'
                        })
                    
                    pair_count += 1
                    pbar.update(1)
                
                if pair_count >= max_pairs:
                    break
        
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
                    print(f"{conj['Satellite1']} - {conj['Satellite2']}:")
                    print(f"  Actual Distance: {conj['Actual_Distance_km']:.2f} km")
                    print(f"  Risk Value: {conj['Risk_Value']:.4f}")
                    print(f"  Collision Probability: {conj['Collision_Probability']:.2%}")
                    print(f"  Risk Level: {conj['Risk_Level']}")
        
    except Exception as e:
        print(f"Error processing TLE file: {e}")
        raise  # Re-raise the exception to see the full traceback

if __name__ == "__main__":
    process_tle_file('data/tle_data.csv', max_pairs=50, threshold_km=10) 