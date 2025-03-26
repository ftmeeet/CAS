from sgp4.api import Satrec
from sgp4.api import WGS72
from datetime import datetime, timedelta
from numpy import radians
from sgp4.conveniences import sat_epoch_datetime

# Function to propagate TLE for a given number of days
def propagate_tle(tle_line1, tle_line2, days, step=60):
    """
    Propagates the TLE data for the given number of days.
    :param tle_line1: First line of TLE
    :param tle_line2: Second line of TLE
    :param days: Number of days to propagate
    :param step: Time step in seconds (default: 60 seconds)
    :return: List of propagated state vectors (time, x, y, z, vx, vy, vz)
    """
    satellite = Satrec.twoline2rv(tle_line1, tle_line2, WGS72)
    epoch = sat_epoch_datetime(satellite)
    
    propagated_data = []
    
    for t in range(0, days * 86400, step):  # Convert days to seconds
        propagation_time = epoch + timedelta(seconds=t)
        jd, fr = propagation_time.timetuple().tm_yday + 2451545, propagation_time.hour/24.0
        e, r, v = satellite.sgp4(jd, fr)
        
        if e == 0:  # Check for propagation errors
            propagated_data.append((propagation_time, *r, *v))
        else:
            print(f"Propagation error at time {propagation_time}")
    
    return propagated_data

# Example usage
if __name__ == "__main__":
    tle_line1 = "1 25544U 98067A   24085.54791667  .00001264  00000-0  32228-4 0  9991"
    tle_line2 = "2 25544  51.6441  37.4421 0005611  34.1196 326.0046 15.49819063501310"
    
    days = int(input("Enter the number of days to propagate: "))
    results = propagate_tle(tle_line1, tle_line2, days)
    
    print("Time (UTC), X (km), Y (km), Z (km), VX (km/s), VY (km/s), VZ (km/s)")
    for entry in results:
        print(entry)