# CAS (Celestial Analysis System)

A Python-based tool for satellite orbit propagation using SGP4 algorithm.

## Features

- TLE (Two-Line Element Set) propagation
- State vector calculation (position and velocity)
- Configurable time steps and propagation duration
- Error checking during propagation

## Requirements

- Python 3.x
- sgp4
- numpy

## Installation

1. Clone the repository:
```bash
git clone https://github.com/ftmeeet/CAS.git
cd CAS
```

2. Install the required packages:
```bash
pip install sgp4 numpy
```

## Usage

Run the main script:
```bash
python Main.py
```

The script will prompt you to enter the number of days to propagate the satellite's orbit. It will then output the propagated state vectors (position and velocity) at regular time intervals.

## Output Format

The output includes:
- Time (UTC)
- Position (X, Y, Z in kilometers)
- Velocity (VX, VY, VZ in kilometers per second)

## License

This project is open source and available under the MIT License. 