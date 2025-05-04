import os
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from preprocess_data import preprocess_data
from tqdm import tqdm
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from utils import extract_features_from_tles

def train_and_save_model(data_path='data/raw_data.csv', model_path='models/conjunction_model.pkl'):
    """
    Train a Random Forest Regressor model and save it to disk.
    
    Args:
        data_file (str): Path to the training data file
        model_path (str): Path to save the trained model
    """
    try:
        # Load training data
        df = pd.read_csv(data_path)
        
        # Define features and target
        features = [
            # Distance and velocity features
            'miss_distance', 'relative_speed',
            'relative_position_r', 'relative_position_t', 'relative_position_n',
            'relative_velocity_r', 'relative_velocity_t', 'relative_velocity_n',
            
            # Target orbital elements
            't_j2k_sma', 't_j2k_ecc', 't_j2k_inc',
            
            # Chaser orbital elements
            'c_j2k_sma', 'c_j2k_ecc', 'c_j2k_inc',
            
            # Height features
            't_h_apo', 't_h_per', 'c_h_apo', 'c_h_per',
            
            # Space weather features
            'F10', 'F3M', 'SSN', 'AP'
        ]
        
        # Convert to numpy arrays
        X = df[features].values
        y = df['risk'].values  # Use risk column as target variable
        
        # Split the data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Scale the features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train the model
        model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42
        )
        
        model.fit(X_train_scaled, y_train)
        
        # Make predictions
        y_pred = model.predict(X_test_scaled)
        
        # Calculate metrics
        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        print("\nModel Performance:")
        print(f"Mean Squared Error: {mse:.4f}")
        print(f"Root Mean Squared Error: {rmse:.4f}")
        print(f"Mean Absolute Error: {mae:.4f}")
        print(f"R-squared Score: {r2:.4f}")
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        
        # Save the model and scaler
        joblib.dump(model, model_path)
        joblib.dump(scaler, model_path.replace('.pkl', '_scaler.pkl'))
        
        print(f"\nModel saved to {model_path}")
        print(f"Scaler saved to {model_path.replace('.pkl', '_scaler.pkl')}")
        
    except Exception as e:
        print(f"Error in model training: {e}")
        raise

if __name__ == "__main__":
    # Create necessary directories
    os.makedirs('data', exist_ok=True)
    os.makedirs('models', exist_ok=True)
    
    # Train and save the model
    train_and_save_model()