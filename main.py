import os
from train_model import train_and_save_model
from user_tle_prediction import read_user_tle, compare_with_tle_data

def main():
    print("TLE Conjunction Prediction System")
    print("================================")
    
    # Create necessary directories
    os.makedirs('data', exist_ok=True)
    os.makedirs('models', exist_ok=True)
    
    # Check if model exists, if not train it
    model_path = 'models/conjunction_model.pkl'
    if not os.path.exists(model_path):
        print("Training model...")
        train_and_save_model('data/raw_data.csv', model_path)
        print("Model training completed!")
    
    # Read TLE from file
    satellite_name, user_tle1, user_tle2 = read_user_tle()
    if satellite_name is None:
        print("Error: Could not read TLE from data/user_tle.txt")
        return
    
    print(f"Using TLE for satellite: {satellite_name}")
    
    # Paths
    tle_data_file = 'data/tle_data.csv'
    model_path = 'models/conjunction_model.pkl'
    
    # Check if required files exist
    if not os.path.exists(tle_data_file):
        print(f"Error: TLE data file not found at {tle_data_file}")
        return
    if not os.path.exists(model_path):
        print(f"Error: Model file not found at {model_path}")
        return
    
    # Compare with TLE data
    compare_with_tle_data(user_tle1, user_tle2, tle_data_file, model_path)

if __name__ == "__main__":
    main() 