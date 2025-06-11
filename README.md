# Collision Avoidance System (CAS)

A real-time satellite tracking and conjunction analysis system that helps monitor and predict potential collisions between satellites and space debris.

## Project Structure

```
CAS/
├── data/              # Data files
├── models/            # ML models
├── scripts/           # Utility scripts
├── tests/             # Test files
└── frontend/          # Frontend application
```

## Features

- Real-time satellite tracking
- Conjunction analysis
- Collision probability calculation
- 3D visualization using Cesium
- Time-based simulation controls
- Satellite filtering and search
- Risk assessment and alerts

## Prerequisites

- Python 3.8+
- Node.js 14+
- npm or yarn
- Cesium ion account (for 3D visualization)

## Setup

### Backend Setup

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Start the backend server:
```bash
python main.py
```

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

## Usage

### Time Controls
- Use the time control panel to adjust simulation speed
- Default speed is 2x
- Maximum speed is 50x
- Current time and date are displayed

### Satellite Visualization
- View satellites in 3D space
- Filter satellites by various parameters
- Search for specific satellites
- Toggle different visualization layers

### Conjunction Analysis
- Run conjunction analysis to detect potential collisions
- View detailed conjunction reports
- Filter conjunctions by risk level
- Get real-time updates on high-risk conjunctions

## API Endpoints

- `GET /api/satellites` - Get list of satellites
- `GET /api/conjunctions` - Get conjunction analysis results
- `POST /api/analysis/start` - Start conjunction analysis
- `POST /api/analysis/stop` - Stop conjunction analysis
- `GET /api/analysis/status` - Get analysis status

## Troubleshooting

1. If the 3D visualization doesn't load:
   - Check your Cesium ion token
   - Ensure you have a stable internet connection
   - Clear your browser cache

2. If the backend fails to start:
   - Check if all dependencies are installed
   - Verify Python version (3.8+ required)
   - Check if required ports are available

3. If the frontend fails to build:
   - Clear node_modules and reinstall
   - Check Node.js version (14+ required)
   - Verify all environment variables

## Development

### Backend Development
- Follow PEP 8 style guide
- Write unit tests for new features
- Update requirements.txt when adding dependencies

### Frontend Development
- Follow ESLint configuration
- Use SCSS modules for styling
- Maintain component structure
- Update documentation for new features

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[Add your license here] 