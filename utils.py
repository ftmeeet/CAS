import numpy as np
import orekit
from orekit.pyhelpers import setup_orekit_curdir
from org.orekit.frames import FramesFactory
from org.orekit.time import AbsoluteDate, TimeScalesFactory
from org.orekit.propagation.analytical.tle import TLE, TLEPropagator
from org.hipparchus.geometry.euclidean.threed import Vector3D
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
    Extract features from two TLEs that match the training data format using Orekit.
    Returns a list of 26 features in the same order as the training data.
    """
    try:
        # Create Orekit TLE objects and propagators
        tle1 = TLE(tle1_line1, tle1_line2)
        tle2 = TLE(tle2_line1, tle2_line2)
        propagator1 = TLEPropagator.selectExtrapolator(tle1)
        propagator2 = TLEPropagator.selectExtrapolator(tle2)
        
        # Get current time
        utc = TimeScalesFactory.getUTC()
        now = datetime.datetime.utcnow()
        current_date = AbsoluteDate(now.year, now.month, now.day, 
                                  now.hour, now.minute, float(now.second), utc)
        
        # Find closest approach
        min_dist, best_time = propagate_and_find_closest(tle1, tle2, current_date)
        
        # Propagate to current time
        state1 = propagator1.propagate(current_date)
        state2 = propagator2.propagate(current_date)
        
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
        
        # Get orbital elements from Orekit
        orbit1 = state1.getOrbit()
        orbit2 = state2.getOrbit()
        
        # Extract orbital elements
        a1 = orbit1.getA() / 1000.0  # Convert to km
        e1 = orbit1.getE()
        i1 = np.degrees(orbit1.getI())
        
        a2 = orbit2.getA() / 1000.0  # Convert to km
        e2 = orbit2.getE()
        i2 = np.degrees(orbit2.getI())
        
        # Calculate miss distance and relative speed
        miss_distance = np.linalg.norm(r_rel) / 1000.0  # Convert to km
        relative_speed = np.linalg.norm(v_rel) / 1000.0  # Convert to km/s
        
        # Calculate RTN components
        def calculate_rtn(r, v):
            r_mag = np.linalg.norm(r)
            v_mag = np.linalg.norm(v)
            
            # Radial unit vector
            r_hat = r / r_mag
            
            # Transverse unit vector
            h = np.cross(r, v)
            h_hat = h / np.linalg.norm(h)
            t_hat = np.cross(h_hat, r_hat)
            
            # Normal unit vector
            n_hat = h_hat
            
            return r_hat, t_hat, n_hat
        
        r_hat, t_hat, n_hat = calculate_rtn(r1, v1)
        
        # Project relative position and velocity onto RTN
        r_rel_r = np.dot(r_rel, r_hat)
        r_rel_t = np.dot(r_rel, t_hat)
        r_rel_n = np.dot(r_rel, n_hat)
        
        v_rel_r = np.dot(v_rel, r_hat)
        v_rel_t = np.dot(v_rel, t_hat)
        v_rel_n = np.dot(v_rel, n_hat)
        
        # Calculate geocentric latitude and azimuth
        r_earth = np.array([r1[0], r1[1], 0])
        r_earth_mag = np.linalg.norm(r_earth)
        geocentric_lat = np.degrees(np.arcsin(r1[2]/np.linalg.norm(r1)))
        
        v_horiz = np.array([v_rel[0], v_rel[1], 0])
        azimuth = np.degrees(np.arctan2(v_horiz[1], v_horiz[0]))
        
        # Return exactly 26 features in the same order as training data
        return [
            # Time and risk features (4)
            1.0,  # time_to_tca
            0.0,  # risk
            0.0,  # max_risk_estimate
            1.0,  # max_risk_scaling
            
            # Position and velocity features (6)
            miss_distance * 1000,  # convert to meters
            relative_speed * 1000,  # convert to m/s
            r_rel_r,  # already in meters
            r_rel_t,
            r_rel_n,
            v_rel_r,  # already in m/s
            
            # Target orbital elements (3)
            a1, e1, i1,
            
            # Chaser orbital elements (3)
            a2, e2, i2,
            
            # Geometry features (2)
            geocentric_lat, azimuth,
            
            # Space weather features (4)
            100,  # F10
            100,  # F3M
            50,   # SSN
            5,    # AP
            
            # Covariance features (4)
            100,  # sigma_r
            100,  # sigma_t
            100,  # sigma_n
            0.1   # sigma_rdot
        ]
        
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
    Propagate two TLEs and find their closest approach.
    
    Args:
        tle1: First TLE
        tle2: Second TLE
        start_date: Start date for propagation
        duration_sec: Duration to propagate in seconds
        coarse_step: Coarse search step in seconds
        fine_step: Fine search step in seconds
        threshold_km: Distance threshold for fine search
        
    Returns:
        tuple: (minimum distance in km, time of closest approach, relative velocity in km/s)
    """
    try:
        # Get the epoch times of both TLEs
        epoch1 = tle1.getDate()
        epoch2 = tle2.getDate()
        
        # Use the most recent epoch as the starting point
        common_start_date = epoch1 if epoch1.compareTo(epoch2) > 0 else epoch2
        
        # Create propagators
        propagator1 = create_propagator(tle1.getLine1(), tle1.getLine2())
        propagator2 = create_propagator(tle2.getLine1(), tle2.getLine2())

        min_dist = float('inf')
        best_time = None
        rel_vel = None

        # First pass: coarse search
        for t in range(0, duration_sec, coarse_step):
            date = common_start_date.shiftedBy(float(t))

            pv1 = propagator1.propagate(date).getPVCoordinates(FramesFactory.getTEME())
            pv2 = propagator2.propagate(date).getPVCoordinates(FramesFactory.getTEME())

            dist = Vector3D.distance(pv1.getPosition(), pv2.getPosition()) / 1000.0

            if dist < min_dist:
                min_dist = dist
                best_time = date
                # Calculate relative velocity at this point
                rel_vel = Vector3D.distance(
                    pv2.getVelocity().subtract(pv1.getVelocity()),
                    Vector3D.ZERO
                ) / 1000.0  # Convert to km/s

                # If we found a very close approach, do fine search
                if dist < threshold_km:
                    # Fine search around this point
                    for dt in range(-coarse_step//2, coarse_step//2, fine_step):
                        fine_date = date.shiftedBy(float(dt))
                        pv1f = propagator1.propagate(fine_date).getPVCoordinates(FramesFactory.getTEME())
                        pv2f = propagator2.propagate(fine_date).getPVCoordinates(FramesFactory.getTEME())
                        fine_dist = Vector3D.distance(pv1f.getPosition(), pv2f.getPosition()) / 1000.0

                        if fine_dist < min_dist:
                            min_dist = fine_dist
                            best_time = fine_date
                            rel_vel = Vector3D.distance(
                                pv2f.getVelocity().subtract(pv1f.getVelocity()),
                                Vector3D.ZERO
                            ) / 1000.0

        return min_dist, best_time, rel_vel
        
    except Exception as e:
        print(f"Error in propagate_and_find_closest: {e}")
        return float('inf'), None, None

def calculate_collision_probability(distance_km, relative_velocity_km_s, threshold_km=10, risk_value=None):
    """
    Calculate collision probability based on distance and risk value.
    
    Args:
        distance_km (float): Distance between objects in km
        relative_velocity_km_s (float): Relative velocity in km/s (not used in this version)
        threshold_km (float): Distance threshold for conjunction
        risk_value (float): Risk value from the model
        
    Returns:
        float: Collision probability between 0 and 1
    """
    # Distance-based probability decreases exponentially with distance
    distance_prob = np.exp(-distance_km / threshold_km)
    
    # Risk-based probability from model
    risk_prob = 1 / (1 + np.exp(risk_value)) if risk_value is not None else 0.0
    
    # Combined probability (weighted average)
    # Give more weight to distance when it's large
    if distance_km > threshold_km:
        weight = 0.8  # More weight to distance
    else:
        weight = 0.5  # Equal weight
        
    collision_probability = weight * distance_prob + (1 - weight) * risk_prob
    
    # Ensure probability is between 0 and 1
    collision_probability = max(0.0, min(1.0, collision_probability))
    
    return collision_probability

def calculate_relative_velocity_components(pv1, pv2):
    """
    Calculate relative velocity components in RTN (Radial, Transverse, Normal) frame.
    
    Args:
        pv1: PVCoordinates of first object
        pv2: PVCoordinates of second object
        
    Returns:
        tuple: (radial, transverse, normal) components in km/s
    """
    # Get position and velocity vectors
    r1 = pv1.getPosition()
    v1 = pv1.getVelocity()
    r2 = pv2.getPosition()
    v2 = pv2.getVelocity()
    
    # Calculate relative velocity
    v_rel = v2.subtract(v1)
    
    # Calculate RTN frame
    r_mag = Vector3D.distance(r1, Vector3D.ZERO)
    r_hat = r1.scalarMultiply(1.0 / r_mag)
    
    h = Vector3D.crossProduct(r1, v1)
    h_hat = h.scalarMultiply(1.0 / Vector3D.distance(h, Vector3D.ZERO))
    
    t_hat = Vector3D.crossProduct(h_hat, r_hat)
    
    # Project relative velocity onto RTN frame
    v_radial = Vector3D.dotProduct(v_rel, r_hat) / 1000.0  # Convert to km/s
    v_transverse = Vector3D.dotProduct(v_rel, t_hat) / 1000.0
    v_normal = Vector3D.dotProduct(v_rel, h_hat) / 1000.0
    
    return v_radial, v_transverse, v_normal

def calculate_miss_distance(pv1, pv2):
    """
    Calculate miss distance between two objects.
    
    Args:
        pv1: PVCoordinates of first object
        pv2: PVCoordinates of second object
        
    Returns:
        float: Miss distance in km
    """
    return Vector3D.distance(pv1.getPosition(), pv2.getPosition()) / 1000.0

def calculate_time_to_closest_approach(pv1, pv2):
    """
    Calculate time to closest approach using relative position and velocity.
    
    Args:
        pv1: PVCoordinates of first object
        pv2: PVCoordinates of second object
        
    Returns:
        float: Time to closest approach in seconds, or None if objects are stationary relative to each other
    """
    r_rel = pv2.getPosition().subtract(pv1.getPosition())
    v_rel = pv2.getVelocity().subtract(pv1.getVelocity())
    
    # Check if relative velocity is zero
    v_rel_mag = Vector3D.dotProduct(v_rel, v_rel)
    if v_rel_mag < 1e-10:  # Small threshold to avoid numerical issues
        return None
    
    # Time to closest approach: t = -r_rel · v_rel / |v_rel|²
    t = -Vector3D.dotProduct(r_rel, v_rel) / v_rel_mag
    
    return t

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
