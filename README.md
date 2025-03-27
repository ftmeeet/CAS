# CAS (Collision Avoidance System)

A Python-based tool for satellite collision prediction and avoidance using the SGP4 algorithm with realistic 3D Earth rendering and orbit visualization.

## Features

- Automatic satellite database updating from CelesTrak
- Interactive satellite selection from thousands of objects
- Search functionality for finding specific satellites
- High-resolution 3D Earth visualization with texture mapping
- Bilinear interpolation for smooth Earth texture rendering
- Detailed orbit propagation using SGP4 algorithm
- Static 3D orbit visualization
- Animated orbit visualization with time-synced Earth rotation
- Orbit characteristics calculation (altitude, eccentricity)
- Collision risk assessment between satellite orbits

## Requirements

- Python 3.x
- sgp4
- numpy
- matplotlib
- pandas
- requests

## Installation

1. Clone the repository:
```bash
git clone https://github.com/ftmeeet/CAS.git
cd CAS
```

2. Install the required packages:
```bash
pip install sgp4 numpy matplotlib pandas requests
```

3. Download an Earth texture image (earth_texture.jpg) and place it in the project directory.

## Usage

Run the main script:
```bash
python Main.py
```

The script will:
1. Automatically check for and update the satellite database if needed
2. Present a list of available satellites
3. Allow you to search for specific satellites by name
4. Calculate orbit propagation for your selected satellite
5. Provide visualization options:
   - Static 3D orbit plot
   - Animated orbit visualization

## Visualization Options

### Static 3D Orbit Plot
- Displays the complete orbital path 
- Shows start and end points with timestamps
- Indicates portions of orbit behind Earth with dashed lines
- Includes orbit statistics (min/max altitude, eccentricity)

### Animated Orbit
- Dynamic satellite position tracking
- Earth rotation synchronized with timestamps
- Satellite trail visualization
- Real-time altitude and time display

## Data Sources

Satellite TLE data is automatically fetched from CelesTrak (https://celestrak.org/) and includes:
- Active satellites
- Debris objects

The database is automatically updated when running the program if the data is older than 24 hours.

## License

This project is open source and available under the MIT License. 