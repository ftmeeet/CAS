import orekit
from orekit.pyhelpers import setup_orekit_curdir
from org.orekit.propagation.analytical.tle import TLE, TLEPropagator
from org.orekit.time import AbsoluteDate, TimeScalesFactory
from org.orekit.utils import PVCoordinates
from org.orekit.frames import FramesFactory
from datetime import datetime, timedelta
from org.orekit.bodies import OneAxisEllipsoid
from org.orekit.utils import IERSConventions

# Initialize Orekit VM
orekit.initVM()
setup_orekit_curdir(from_pip_library=True)


def propagate_tle_orekit(tle_line1, tle_line2, days, step=1):  # Using 60-sec step for accuracy
    """
    Propagates the TLE using Orekit's SGP4 propagator and converts to TEME of Date.
    :param tle_line1: First line of TLE
    :param tle_line2: Second line of TLE
    :param days: Number of days to propagate
    :param step: Time step in seconds (default: 60 seconds)
    :return: List of propagated state vectors (time, x, y, z, vx, vy, vz)
    """
    tle = TLE(tle_line1, tle_line2)
    propagator = TLEPropagator.selectExtrapolator(tle)  # Uses SGP4 or SDP4 based on orbital period
    epoch = tle.getDate()
    
    print(f"Epoch from TLE: {epoch}")  # Debugging step

    propagated_data = []
    
    # Define the ITRF frame for transformations (used to handle Earth's rotation)
    itrf_frame = FramesFactory.getITRF(IERSConventions.IERS_2010, False)
    
    for t in range(0, days * 86400, step):
        propagation_time = epoch.shiftedBy(float(t))
        state = propagator.propagate(propagation_time)
        pv = state.getPVCoordinates(FramesFactory.getTEME())  # State vector in TEME of Epoch
        
        # Convert the state vector to TEME of Date (by transforming to ITRF and then to TEME)
        teme_of_date_transform = FramesFactory.getTEME().getTransformTo(itrf_frame, propagation_time)
        pv_teme_date = teme_of_date_transform.transformPVCoordinates(pv)  # Transform to TEME of Date
        
        position = pv_teme_date.getPosition()
        velocity = pv_teme_date.getVelocity()
        
        propagated_data.append((
            propagation_time.toString(), 
            position.getX() / 1000.0, position.getY() / 1000.0, position.getZ() / 1000.0,  # Convert meters to km
            velocity.getX() / 1000.0, velocity.getY() / 1000.0, velocity.getZ() / 1000.0   # Convert m/s to km/s
        ))
    
    return propagated_data

# Example usage
if __name__ == "__main__":
    tle_line1 = "1 00005U 58002B   00179.78495062 +.00000023 +00000-0 +28098-4 0  9994"
    tle_line2 = "2 00005  034.2682 348.7242 1859667 331.7664 019.3264 10.82419157413667"
    
    days = int(input("Enter the number of days to propagate: "))
    results = propagate_tle_orekit(tle_line1, tle_line2, days)
    
    print("Time (UTC), X (km), Y (km), Z (km), VX (km/s), VY (km/s), VZ (km/s)")
    for entry in results:
        print(entry)
