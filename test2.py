import orekit
from orekit.pyhelpers import setup_orekit_curdir
from org.orekit.frames import FramesFactory
from org.orekit.propagation.analytical.tle import TLEPropagator, TLE

# Initialize Orekit
orekit.initVM()
setup_orekit_curdir(from_pip_library=True)

# TLE data
line1 = "1 00005U 58002B   00179.78495062  .00000023  00000-0  28098-4 0  9994"
line2 = "2 00005 034.2682 348.7242 1859667 331.7664 019.3264 10.82419157413667"

# Create TLE and propagator
tle = TLE(line1, line2)
prop = TLEPropagator.selectExtrapolator(tle)
epoch = tle.getDate()

# Get user input for propagation days
try:
    total_days = float(input("Enter the number of days to propagate: "))
except ValueError:
    print("Invalid input. Please enter a number.")
    exit(1)

# Calculate number of 6-hour intervals
interval_minutes = 360  # 6 hours
intervals_per_day = 24 * 60 / interval_minutes  # 4 intervals per day
total_intervals = int(total_days * intervals_per_day)

# Print header
print(f"Propagation Time x [km] y [km] z [km] vx [km/s] vy [km/s] vz [km/s]")

# Loop through time intervals
for i in range(total_intervals + 1):  # +1 to include the final time
    # Calculate time in days
    days = i * interval_minutes / (24 * 60)
    
    # Convert days to seconds and ensure it's a float
    seconds = float(days * 86400)
    
    # Propagate to the specified time
    state = prop.propagate(epoch.shiftedBy(seconds))
    print(state)
    
    # Get state in TEME frame
    pv = state.getPVCoordinates(FramesFactory.getTEME())
    position = pv.getPosition()
    velocity = pv.getVelocity()
    
    # Convert to km and km/s
    x = position.getX() / 1000.0
    y = position.getY() / 1000.0
    z = position.getZ() / 1000.0
    vx = velocity.getX() / 1000.0
    vy = velocity.getY() / 1000.0
    vz = velocity.getZ() / 1000.0
    
    # Print results
    print(f"{days:.2f} days {x:.6f} {y:.6f} {z:.6f} {vx:.6f} {vy:.6f} {vz:.6f}")