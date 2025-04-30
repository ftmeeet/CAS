import os
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from tqdm import tqdm

def preprocess_data(data_path):
    """
    Preprocess the raw data for training.
    
    Args:
        data_path (str): Path to the raw data file
        
    Returns:
        tuple: (X_train, X_test, y_train, y_test, scaler)
    """
    try:
        print(f"Reading data from {data_path}...")
        # Read the data
        df = pd.read_csv(data_path)
        
        # Print data info
        print("\nData Info:")
        print(f"Number of rows: {len(df)}")
        print(f"Number of columns: {len(df.columns)}")
        print("\nFirst few rows of data:")
        print(df.head())
        
        # Check for distance-related columns
        distance_columns = [col for col in df.columns if 'distance' in col.lower() or 'range' in col.lower()]
        if not distance_columns:
            raise ValueError("No distance-related columns found in the data.")
        
        print("\nFound distance-related columns:", distance_columns)
        
        # Use the first distance column found
        distance_col = distance_columns[0]
        print(f"\nUsing '{distance_col}' for conjunction detection")
        
        # Create label based on distance (1 if < 10km, 0 otherwise)
        print("\nCreating labels based on distance...")
        df['conjunction'] = (df[distance_col] < 10000).astype(int)  # Converting meters to km
        
        # Find numeric columns for features
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        feature_columns = [col for col in numeric_columns if col != 'conjunction']
        
        print("\nUsing the following numeric columns as features:")
        print(feature_columns)
        
        print("\nRemoving rows with missing values...")
        # Remove rows with missing values
        df_clean = df.dropna(subset=feature_columns + ['conjunction'])
        
        # Prepare features and target
        X = df_clean[feature_columns]
        y = df_clean['conjunction']
        
        # Split the data
        print("\nSplitting data into train and test sets...")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale the features
        print("\nScaling features...")
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        return X_train_scaled, X_test_scaled, y_train, y_test, scaler
        
    except Exception as e:
        print(f"Error during data preprocessing: {e}")
        return None

def train_and_save_model(data_path='data/raw_data.csv', model_path='models/conjunction_model.pkl'):
    """
    Train the model and save it for future use.
    
    Args:
        data_path (str): Path to the training data
        model_path (str): Path to save the trained model
    """
    try:
        print("Starting data preprocessing...")
        preprocessed_data = preprocess_data(data_path)
        if preprocessed_data is None:
            return False
            
        X_train, X_test, y_train, y_test, scaler = preprocessed_data
        
        print("\nStarting model training...")
        # Initialize and train the model
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight='balanced'
        )
        
        model.fit(X_train, y_train)
        
        # Evaluate the model
        y_pred = model.predict(X_test)
        print("\nModel Evaluation:")
        print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred))
        
        # Create models directory if it doesn't exist
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        
        # Save the model and scaler
        joblib.dump(model, model_path)
        joblib.dump(scaler, model_path.replace('.pkl', '_scaler.pkl'))
        
        print(f"\nModel saved to {model_path}")
        print(f"Scaler saved to {model_path.replace('.pkl', '_scaler.pkl')}")
        
        return True
        
    except Exception as e:
        print(f"Error during model training: {e}")
        return False

if __name__ == "__main__":
    train_and_save_model()