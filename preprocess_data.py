import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib

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
        print(f"Removed {len(df) - len(df_clean)} rows with missing values")
        
        # Separate features and target
        X = df_clean[feature_columns]
        y = df_clean['conjunction']
        
        print("\nSplitting data into train and test sets...")
        # Split the data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        print("Scaling features...")
        # Scale the features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Save the processed data
        processed_data_path = data_path.replace('.csv', '_processed.csv')
        df_clean.to_csv(processed_data_path, index=False)
        print(f"\nProcessed data saved to {processed_data_path}")
        
        # Print data statistics
        print("\nData Statistics:")
        print(f"Total samples: {len(df)}")
        print(f"Clean samples: {len(df_clean)}")
        print(f"Training samples: {len(X_train)}")
        print(f"Test samples: {len(X_test)}")
        print(f"Conjunction cases: {y.sum()} ({y.mean()*100:.2f}%)")
        
        return X_train_scaled, X_test_scaled, y_train, y_test, scaler
        
    except Exception as e:
        print(f"\nError during data preprocessing: {e}")
        print("\nPlease check your data file format. The data should contain:")
        print("1. At least one distance-related column (containing 'distance' or 'range' in the name)")
        print("2. Numeric columns for features")
        print("3. No missing values in the numeric columns")
        return None

if __name__ == "__main__":
    preprocess_data() 