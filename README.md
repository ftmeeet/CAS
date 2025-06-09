# Satellite Conjunction Analysis and Visualization

A full-stack application for satellite conjunction analysis and visualization, featuring a Python backend for conjunction analysis and a React frontend for 3D visualization using Cesium.

## Features

- Real-time 3D visualization of satellites using Cesium
- Automatic TLE data updates and conversion
- Conjunction analysis with collision probability calculation
- Time control for simulation speed (up to 50x)
- Interactive satellite selection and tracking
- High-risk conjunction highlighting
- Space weather data integration
- Machine learning-based conjunction prediction

## Prerequisites

- Python 3.8 or higher
- Node.js 14 or higher
- npm or yarn
- Git

## Project Structure

```
.
├── main.py              # FastAPI backend server and analysis logic
├── fetch_tle.py         # TLE data fetching and processing
├── convert_tle.py       # TLE data conversion to JS format
├── train_model.py       # ML model training for conjunction prediction
├── predict_from_tle.py  # Conjunction prediction using trained model
├── space_weather.py     # Space weather data integration
├── requirements.txt     # Python dependencies
├── data/               # Data storage directory
│   ├── tle_data.csv    # TLE data
│   ├── predictions.csv # Analysis results
│   └── user_tle.csv    # User-provided TLE data
├── models/             # ML models directory
│   └── conjunction_model.pkl
└── satellite-tracker/  # Frontend application
    ├── package.json
    ├── public/
    └── src/
        └── components/
            └── satellites/
                ├── CesiumView/      # 3D visualization
                ├── TimeControls/    # Time simulation controls
                ├── AnalysisControls/# Analysis controls
                └── ConjunctionView/ # Conjunction results display
```

## Setup Instructions

### Backend Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Create and activate a Python virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Start the backend server:
```bash
python main.py
```

The backend server will:
- Start on http://localhost:8000
- Automatically fetch and update TLE data
- Convert TLE data to JS format for the frontend
- Train the conjunction prediction model if needed
- Update space weather data

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd satellite-tracker
```

2. Install Node.js dependencies:
```bash
npm install
# or
yarn install
```

3. Start the frontend development server:
```bash
npm start
# or
yarn start
```

The frontend will start on http://localhost:3000

## Usage Guide

### Time Controls
- Use the slider in the top right corner to control simulation speed
- Speed range: 0x (paused) to 50x
- Default speed: 2x
- Click the stop button to pause the simulation

### Satellite Visualization
- Left-click on a satellite to select and track it
- The selected satellite's orbit path will be displayed
- Use mouse to rotate, zoom, and pan the view
- Right-click to reset the camera

### Conjunction Analysis
1. Click "Start Analysis" to begin conjunction analysis
2. Monitor progress in the analysis controls
3. View results in the conjunction panel
4. High-risk conjunctions are highlighted in red
5. Click "Stop Analysis" to cancel the analysis

### Analysis Results
- Conjunctions are color-coded by risk level:
  - Red: High risk (>70% collision probability)
  - Orange: Medium risk (30-70% collision probability)
  - Green: Low risk (<30% collision probability)
- Each conjunction shows:
  - Satellite pair
  - Distance
  - Collision probability
  - Conjunction time
  - Relative velocity

## API Endpoints

### Analysis
- `POST /api/start-analysis`: Start conjunction analysis
- `POST /api/stop-analysis`: Stop running analysis
- `GET /api/analysis-status`: Get current analysis status

### Data
- `GET /api/conjunctions`: Get conjunction analysis results
- `GET /api/satellites`: Get list of all satellites

## Development

### Backend Development
- The backend uses FastAPI for the web server
- Conjunction analysis runs asynchronously
- TLE data is automatically updated every 24 hours
- ML model is retrained every 7 days

### Frontend Development
- Built with React and Cesium
- Uses CSS modules for styling
- Components are organized by feature
- State management with React hooks

## Troubleshooting

### Common Issues
1. Backend fails to start:
   - Check if port 8000 is available
   - Verify Python version and dependencies
   - Check data directory permissions

2. Frontend fails to start:
   - Check if port 3000 is available
   - Verify Node.js version
   - Clear npm cache if needed

3. Analysis fails:
   - Check TLE data freshness
   - Verify model file exists
   - Check disk space

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[Your License Here] 