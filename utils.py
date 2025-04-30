import numpy as np
import orekit
from orekit.pyhelpers import setup_orekit_curdir
from org.orekit.frames import FramesFactory
from org.orekit.time import AbsoluteDate, TimeScalesFactory
from org.orekit.propagation.analytical.tle import TLE, TLEPropagator
from org.hipparchus.geometry.euclidean.threed import Vector3D
from org.orekit.orbits import KeplerianOrbit
import datetime
import math

# Initialize VM once
orekit.initVM()
setup_orekit_curdir(from_pip_library=True)

def create_propagator(tle_line1, tle_line2):
    tle = TLE(tle_line1, tle_line2)
    return TLEPropagator.selectExtrapolator(tle)

def extract_features_from_tles(tle1_line1, tle1_line2, tle2_line1, tle2_line2):
    """
    Extract essential features from two TLEs for conjunction prediction.
    Returns a list of features in the same order as the training data.
    """
    try:
        # Create Orekit TLE objects
        tle1 = TLE(tle1_line1, tle1_line2)
        tle2 = TLE(tle2_line1, tle2_line2)
        
        # Get current time
        utc = TimeScalesFactory.getUTC()
        now = datetime.datetime.utcnow()
        current_date = AbsoluteDate(now.year, now.month, now.day, 
                                  now.hour, now.minute, float(now.second), utc)
        
        # Create propagators
        propagator1 = TLEPropagator.selectExtrapolator(tle1)
        propagator2 = TLEPropagator.selectExtrapolator(tle2)
        
        # Propagate to current time
        state1 = propagator1.propagate(current_date)
        state2 = propagator2.propagate(current_date)
        
        # Convert to Keplerian orbits
        orbit1 = KeplerianOrbit(state1.getPVCoordinates(), FramesFactory.getTEME(), current_date, state1.getMu())
        orbit2 = KeplerianOrbit(state2.getPVCoordinates(), FramesFactory.getTEME(), current_date, state2.getMu())
        
        # Extract basic orbital elements
        a1 = orbit1.getA() / 1000.0  # Convert to km
        e1 = orbit1.getE()
        i1 = np.degrees(orbit1.getI())
        raan1 = np.degrees(orbit1.getRightAscensionOfAscendingNode())
        pa1 = np.degrees(orbit1.getPerigeeArgument())
        ma1 = np.degrees(orbit1.getMeanAnomaly())
        
        a2 = orbit2.getA() / 1000.0
        e2 = orbit2.getE()
        i2 = np.degrees(orbit2.getI())
        raan2 = np.degrees(orbit2.getRightAscensionOfAscendingNode())
        pa2 = np.degrees(orbit2.getPerigeeArgument())
        ma2 = np.degrees(orbit2.getMeanAnomaly())
        
        # Calculate relative orbital elements
        da = abs(a1 - a2)
        de = abs(e1 - e2)
        di = abs(i1 - i2)
        draan = abs(raan1 - raan2)
        dpa = abs(pa1 - pa2)
        dma = abs(ma1 - ma2)
        
        # Get position and velocity vectors
        pv1 = state1.getPVCoordinates(FramesFactory.getTEME())
        pv2 = state2.getPVCoordinates(FramesFactory.getTEME())
        
        # Convert to numpy arrays
        r1 = np.array([pv1.getPosition().getX(), pv1.getPosition().getY(), pv1.getPosition().getZ()])
        v1 = np.array([pv1.getVelocity().getX(), pv1.getVelocity().getY(), pv1.getVelocity().getZ()])
        r2 = np.array([pv2.getPosition().getX(), pv2.getPosition().getY(), pv2.getPosition().getZ()])
        v2 = np.array([pv2.getVelocity().getX(), pv2.getVelocity().getY(), pv2.getVelocity().getZ()])
        
        # Calculate relative position and velocity
        r_rel = r2 - r1
        v_rel = v2 - v1
        
        # Calculate distances and speeds
        miss_distance = np.linalg.norm(r_rel) / 1000.0  # Convert to km
        relative_speed = np.linalg.norm(v_rel) / 1000.0  # Convert to km/s
        
        # Create feature array with 102 features
        features = np.zeros(102)
        
        # Basic orbital elements (12)
        features[0] = a1
        features[1] = e1
        features[2] = i1
        features[3] = raan1
        features[4] = pa1
        features[5] = ma1
        features[6] = a2
        features[7] = e2
        features[8] = i2
        features[9] = raan2
        features[10] = pa2
        features[11] = ma2
        
        # Relative orbital elements (6)
        features[12] = da
        features[13] = de
        features[14] = di
        features[15] = draan
        features[16] = dpa
        features[17] = dma
        
        # Position and velocity components (6)
        features[18] = r_rel[0] / 1000.0  # Convert to km
        features[19] = r_rel[1] / 1000.0
        features[20] = r_rel[2] / 1000.0
        features[21] = v_rel[0] / 1000.0  # Convert to km/s
        features[22] = v_rel[1] / 1000.0
        features[23] = v_rel[2] / 1000.0
        
        # Distance and speed (2)
        features[24] = miss_distance
        features[25] = relative_speed
        
        return features
        
    except Exception:
        return None

def extract_features(tle1, tle2):
    features = []
    features.append(abs(tle1.getMeanMotion() - tle2.getMeanMotion()))
    features.append(abs(tle1.getE() - tle2.getE()))
    features.append(abs(tle1.getI() - tle2.getI()))
    features.append(abs(tle1.getRaan() - tle2.getRaan()))
    features.append(abs(tle1.getPerigeeArgument() - tle2.getPerigeeArgument()))
    features.append(abs(tle1.getMeanAnomaly() - tle2.getMeanAnomaly()))
    return features

def are_orbits_close(tle1, tle2, sma_thresh_km=100, inc_thresh_deg=5):
    utc = TimeScalesFactory.getUTC()
    now = datetime.datetime.utcnow()
    date = AbsoluteDate(now.year, now.month, now.day, now.hour, now.minute, float(now.second), utc)
    propagator1 = TLEPropagator.selectExtrapolator(tle1)
    propagator2 = TLEPropagator.selectExtrapolator(tle2)
    state1 = propagator1.propagate(date)
    state2 = propagator2.propagate(date)
    sma1 = state1.getOrbit().getA()  # in meters
    sma2 = state2.getOrbit().getA()  # in meters
    inc1 = tle1.getI()
    inc2 = tle2.getI()

    if abs(sma1 - sma2) > sma_thresh_km * 1000:
        return False
    if abs(np.degrees(inc1) - np.degrees(inc2)) > inc_thresh_deg:
        return False
    return True

def propagate_and_find_closest(tle1, tle2, start_date, duration_sec=86400, coarse_step=600, fine_step=60, threshold_km=10):
    """
    Propagate two satellites and find their closest approach.
    
    Args:
        tle1 (TLE): First satellite TLE
        tle2 (TLE): Second satellite TLE
        start_date (AbsoluteDate): Start date for propagation
        duration_sec (int): Duration to propagate in seconds
        coarse_step (int): Coarse search step in seconds
        fine_step (int): Fine search step in seconds
        threshold_km (float): Distance threshold for fine search
        
    Returns:
        tuple: (minimum distance in km, time of closest approach)
    """
    try:
        propagator1 = create_propagator(tle1.getLine1(), tle1.getLine2())
        propagator2 = create_propagator(tle2.getLine1(), tle2.getLine2())

        min_dist = float('inf')
        best_time = None

        for t in range(0, duration_sec, coarse_step):
            date = start_date.shiftedBy(float(t))

            pv1 = propagator1.propagate(date).getPVCoordinates(FramesFactory.getTEME())
            pv2 = propagator2.propagate(date).getPVCoordinates(FramesFactory.getTEME())

            dist = Vector3D.distance(pv1.getPosition(), pv2.getPosition()) / 1000.0

            if dist < threshold_km and dist < min_dist:
                # Fine search
                for dt in range(-coarse_step//2, coarse_step//2, fine_step):
                    fine_date = date.shiftedBy(float(dt))
                    pv1f = propagator1.propagate(fine_date).getPVCoordinates(FramesFactory.getTEME())
                    pv2f = propagator2.propagate(fine_date).getPVCoordinates(FramesFactory.getTEME())
                    fine_dist = Vector3D.distance(pv1f.getPosition(), pv2f.getPosition()) / 1000.0

                    if fine_dist < min_dist:
                        min_dist = fine_dist
                        best_time = fine_date

        return min_dist, best_time
        
    except Exception:
        return float('inf'), None

def is_tle_recent(tle, max_age_days=20):
    """
    Returns True if the TLE epoch is within max_age_days of now.
    """
    utc = TimeScalesFactory.getUTC()
    now = datetime.datetime.utcnow()
    now_abs = AbsoluteDate(now.year, now.month, now.day, now.hour, now.minute, float(now.second), utc)
    tle_epoch = tle.getDate()
    age_days = now_abs.durationFrom(tle_epoch) / 86400.0  # durationFrom returns seconds
    return abs(age_days) <= max_age_days

def perigee_apogee_overlap(tle1, tle2, dth_km=100):
    # Get perigee/apogee for both TLEs (in km)
    orbit1 = TLEPropagator.selectExtrapolator(tle1).propagate(tle1.getDate()).getOrbit()
    orbit2 = TLEPropagator.selectExtrapolator(tle2).propagate(tle2.getDate()).getOrbit()
    perigee1 = (orbit1.getA() * (1 - orbit1.getE())) / 1000
    apogee1  = (orbit1.getA() * (1 + orbit1.getE())) / 1000
    perigee2 = (orbit2.getA() * (1 - orbit2.getE())) / 1000
    apogee2  = (orbit2.getA() * (1 + orbit2.getE())) / 1000

    # Expand ranges by Dth
    min1, max1 = perigee1 - dth_km, apogee1 + dth_km
    min2, max2 = perigee2 - dth_km, apogee2 + dth_km

    # Check for overlap
    return max(min1, min2) <= min(max1, max2)
