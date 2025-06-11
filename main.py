import os
import pandas as pd
from datetime import datetime, timedelta
from fetch_tle import fetch_and_save_tle_data
from train_model import train_and_save_model
from predict_from_tle import process_tle_file
import warnings
from space_weather import get_latest_space_weather_data
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import json
from typing import List, Dict
import asyncio
import signal
import sys
from convert_tle import convert_csv_to_js
import multiprocessing
from multiprocessing import Process, Event

# Suppress all warnings
warnings.filterwarnings('ignore')

app = FastAPI()

# Update CORS middleware with more specific configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your frontend URL
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Global variables to track analysis status
analysis_status = {
    "is_running": False,
    "progress": 0,
    "message": "",
    "should_stop": False
}

# Global variable to store the current analysis process
current_analysis_process = None
stop_event = None

def restart_server():
    """Restart the server by spawning a new process and exiting the current one"""
    python = sys.executable
    os.execl(python, python, *sys.argv)

def run_tle_processing(stop_event, analysis_status):
    """Run TLE processing in a separate process"""
    try:
        process_tle_file(
            'data/user_tle.csv',
            'data/tle_data.csv',
            'models/conjunction_model.pkl',
            100,
            analysis_status
        )
    except Exception as e:
        print(f"Error in TLE processing: {e}")
    finally:
        stop_event.set()

async def run_conjunction_analysis():
    """Background task to run conjunction analysis"""
    global analysis_status, current_analysis_process, stop_event
    try:
        analysis_status["is_running"] = True
        analysis_status["progress"] = 0
        analysis_status["message"] = "Starting analysis..."
        analysis_status["should_stop"] = False
        await asyncio.sleep(0.1)  # Allow initial status to be processed

        # Check and update TLE data if needed
        if analysis_status["should_stop"]:
            raise Exception("Analysis stopped by user")
            
        analysis_status["message"] = "Checking TLE data..."
        analysis_status["progress"] = 10
        await asyncio.sleep(0.1)
        
        if not check_tle_freshness():
            if analysis_status["should_stop"]:
                raise Exception("Analysis stopped by user")
                
            analysis_status["message"] = "Updating TLE data..."
            analysis_status["progress"] = 5
            await asyncio.sleep(0.1)
            fetch_and_save_tle_data()
            analysis_status["progress"] = 10
            await asyncio.sleep(0.1)

        # Check and retrain model if needed
        if analysis_status["should_stop"]:
            raise Exception("Analysis stopped by user")
            
        analysis_status["message"] = "Checking model..."
        analysis_status["progress"] = 15
        await asyncio.sleep(0.1)
        
        if not check_model_freshness():
            if analysis_status["should_stop"]:
                raise Exception("Analysis stopped by user")
                
            analysis_status["message"] = "Training model..."
            analysis_status["progress"] = 18
            await asyncio.sleep(0.1)
            train_and_save_model()
            analysis_status["progress"] = 20
            await asyncio.sleep(0.1)

        # Update space weather data
        if analysis_status["should_stop"]:
            raise Exception("Analysis stopped by user")
            
        analysis_status["message"] = "Updating space weather data..."
        analysis_status["progress"] = 25
        await asyncio.sleep(0.1)
        get_latest_space_weather_data()
        analysis_status["progress"] = 30
        await asyncio.sleep(0.1)

        # Process TLE file
        if analysis_status["should_stop"]:
            raise Exception("Analysis stopped by user")
            
        analysis_status["message"] = "Processing TLE data..."
        analysis_status["progress"] = 30
        await asyncio.sleep(0.1)
        
        # Create a stop event for the process
        stop_event = Event()
        
        # Start TLE processing in a separate process
        current_analysis_process = Process(
            target=run_tle_processing,
            args=(stop_event, analysis_status)
        )
        current_analysis_process.start()
        
        # Wait for the process to complete or be stopped
        while current_analysis_process.is_alive():
            if analysis_status["should_stop"]:
                stop_event.set()
                current_analysis_process.terminate()
                current_analysis_process.join()
                raise Exception("Analysis stopped by user")
            await asyncio.sleep(0.1)
        
        if not analysis_status["should_stop"]:
            analysis_status["progress"] = 100
            analysis_status["message"] = "Analysis complete!"
            await asyncio.sleep(0.1)

    except asyncio.CancelledError:
        analysis_status["message"] = "Analysis cancelled"
        analysis_status["progress"] = 0
        raise
    except Exception as e:
        if "stopped by user" in str(e):
            analysis_status["message"] = "Analysis stopped by user"
        else:
            analysis_status["message"] = f"Error: {str(e)}"
        analysis_status["progress"] = 0
        raise
    finally:
        if current_analysis_process and current_analysis_process.is_alive():
            current_analysis_process.terminate()
            current_analysis_process.join()
        analysis_status["is_running"] = False
        analysis_status["should_stop"] = False
        current_analysis_process = None
        stop_event = None
        await asyncio.sleep(0.1)  # Allow final status to be processed

@app.post("/api/start-analysis")
async def start_analysis(background_tasks: BackgroundTasks):
    """Start conjunction analysis"""
    global current_analysis_process
    
    if analysis_status["is_running"]:
        raise HTTPException(status_code=400, detail="Analysis already running")
    
    # Create and store the task
    current_analysis_task = asyncio.create_task(run_conjunction_analysis())
    return {"message": "Analysis started"}

@app.post("/api/stop-analysis")
async def stop_analysis():
    """Stop the running conjunction analysis and restart the server"""
    global current_analysis_process, analysis_status, stop_event
    
    if not analysis_status["is_running"]:
        raise HTTPException(status_code=400, detail="No analysis is currently running")
    
    # Set the stop flag
    analysis_status["should_stop"] = True
    
    # Signal the process to stop if it exists
    if stop_event:
        stop_event.set()
    
    # Terminate the process if it's still running
    if current_analysis_process and current_analysis_process.is_alive():
        current_analysis_process.terminate()
        current_analysis_process.join()
    
    # Reset analysis status
    analysis_status = {
        "is_running": False,
        "progress": 0,
        "message": "Analysis stopped by user",
        "should_stop": False
    }
    
    # Schedule server restart
    asyncio.create_task(asyncio.sleep(1))  # Give time for response to be sent
    restart_server()
    
    return {"message": "Analysis stopped and server restarting..."}

@app.get("/api/analysis-status")
async def get_analysis_status():
    """Get current analysis status"""
    return {
        "is_running": analysis_status["is_running"],
        "progress": analysis_status["progress"],
        "message": analysis_status["message"]
    }

@app.get("/api/conjunctions")
async def get_conjunctions():
    """
    Get conjunction data for visualization
    """
    try:
        # Read predictions file
        predictions_df = pd.read_csv('data/predictions.csv')
        
        # Convert to list of dictionaries
        conjunctions = []
        for _, row in predictions_df.iterrows():
            if row['prediction'] == 1:  # Only include actual conjunctions
                conjunction = {
                    'satellite1': row['satellite1'],
                    'satellite2': row['satellite2'],
                    'distance_km': float(row['distance_km']),
                    'conjunction_time': row['conjunction_time'],
                    'collision_probability': float(row['collision_probability']),
                    'relative_velocity_km_s': float(row['relative_velocity_km_s'])
                }
                conjunctions.append(conjunction)
        
        return conjunctions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analysis-results")
async def get_analysis_results():
    """Get the results of the last analysis"""
    try:
        # Read the predictions file
        results_file = 'data/predictions.csv'
        
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        if not os.path.exists(results_file):
            # Return empty results instead of 404
            return {
                "total_pairs": 0,
                "successful_predictions": 0,
                "threshold_km": 100,
                "potential_conjunctions": 0,
                "avg_distance": 0,
                "min_distance": 0,
                "max_distance": 0,
                "avg_velocity": 0,
                "max_velocity": 0,
                "avg_risk": 0,
                "avg_probability": 0,
                "high_risk_pairs": 0,
                "medium_risk_pairs": 0,
                "low_risk_pairs": 0,
                "conjunctions": []
            }
            
        df = pd.read_csv(results_file)
        
        # Calculate summary statistics
        total_pairs = len(df)
        successful_predictions = len(df)
        potential_conjunctions = sum(df['Prediction'])
        
        # Distance statistics
        avg_distance = df['Actual_Distance_km'].mean()
        min_distance = df['Actual_Distance_km'].min()
        max_distance = df['Actual_Distance_km'].max()
        
        # Velocity statistics
        valid_velocities = df['Relative_Velocity_km_s'].dropna()
        avg_velocity = valid_velocities.mean() if not valid_velocities.empty else 0
        max_velocity = valid_velocities.max() if not valid_velocities.empty else 0
        
        # Risk statistics
        avg_risk = df['Risk_Value'].mean()
        avg_probability = df['Collision_Probability'].mean()
        high_risk_pairs = sum(df['Risk_Level'] == 'High')
        medium_risk_pairs = sum(df['Risk_Level'] == 'Medium')
        low_risk_pairs = sum(df['Risk_Level'] == 'Low')
        
        # Get potential conjunctions
        conjunctions = df[df['Prediction'] == 1].to_dict('records')
        
        return {
            "total_pairs": total_pairs,
            "successful_predictions": successful_predictions,
            "threshold_km": 100,  # This should match the threshold used in process_tle_file
            "potential_conjunctions": potential_conjunctions,
            "avg_distance": avg_distance,
            "min_distance": min_distance,
            "max_distance": max_distance,
            "avg_velocity": avg_velocity,
            "max_velocity": max_velocity,
            "avg_risk": avg_risk,
            "avg_probability": avg_probability,
            "high_risk_pairs": high_risk_pairs,
            "medium_risk_pairs": medium_risk_pairs,
            "low_risk_pairs": low_risk_pairs,
            "conjunctions": conjunctions
        }
        
    except Exception as e:
        print(f"Error in get_analysis_results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def check_tle_freshness(tle_file='data/tle_data.csv', max_age_hours=24):
    """
    Check if TLE data is fresh enough.
    
    Args:
        tle_file (str): Path to the TLE data file
        max_age_hours (int): Maximum age in hours before data is considered stale
        
    Returns:
        bool: True if data is fresh, False otherwise
    """
    if not os.path.exists(tle_file):
        return False
        
    file_time = datetime.fromtimestamp(os.path.getmtime(tle_file))
    age_hours = (datetime.now() - file_time).total_seconds() / 3600
    
    return age_hours <= max_age_hours

def check_model_freshness(model_file='models/conjunction_model.pkl', max_age_days=7):
    """
    Check if the model is fresh enough.
    
    Args:
        model_file (str): Path to the model file
        max_age_days (int): Maximum age in days before model is considered stale
        
    Returns:
        bool: True if model is fresh, False otherwise
    """
    if not os.path.exists(model_file):
        return False
        
    file_time = datetime.fromtimestamp(os.path.getmtime(model_file))
    age_days = (datetime.now() - file_time).days
    
    return age_days <= max_age_days

if __name__ == "__main__":
    import uvicorn
    print("Starting CAS backend server...")
    print("Server will be available at http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)