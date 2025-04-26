import os
import math
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import orekit
from orekit.pyhelpers import setup_orekit_curdir
from org.orekit.frames import FramesFactory
from org.orekit.propagation.analytical.tle import TLEPropagator, TLE

# Initialize Orekit
orekit.initVM()
setup_orekit_curdir(from_pip_library=True)

def calculate_earth_rotation_angle(time_str):
    """
    Calculate the Earth rotation angle (ERA) in degrees for a given UTC time.
    
    Args:
        time_str: UTC time string in format 'YYYY-MM-DD HH:MM:SS'
        
    Returns:
        float: Earth rotation angle in degrees
    """
    # Parse the time string into a datetime object
    time_utc = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
    
    # Calculate the hour decimal
    hour_decimal = time_utc.hour + time_utc.minute/60 + time_utc.second/3600
    
    # Calculate the day of the year
    day_of_year = time_utc.timetuple().tm_yday
    
    # Calculate the ERA using the formula from IERS Technical Note 36
    # ERA = 2π(0.7790572732640 + 1.00273781191135448 * (day_of_year + hour_decimal/24))
    era_radians = 2 * math.pi * (0.7790572732640 + 1.00273781191135448 * (day_of_year + hour_decimal/24))
    
    # Convert to degrees
    era_degrees = math.degrees(era_radians)
    
    # Normalize to [0, 360)
    era_degrees = era_degrees % 360
    
    return era_degrees

def plot_orbit(results, satellite_name):
    """
    Plot the satellite orbit in 3D.
    
    Args:
        results: List of tuples containing (time, x, y, z, vx, vy, vz)
        satellite_name: Name of the satellite
    """
    # Extract position data
    times = [r[0] for r in results]
    x_pos = [r[1] for r in results]
    y_pos = [r[2] for r in results]
    z_pos = [r[3] for r in results]
    
    # Create figure
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    # Plot orbit
    ax.plot(x_pos, y_pos, z_pos, 'b-', label='Orbit')
    
    # Plot Earth
    earth_radius = 6371  # km
    u = np.linspace(0, 2 * np.pi, 100)
    v = np.linspace(0, np.pi, 100)
    x = earth_radius * np.outer(np.cos(u), np.sin(v))
    y = earth_radius * np.outer(np.sin(u), np.sin(v))
    z = earth_radius * np.outer(np.ones(np.size(u)), np.cos(v))
    ax.plot_surface(x, y, z, color='lightblue', alpha=0.3)
    
    # Set labels and title
    ax.set_xlabel('X (km)')
    ax.set_ylabel('Y (km)')
    ax.set_zlabel('Z (km)')
    ax.set_title(f'Orbit of {satellite_name}')
    
    # Set equal aspect ratio
    ax.set_box_aspect([1, 1, 1])
    
    # Add legend
    ax.legend()
    
    # Show plot
    plt.tight_layout()
    plt.show()

def propagate_tle_orekit(tle_line1, tle_line2, days, step=10):  # Using 6-hour step for accuracy
    """
    Propagates the TLE using Orekit's SGP4 propagator and converts to TEME of Date.
    :param tle_line1: First line of TLE
    :param tle_line2: Second line of TLE
    :param days: Number of days to propagate
    :param step: Time step in seconds (default: 6 hours)
    :return: List of propagated state vectors (time, x, y, z, vx, vy, vz)
    """
    tle = TLE(tle_line1, tle_line2)
    propagator = TLEPropagator.selectExtrapolator(tle)  # Uses SGP4 or SDP4 based on orbital period
    epoch = tle.getDate()
    
    print(f"Epoch from TLE: {epoch}")  # Debugging step

    propagated_data = []
       
    for t in range(0, days * 86400 + 1, step):
        propagation_time = epoch.shiftedBy(float(t))
        state = propagator.propagate(propagation_time)
        pv = state.getPVCoordinates(FramesFactory.getTEME())  # State vector in TEME frame
        
        position = pv.getPosition()
        velocity = pv.getVelocity()
        
        propagated_data.append((
            propagation_time.toString(), 
            position.getX() / 1000.0, position.getY() / 1000.0, position.getZ() / 1000.0,  # Convert meters to km
            velocity.getX() / 1000.0, velocity.getY() / 1000.0, velocity.getZ() / 1000.0   # Convert m/s to km/s
        ))

    return propagated_data

# Example usage
if __name__ == "__main__":
    tle_line1 = "1 00005U 58002B   00179.78495062  .00000023  00000-0  28098-4 0  9994"
    tle_line2 = "2 00005 034.2682 348.7242 1859667 331.7664 019.3264 10.82419157413667"
    
    days = int(input("Enter the number of days to propagate: "))
    results = propagate_tle_orekit(tle_line1, tle_line2, days)
    
    print("Time (UTC), X (km), Y (km), Z (km), VX (km/s), VY (km/s), VZ (km/s)")
    for entry in results:
        print(entry)
    
    # Plot the orbit
    plot_orbit(results, "Satellite 00005")