import numpy as np
import orekit
from orekit.pyhelpers import setup_orekit_curdir

from org.orekit.frames import FramesFactory
from org.orekit.time import AbsoluteDate, TimeScalesFactory
from org.orekit.propagation.analytical.tle import TLE, TLEPropagator
from org.hipparchus.geometry.euclidean.threed import Vector3D
import datetime

# Initialize VM once
orekit.initVM()
setup_orekit_curdir(from_pip_library=True)

def create_propagator(tle_line1, tle_line2):
    tle = TLE(tle_line1, tle_line2)
    return TLEPropagator.selectExtrapolator(tle)

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
