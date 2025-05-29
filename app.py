from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os
import json
from datetime import datetime
import pandas as pd
from typing import List, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Import the main analysis functions
from main import main as run_analysis
from predict_from_tle import process_tle_file

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables to store analysis state
analysis_status = {
    "is_running": False,
    "progress": 0,
    "results": None,
    "error": None
}

class TLEData(BaseModel):
    name: str
    tle1: str
    tle2: str

class AnalysisResponse(BaseModel):
    status: str
    progress: float
    results: Optional[dict] = None
    error: Optional[str] = None

def run_analysis_task():
    global analysis_status
    try:
        analysis_status["is_running"] = True
        analysis_status["progress"] = 0
        analysis_status["error"] = None
        
        # Run the main analysis
        run_analysis()
        
        # Process TLE file and get results
        results = process_tle_file(
            user_tle_file='data/user_tle.csv',
            tle_data_file='data/tle_data.csv',
            model_path='models/conjunction_model.pkl',
            threshold_km=100
        )
        
        analysis_status["results"] = results
        analysis_status["progress"] = 100
    except Exception as e:
        analysis_status["error"] = str(e)
    finally:
        analysis_status["is_running"] = False

@app.post("/api/start-analysis")
async def start_analysis(background_tasks: BackgroundTasks):
    if analysis_status["is_running"]:
        raise HTTPException(status_code=400, detail="Analysis is already running")
    
    background_tasks.add_task(run_analysis_task)
    return {"status": "Analysis started"}

@app.get("/api/analysis-status")
async def get_analysis_status():
    return analysis_status

@app.post("/api/upload-tle")
async def upload_tle(tle_data: TLEData):
    try:
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        # Save TLE data to CSV
        df = pd.DataFrame([{
            'Name': tle_data.name,
            'TLE1': tle_data.tle1,
            'TLE2': tle_data.tle2
        }])
        
        df.to_csv('data/user_tle.csv', index=False)
        return {"status": "TLE data uploaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/satellites")
async def get_satellites():
    try:
        # Read TLE data
        tle_df = pd.read_csv('data/tle_data.csv')
        user_tle_df = pd.read_csv('data/user_tle.csv')
        
        # Combine both datasets
        all_satellites = pd.concat([tle_df, user_tle_df])
        
        # Convert to list of dictionaries
        satellites = all_satellites.to_dict('records')
        return {"satellites": satellites}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 