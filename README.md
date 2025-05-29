# Satellite Conjunction Analysis and Visualization

This project provides a full-stack application for satellite conjunction analysis and visualization. It consists of a Python backend for conjunction analysis and a React frontend for 3D visualization using Cesium.

## Project Structure

```
.
├── app.py              # FastAPI backend server
├── main.py            # Main analysis script
├── requirements.txt   # Combined Python and Node.js dependencies
├── frontend/
│   └── src/
│       └── App.js
├── data/
└── models/
```

## Setup Instructions

1. Create a Python virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Install Node.js dependencies:
```bash
cd frontend
npm install
```

4. Start the backend server (in one terminal):
```bash
python app.py
```

5. Start the frontend development server (in another terminal):
```bash
cd frontend
npm start
```

The backend server will run on http://localhost:8000 and the frontend will run on http://localhost:3000

## Features

- Upload TLE data for user satellites
- Visualize satellites in 3D using Cesium
- Run conjunction analysis
- Real-time progress tracking
- Display analysis results

## API Endpoints

- `POST /api/upload-tle`: Upload TLE data for a satellite
- `POST /api/start-analysis`: Start conjunction analysis
- `GET /api/analysis-status`: Get current analysis status
- `GET /api/satellites`: Get list of all satellites

## Dependencies

All dependencies are listed in the root `requirements.txt` file, including:
- Python packages (FastAPI, Pandas, NumPy, Orekit, etc.)
- Node.js packages (React, Cesium, Material-UI, etc.) 