# Conjunction Analysis System (CAS)

A system for analyzing potential satellite conjunctions using Two-Line Element (TLE) data and machine learning.

## Features

- TLE data processing and validation
- Satellite conjunction prediction
- Machine learning-based risk assessment
- Distance and probability calculations
- Progress tracking and detailed reporting

## Requirements

- Python 3.8+
- Required packages:
  - pandas
  - numpy
  - scikit-learn
  - joblib
  - tqdm
  - orekit
  - hipparchus

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/CAS.git
cd CAS
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Prepare your TLE data:
   - Place your satellite TLEs in `data/user_tle.csv` (format: Name,TLE1,TLE2)
   - Ensure `data/tle_data.csv` contains the database of satellites to compare against

2. Run the analysis:
```bash
python main.py
```

The script will:
- Check TLE data freshness
- Check model freshness
- Compare your satellites with the database
- Generate predictions and save them to `data/predictions.csv`

## File Structure

```
CAS/
├── data/                   # Data directory (ignored by git)
│   ├── user_tle.csv       # User's satellite TLEs
│   ├── tle_data.csv       # Database of satellite TLEs
│   └── predictions.csv    # Generated predictions
├── models/                 # Trained models
│   ├── conjunction_model.pkl
│   └── conjunction_model_scaler.pkl
├── main.py                # Main script
├── predict_from_tle.py    # Prediction functions
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Output

The system generates:
- Distance measurements between satellites
- Risk assessments
- Collision probabilities
- Detailed reports of potential conjunctions

## Notes

- TLE data should be updated regularly (less than 24 hours old)
- Models are retrained weekly
- Data files are ignored by git to keep repository size manageable
- Models are included in the repository for reproducibility

## License

This project is licensed under the MIT License - see the LICENSE file for details. 