from sgp4.api import Satrec
from sgp4.api import WGS72
from datetime import datetime, timedelta
from numpy import radians
from sgp4.conveniences import sat_epoch_datetime
import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import FuncAnimation
from matplotlib import cm
import matplotlib.image as mpimg
from urllib.request import urlretrieve
import time
import subprocess
import sys

# Function to propagate TLE for a given number of days
def propagate_tle(tle_line1, tle_line2, days, step=10):
    """
    Propagates the TLE data for the given number of days.
    :param tle_line1: First line of TLE
    :param tle_line2: Second line of TLE
    :param days: Number of days to propagate
    :param step: Time step in seconds (default: 10 seconds for smoother animation)
    :return: List of propagated state vectors (time, x, y, z, vx, vy, vz)
    """
    satellite = Satrec.twoline2rv(tle_line1, tle_line2, WGS72)
    epoch = sat_epoch_datetime(satellite)
    
    propagated_data = []
    
    # Get the satellite's orbital period (if available, otherwise estimate)
    try:
        # Mean motion in revolutions per day from TLE line 2 (approx)
        mean_motion = float(tle_line2.split()[7])
        orbital_period_seconds = 86400 / mean_motion  # Convert to seconds
    except:
        # Default to a reasonable value if we can't extract from TLE
        orbital_period_seconds = 90 * 60  # ~90 minutes (typical LEO orbit)
    
    # Make sure our step size allows for smooth orbits
    # We want at least 120 points per orbit for smooth visualization
    max_step = orbital_period_seconds / 120
    step = min(step, max_step)
    
    # Generate data points
    for t in range(0, int(days * 86400), int(step)):  # Convert days to seconds
        propagation_time = epoch + timedelta(seconds=t)
        
        # Convert to Julian date and fraction
        jd = propagation_time.toordinal() + 1721425.5  # Add Julian date offset
        
        # Calculate fraction of day
        fr = (propagation_time.hour / 24.0 + 
              propagation_time.minute / 1440.0 + 
              propagation_time.second / 86400.0)
        
        # Get position and velocity
        e, r, v = satellite.sgp4(jd, fr)
        
        if e == 0:  # Check for propagation errors
            propagated_data.append((propagation_time, *r, *v))
        else:
            print(f"Propagation error at time {propagation_time}")
    
    return propagated_data

def load_satellite_data(csv_file):
    """
    Load satellite TLE data from CSV file.
    If the file doesn't exist or is outdated, run tle_data.py to generate/update it.
    
    :param csv_file: Path to the CSV file
    :return: DataFrame with satellite data
    """
    csv_needs_update = False
    
    # Check if CSV file exists
    if not os.path.exists(csv_file):
        print(f"Satellite data file {csv_file} not found.")
        csv_needs_update = True
    else:
        # Check if the file is older than 1 day
        file_age = time.time() - os.path.getmtime(csv_file)
        if file_age > 86400:  # 86400 seconds = 1 day
            print(f"Satellite data is {file_age/3600:.1f} hours old. Checking for updates...")
            csv_needs_update = True
    
    # Update satellite data if needed
    if csv_needs_update:
        print("Fetching latest satellite data...")
        try:
            # Check if tle_data.py exists
            if not os.path.exists("tle_data.py"):
                print("Error: tle_data.py script not found.")
                return None
                
            # Run tle_data.py to update the CSV
            print("Running tle_data.py to update satellite database...")
            result = subprocess.run([sys.executable, "tle_data.py"], 
                                    capture_output=True, text=True)
            
            if result.returncode == 0:
                print("Satellite data updated successfully.")
                print(result.stdout.strip())
            else:
                print(f"Error running tle_data.py: {result.stderr}")
                # If update fails but CSV exists, use existing file
                if not os.path.exists(csv_file):
                    return None
        except Exception as e:
            print(f"Exception while updating satellite data: {str(e)}")
            # If update fails but CSV exists, use existing file
            if not os.path.exists(csv_file):
                return None
    
    # Load the CSV file (either existing or newly updated)
    try:
        return pd.read_csv(csv_file)
    except Exception as e:
        print(f"Error loading satellite data from {csv_file}: {str(e)}")
        return None

def display_satellite_options(satellites_df, limit=10):
    """
    Display a list of satellites for the user to select.
    :param satellites_df: DataFrame with satellite data
    :param limit: Number of satellites to display initially
    """
    print(f"\nAvailable satellites (showing first {limit}):")
    for i, (_, row) in enumerate(satellites_df.head(limit).iterrows()):
        print(f"{i+1}. {row['Name']}")
    
    print(f"\n{len(satellites_df)} total satellites available.")
    print("Options:")
    print("1. Enter a number to select a satellite from the list")
    print("2. Enter 'search <keyword>' to search for a satellite by name")
    print("3. Enter 'more' to see more satellites")

def search_satellites(satellites_df, keyword):
    """
    Search for satellites by name.
    :param satellites_df: DataFrame with satellite data
    :param keyword: Keyword to search for
    :return: DataFrame with filtered results
    """
    results = satellites_df[satellites_df['Name'].str.contains(keyword, case=False)]
    return results

def get_earth_texture():
    """
    Gets the Earth texture map from local file.
    Returns the path to the texture image.
    """
    texture_file = "earth_texture.jpg"
    
    # Check if file exists
    if os.path.exists(texture_file):
        return texture_file
    else:
        print(f"Warning: Earth texture file {texture_file} not found.")
        print("Using solid color Earth instead.")
        return None

def plot_earth(ax=None, rotation_angle=0):
    """
    Create a 3D representation of Earth with realistic texture.
    
    :param ax: Matplotlib axes to plot on (optional)
    :param rotation_angle: Earth rotation angle in degrees (0-360)
    :return: Surface plot of Earth
    """
    # Create a sphere for Earth with much higher resolution for smoother appearance
    # Significantly increased resolution to reduce pixelation
    u, v = np.mgrid[0:2*np.pi:400j, 0:np.pi:200j]
    radius = 6371  # Earth's radius in km
    
    # Coordinates before rotation
    x = radius * np.cos(u) * np.sin(v)
    y = radius * np.sin(u) * np.sin(v)
    z = radius * np.cos(v)
    
    # Apply rotation around z-axis
    rot_angle_rad = np.radians(rotation_angle)
    x_rot = x * np.cos(rot_angle_rad) - y * np.sin(rot_angle_rad)
    y_rot = x * np.sin(rot_angle_rad) + y * np.cos(rot_angle_rad)
    
    # Get or create the axes
    if ax is None:
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')
        
    # Try to load Earth texture
    texture_file = get_earth_texture()
    
    if texture_file and os.path.exists(texture_file):
        # Load Earth texture image
        earth_img = mpimg.imread(texture_file)
        
        # Create texture coordinates
        # Map u from 0-2π to texture coordinates 0-1
        # Map v from 0-π to texture coordinates 0-1
        u_normalized = u / (2 * np.pi)
        v_normalized = v / np.pi
        
        # Plot Earth with texture
        earth = ax.plot_surface(
            x_rot, y_rot, z, 
            facecolors=get_surface_colors(earth_img, u_normalized, v_normalized),
            rstride=1, cstride=1,  # Use full detail
            zorder=0, alpha=1.0,
            antialiased=True
        )
    else:
        # Fallback to a simple colored sphere if texture isn't available
        earth = ax.plot_surface(
            x_rot, y_rot, z, 
            color='blue', alpha=0.9,
            edgecolor='darkblue', linewidth=0.5,
            cmap=plt.cm.Blues, zorder=0
        )
        
    return earth, (x_rot, y_rot, z)

def get_surface_colors(img, u, v):
    """
    Maps the Earth texture to the 3D sphere with improved quality using bilinear interpolation.
    
    :param img: Earth texture image
    :param u: Normalized u coordinates (0-1) for longitude
    :param v: Normalized v coordinates (0-1) for latitude
    :return: Colors for each point on the sphere
    """
    h, w, channels = img.shape
    
    # Convert to pixel coordinates with precise floating point values (not rounded)
    u_pixel = (u % 1.0) * (w - 1)  # Direct mapping without flipping
    v_pixel = v * (h - 1)  # Map v from 0-1 to pixel coordinates
    
    # Initialize colors array
    colors = np.zeros((u.shape[0], u.shape[1], 3))
    
    # Implement bilinear interpolation for smoother texture mapping
    x0 = np.floor(u_pixel).astype(int)
    y0 = np.floor(v_pixel).astype(int)
    x1 = np.minimum(x0 + 1, w - 1)
    y1 = np.minimum(y0 + 1, h - 1)
    
    # Calculate interpolation weights
    wx = u_pixel - x0
    wy = v_pixel - y0
    
    # Ensure indices are within bounds
    x0 = np.clip(x0, 0, w-1)
    y0 = np.clip(y0, 0, h-1)
    
    # Use vectorized operations where possible
    for i in range(u.shape[0]):
        for j in range(u.shape[1]):
            # Get the four nearest pixels
            c00 = img[y0[i,j], x0[i,j], :3]
            c01 = img[y0[i,j], x1[i,j], :3]
            c10 = img[y1[i,j], x0[i,j], :3]
            c11 = img[y1[i,j], x1[i,j], :3]
            
            # Calculate interpolation weights for this point
            w_x = wx[i,j]
            w_y = wy[i,j]
            
            # Bilinear interpolation formula:
            # f(x,y) = (1-wx)(1-wy)f(x0,y0) + wx(1-wy)f(x1,y0) + (1-wx)wy f(x0,y1) + wxwy f(x1,y1)
            color = (
                (1-w_x)*(1-w_y)*c00 + 
                w_x*(1-w_y)*c01 + 
                (1-w_x)*w_y*c10 + 
                w_x*w_y*c11
            )
            
            # Normalize if needed (if image values are 0-255 instead of 0-1)
            if np.max(color) > 1.0:
                color = color / 255.0
                
            colors[i, j] = color
    
    return colors

def calculate_earth_rotation_angle(time_utc):
    """
    Calculate Earth's rotation angle in degrees based on UTC time.
    
    :param time_utc: UTC time as datetime object
    :return: Earth rotation angle in degrees (0-360)
    """
    # Earth rotates 15 degrees per hour (360 degrees / 24 hours)
    # Get the hour of the day as a decimal (including minutes, seconds)
    hour_decimal = time_utc.hour + time_utc.minute/60 + time_utc.second/3600
    
    # Calculate rotation angle in degrees
    # At 0:00 UTC, the prime meridian (0°) is facing away from the sun
    # So we add 180 degrees to align with common map orientation
    rotation_angle = (hour_decimal * 15 + 180) % 360
    
    return rotation_angle

def plot_orbit(results, satellite_name):
    """
    Plot the orbital path in 3D with a realistic Earth.
    :param results: List of propagated state vectors
    :param satellite_name: Name of the satellite
    """
    # Extract coordinates
    times = [r[0] for r in results]
    x = [r[1] for r in results]
    y = [r[2] for r in results]
    z = [r[3] for r in results]
    
    # Create 3D plot
    fig = plt.figure(figsize=(14, 12))
    ax = fig.add_subplot(111, projection='3d')
    
    # Get the Earth rotation angle for the first timestamp
    earth_rotation = calculate_earth_rotation_angle(times[0])
    
    # Plot Earth with the correct orientation based on the first timestamp
    earth, (earth_x, earth_y, earth_z) = plot_earth(ax, rotation_angle=earth_rotation)
    
    # Calculate which points are behind Earth (relative to viewing angle)
    # First get the default viewing angle
    elev, azim = 30, 45
    # Convert viewing angle to radians
    elev_rad = np.radians(elev)
    azim_rad = np.radians(azim)
    
    # Calculate the viewing vector
    view_x = -np.cos(elev_rad) * np.sin(azim_rad)
    view_y = -np.cos(elev_rad) * np.cos(azim_rad)
    view_z = -np.sin(elev_rad)
    view_vec = np.array([view_x, view_y, view_z])
    
    # Calculate dot product between position vectors and viewing vector
    # If dot product is positive, point is behind Earth
    front_indices = []
    back_indices = []
    
    for i, (xi, yi, zi) in enumerate(zip(x, y, z)):
        pos_vec = np.array([xi, yi, zi])
        dot = np.dot(pos_vec, view_vec)
        if dot < 0:  # In front
            front_indices.append(i)
        else:  # Behind
            back_indices.append(i)
    
    # Find continuous segments to avoid connecting lines between discontinuous parts
    # For the FRONT points
    front_segments = []
    if front_indices:
        current_segment = [front_indices[0]]
        for i in range(1, len(front_indices)):
            if front_indices[i] == front_indices[i-1] + 1:  # Continuous
                current_segment.append(front_indices[i])
            else:  # Discontinuity detected
                if len(current_segment) > 1:  # Only add if segment has multiple points
                    front_segments.append(current_segment)
                current_segment = [front_indices[i]]
        if len(current_segment) > 1:  # Add the last segment if it has multiple points
            front_segments.append(current_segment)
    
    # For the BACK points
    back_segments = []
    if back_indices:
        current_segment = [back_indices[0]]
        for i in range(1, len(back_indices)):
            if back_indices[i] == back_indices[i-1] + 1:  # Continuous
                current_segment.append(back_indices[i])
            else:  # Discontinuity detected
                if len(current_segment) > 1:  # Only add if segment has multiple points
                    back_segments.append(current_segment)
                current_segment = [back_indices[i]]
        if len(current_segment) > 1:  # Add the last segment if it has multiple points
            back_segments.append(current_segment)
    
    # Plot the orbital path segments that are behind Earth with reduced visibility
    for segment in back_segments:
        segment_x = [x[i] for i in segment]
        segment_y = [y[i] for i in segment]
        segment_z = [z[i] for i in segment]
        ax.plot(segment_x, segment_y, segment_z, color='red', linewidth=1.5, 
                alpha=0.3, linestyle='--', zorder=5)
    
    # Plot the orbital path segments that are in front of Earth
    for i, segment in enumerate(front_segments):
        segment_x = [x[i] for i in segment]
        segment_y = [y[i] for i in segment]
        segment_z = [z[i] for i in segment]
        if i == 0:  # Only add label for the first segment
            ax.plot(segment_x, segment_y, segment_z, color='red', linewidth=2.5, 
                    label=f'{satellite_name} Orbit', zorder=10)
        else:
            ax.plot(segment_x, segment_y, segment_z, color='red', linewidth=2.5, zorder=10)
    
    # Add start and end points for the orbit
    ax.scatter(x[0], y[0], z[0], color='green', s=50, label='Start', zorder=20)
    ax.scatter(x[-1], y[-1], z[-1], color='orange', s=50, label='End', zorder=20)
    
    # Display the time at start and end points
    start_time = times[0].strftime('%Y-%m-%d %H:%M:%S')
    end_time = times[-1].strftime('%Y-%m-%d %H:%M:%S')
    ax.text(x[0], y[0], z[0], f"  {start_time}", color='green', fontsize=9, zorder=20)
    ax.text(x[-1], y[-1], z[-1], f"  {end_time}", color='orange', fontsize=9, zorder=20)
    
    # Set labels and title
    ax.set_xlabel('X (km)', fontsize=12)
    ax.set_ylabel('Y (km)', fontsize=12)
    ax.set_zlabel('Z (km)', fontsize=12)
    ax.set_title(f'Orbital Path of {satellite_name} Around Earth\n{start_time} to {end_time}', fontsize=14)
    
    # Calculate distance from origin for each point
    distances = [np.sqrt(xi**2 + yi**2 + zi**2) for xi, yi, zi in zip(x, y, z)]
    min_dist = min(distances)
    max_dist = max(distances)
    
    # Calculate orbit eccentricity (approximation)
    eccentricity = (max_dist - min_dist) / (max_dist + min_dist)
    
    # Show orbit information
    earth_radius = 6371  # km
    min_altitude = min_dist - earth_radius
    max_altitude = max_dist - earth_radius
    orbit_info = (
        f'Min Altitude: {min_altitude:.2f} km\n'
        f'Max Altitude: {max_altitude:.2f} km\n'
        f'Eccentricity: {eccentricity:.4f}\n'
        f'Earth Time: {start_time}'
    )
    ax.text2D(0.05, 0.05, orbit_info, transform=ax.transAxes,
             bbox=dict(facecolor='white', alpha=0.7))
    
    # Set the view to show orbit clearly
    ax.view_init(elev=elev, azim=azim)
    
    # Set equal aspect ratio
    max_range = max(max(x) - min(x), max(y) - min(y), max(z) - min(z))
    mid_x = (max(x) + min(x)) / 2
    mid_y = (max(y) + min(y)) / 2
    mid_z = (max(z) + min(z)) / 2
    ax.set_xlim(mid_x - max_range/2, mid_x + max_range/2)
    ax.set_ylim(mid_y - max_range/2, mid_y + max_range/2)
    ax.set_zlim(mid_z - max_range/2, mid_z + max_range/2)
    
    # Add grid and make it semi-transparent
    ax.grid(True, alpha=0.3)
    
    plt.legend()
    plt.tight_layout()
    plt.show()

def animate_orbit(results, satellite_name, interval=30):
    """
    Create an animation of the satellite orbit with a realistic, rotating Earth.
    :param results: List of propagated state vectors
    :param satellite_name: Name of the satellite
    :param interval: Time between animation frames in milliseconds (default: 30ms for smooth animation)
    """
    # Extract coordinates and times
    times = [r[0] for r in results]
    x = [r[1] for r in results]
    y = [r[2] for r in results]
    z = [r[3] for r in results]
    
    # Create 3D plot
    fig = plt.figure(figsize=(14, 12))
    ax = fig.add_subplot(111, projection='3d')
    
    # Plot initial Earth (will be updated during animation)
    # Get the Earth rotation angle for the first timestamp
    earth_rotation = calculate_earth_rotation_angle(times[0])
    earth, (earth_x, earth_y, earth_z) = plot_earth(ax, rotation_angle=earth_rotation)
    
    # Store Earth as reusable object to update later
    earth_surface = earth
    
    # Calculate which points are behind Earth (for the faded reference path)
    elev, azim = 30, 45  # Fixed view angles
    # Convert viewing angle to radians
    elev_rad = np.radians(elev)
    azim_rad = np.radians(azim)
    
    # Calculate the viewing vector
    view_x = -np.cos(elev_rad) * np.sin(azim_rad)
    view_y = -np.cos(elev_rad) * np.cos(azim_rad)
    view_z = -np.sin(elev_rad)
    view_vec = np.array([view_x, view_y, view_z])
    
    # Calculate dot product between position vectors and viewing vector
    front_indices = []
    back_indices = []
    
    for i, (xi, yi, zi) in enumerate(zip(x, y, z)):
        pos_vec = np.array([xi, yi, zi])
        dot = np.dot(pos_vec, view_vec)
        if dot < 0:  # In front
            front_indices.append(i)
        else:  # Behind
            back_indices.append(i)
    
    # Find continuous segments to avoid connecting lines between discontinuous parts
    # For the FRONT points
    front_segments = []
    if front_indices:
        current_segment = [front_indices[0]]
        for i in range(1, len(front_indices)):
            if front_indices[i] == front_indices[i-1] + 1:  # Continuous
                current_segment.append(front_indices[i])
            else:  # Discontinuity detected
                if len(current_segment) > 1:  # Only add if segment has multiple points
                    front_segments.append(current_segment)
                current_segment = [front_indices[i]]
        if len(current_segment) > 1:  # Add the last segment if it has multiple points
            front_segments.append(current_segment)
    
    # For the BACK points
    back_segments = []
    if back_indices:
        current_segment = [back_indices[0]]
        for i in range(1, len(back_indices)):
            if back_indices[i] == back_indices[i-1] + 1:  # Continuous
                current_segment.append(back_indices[i])
            else:  # Discontinuity detected
                if len(current_segment) > 1:  # Only add if segment has multiple points
                    back_segments.append(current_segment)
                current_segment = [back_indices[i]]
        if len(current_segment) > 1:  # Add the last segment if it has multiple points
            back_segments.append(current_segment)
    
    # Plot behind Earth orbit path reference (faded more)
    for segment in back_segments:
        segment_x = [x[i] for i in segment]
        segment_y = [y[i] for i in segment]
        segment_z = [z[i] for i in segment]
        ax.plot(segment_x, segment_y, segment_z, color='gray', alpha=0.15, 
                linestyle='--', linewidth=1, zorder=5)
    
    # Plot in front of Earth orbit path reference
    for segment in front_segments:
        segment_x = [x[i] for i in segment]
        segment_y = [y[i] for i in segment]
        segment_z = [z[i] for i in segment]
        ax.plot(segment_x, segment_y, segment_z, color='gray', alpha=0.3, 
                linestyle='--', linewidth=1, zorder=5)
    
    # Initialize satellite point and orbit trace
    point, = ax.plot([], [], [], 'ro', markersize=10, label=satellite_name, zorder=20)
    orbit, = ax.plot([], [], [], 'r-', alpha=0.8, linewidth=2.5, label='Orbital Path', zorder=10)
    
    # Set labels and title
    ax.set_xlabel('X (km)', fontsize=12)
    ax.set_ylabel('Y (km)', fontsize=12)
    ax.set_zlabel('Z (km)', fontsize=12)
    ax.set_title(f'Orbital Animation of {satellite_name} Around Earth', fontsize=14)
    
    # Calculate distance from origin for each point
    distances = [np.sqrt(xi**2 + yi**2 + zi**2) for xi, yi, zi in zip(x, y, z)]
    min_dist = min(distances)
    max_dist = max(distances)
    
    # Calculate orbit eccentricity (approximation)
    eccentricity = (max_dist - min_dist) / (max_dist + min_dist)
    
    # Show minimum altitude info
    earth_radius = 6371  # km
    min_altitude = min_dist - earth_radius
    max_altitude = max_dist - earth_radius
    
    orbit_info = (
        f'Min Altitude: {min_altitude:.2f} km\n'
        f'Max Altitude: {max_altitude:.2f} km\n'
        f'Eccentricity: {eccentricity:.4f}'
    )
    static_info = ax.text2D(0.05, 0.05, orbit_info, transform=ax.transAxes,
                          bbox=dict(facecolor='white', alpha=0.7))
    
    # Set the initial view to show orbit clearly - this will be fixed during animation
    ax.view_init(elev=elev, azim=azim)
    
    # Set equal aspect ratio
    max_range = max(max(x) - min(x), max(y) - min(y), max(z) - min(z))
    mid_x = (max(x) + min(x)) / 2
    mid_y = (max(y) + min(y)) / 2
    mid_z = (max(z) + min(z)) / 2
    ax.set_xlim(mid_x - max_range/2, mid_x + max_range/2)
    ax.set_ylim(mid_y - max_range/2, mid_y + max_range/2)
    ax.set_zlim(mid_z - max_range/2, mid_z + max_range/2)
    
    # Add grid and make it semi-transparent
    ax.grid(True, alpha=0.3)
    
    # Add timestamp and current altitude annotation
    timestamp_text = ax.text2D(0.05, 0.95, '', transform=ax.transAxes, color='black',
                              bbox=dict(facecolor='white', alpha=0.7))
    altitude_dynamic_text = ax.text2D(0.05, 0.90, '', transform=ax.transAxes, color='black',
                                    bbox=dict(facecolor='white', alpha=0.7))
    
    # Trail length (how many previous points to show)
    trail_length = min(100, len(results) // 10)
    
    # Precompute Earth rotation angles for each frame to improve performance
    earth_rotations = [calculate_earth_rotation_angle(t) for t in times]
    
    # To store the previous Earth surface for removal
    earth_artists = []
    
    def init():
        point.set_data([], [])
        point.set_3d_properties([])
        orbit.set_data([], [])
        orbit.set_3d_properties([])
        timestamp_text.set_text('')
        altitude_dynamic_text.set_text('')
        # We don't return the Earth here because we'll be replacing it
        return point, orbit, timestamp_text, altitude_dynamic_text
    
    def update(frame):
        # Clear previous Earth (if any)
        for artist in earth_artists:
            if artist in ax.collections:
                artist.remove()
        earth_artists.clear()
        
        # Update the satellite position
        point.set_data([x[frame]], [y[frame]])
        point.set_3d_properties([z[frame]])
        
        # Get current timestamp and Earth rotation angle
        current_time = times[frame]
        rotation_angle = earth_rotations[frame]
        
        # Redraw Earth with the correct rotation for this timestamp
        new_earth, _ = plot_earth(ax, rotation_angle=rotation_angle)
        earth_artists.append(new_earth)
        
        # Update the orbit trace (show recent trail)
        start_idx = max(0, frame - trail_length)
        
        # Check for discontinuities in the trail segment
        trail_segment = list(range(start_idx, frame + 1))
        continuous_segments = []
        
        if trail_segment:
            current_segment = [trail_segment[0]]
            for i in range(1, len(trail_segment)):
                if trail_segment[i] == trail_segment[i-1] + 1:  # Continuous
                    current_segment.append(trail_segment[i])
                else:  # Discontinuity detected
                    continuous_segments.append(current_segment)
                    current_segment = [trail_segment[i]]
            continuous_segments.append(current_segment)
        
        # Clear previous trail
        orbit.set_data([], [])
        orbit.set_3d_properties([])
        
        # Plot each continuous segment separately
        if len(continuous_segments) == 1:
            # Single continuous segment - use the existing line
            indices = continuous_segments[0]
            orbit.set_data([x[i] for i in indices], [y[i] for i in indices])
            orbit.set_3d_properties([z[i] for i in indices])
        else:
            # Multiple segments - create new lines for each segment
            for segment in continuous_segments:
                if len(segment) > 1:  # Only draw if more than one point
                    segment_x = [x[i] for i in segment]
                    segment_y = [y[i] for i in segment]
                    segment_z = [z[i] for i in segment]
                    ax.plot(segment_x, segment_y, segment_z, color='red', 
                            linewidth=2.5, alpha=0.8, zorder=10)
        
        # Update timestamp
        time_str = current_time.strftime('%Y-%m-%d %H:%M:%S')
        timestamp_text.set_text(f'Time: {time_str}')
        
        # Update current altitude
        current_dist = np.sqrt(x[frame]**2 + y[frame]**2 + z[frame]**2)
        current_alt = current_dist - earth_radius
        altitude_dynamic_text.set_text(f'Current Altitude: {current_alt:.2f} km')
        
        # Keep the view stable - don't rotate camera
        ax.view_init(elev=elev, azim=azim)
        
        # Include new Earth surface in the return
        return (point, orbit, timestamp_text, altitude_dynamic_text) + tuple(earth_artists)
    
    # Create animation with reduced number of frames for smoother animation
    step = max(1, len(results) // 300)  # Increase frame count for smoother animation
    anim = FuncAnimation(
        fig, update, frames=range(0, len(results), step),
        init_func=init, blit=False, interval=interval, repeat=True
    )
    
    plt.legend()
    plt.tight_layout()
    plt.show()
    
    return anim

# Example usage
if __name__ == "__main__":
    csv_file = "satellite_data.csv"
    satellites_df = load_satellite_data(csv_file)
    
    if satellites_df is None:
        exit(1)
    
    satellites_displayed = 10
    selected_satellite = None
    
    while selected_satellite is None:
        display_satellite_options(satellites_df, satellites_displayed)
        user_input = input("\nEnter selection (or 'q' to quit): ").strip()
        
        if user_input.lower() == 'q':
            print("Exiting program.")
            exit(0)
        elif user_input.lower() == 'more':
            satellites_displayed += 10
        elif user_input.lower().startswith('search '):
            keyword = user_input[7:].strip()
            results = search_satellites(satellites_df, keyword)
            if len(results) == 0:
                print(f"No satellites found matching '{keyword}'")
            else:
                print(f"\nFound {len(results)} satellites matching '{keyword}':")
                for i, (_, row) in enumerate(results.iterrows()):
                    print(f"{i+1}. {row['Name']}")
                
                index = input("\nEnter number to select satellite (or press Enter to continue): ").strip()
                if index.isdigit() and 1 <= int(index) <= len(results):
                    selected_satellite = results.iloc[int(index)-1]
        elif user_input.isdigit():
            index = int(user_input)
            if 1 <= index <= satellites_displayed and index <= len(satellites_df):
                selected_satellite = satellites_df.iloc[index-1]
            else:
                print("Invalid selection. Please try again.")
        else:
            print("Invalid input. Please try again.")
    
    print(f"\nSelected satellite: {selected_satellite['Name']}")
    
    # Ask for propagation settings - only days, use fixed step size
    days = int(input("Enter the number of days to propagate (1-30): ") or "1")
    step = 20  # Fixed step size of 20 seconds
    
    tle_line1 = selected_satellite['TLE1']
    tle_line2 = selected_satellite['TLE2']
    
    # Extract mean motion from TLE line 2 to estimate orbital period
    try:
        mean_motion = float(tle_line2.split()[7])  # Revolutions per day
        orbital_period_minutes = 1440 / mean_motion  # Minutes per orbit
        print(f"\nSatellite orbital period: ~{orbital_period_minutes:.1f} minutes")
        print(f"Recommended to propagate for at least 1-2 full orbits")
        
        # Suggest good propagation time
        suggested_days = max(1, int(orbital_period_minutes * 2 / 1440) + 1)
        if days < suggested_days:
            new_days = input(f"For better visualization, consider using {suggested_days} days. Update? (y/n): ").lower()
            if new_days == 'y':
                days = suggested_days
    except:
        pass
    
    print("\nCalculating orbital propagation...")
    results = propagate_tle(tle_line1, tle_line2, days, step=step)
    
    if not results:
        print("No valid propagation results. Please try a different satellite or time period.")
        exit(1)
    
    print(f"\nPropagation completed with {len(results)} data points.")
    
    # Calculate orbital characteristics
    earth_radius = 6371  # km
    distances = [np.sqrt(r[1]**2 + r[2]**2 + r[3]**2) for r in results]
    min_distance = min(distances)
    max_distance = max(distances)
    
    # Calculate eccentricity (approximation)
    eccentricity = (max_distance - min_distance) / (max_distance + min_distance)
    
    print(f"\nOrbit characteristics:")
    print(f"- Minimum altitude: {min_distance - earth_radius:.2f} km")
    print(f"- Maximum altitude: {max_distance - earth_radius:.2f} km")
    print(f"- Approximate eccentricity: {eccentricity:.4f}")
    
    if min_distance < earth_radius:
        print(f"\nWARNING: The orbit passes through Earth! Minimum distance is {min_distance:.2f} km")
        print(f"Earth's radius is approximately {earth_radius} km")
        adjust = input("Do you want to try a different satellite? (y/n): ").lower()
        
        if adjust == 'y':
            print("Please restart the program and select a different satellite.")
            exit(0)
    
    # Ask user which visualization they prefer
    vis_choice = input("\nVisualization options:\n1. Static 3D Orbit Plot\n2. Animated Orbit\nEnter your choice (1 or 2): ").strip()
    
    if vis_choice == '1':
        print("\nGenerating 3D orbital plot...")
        plot_orbit(results, selected_satellite['Name'])
    elif vis_choice == '2':
        print("\nGenerating orbital animation (close the plot window to exit)...")
        anim = animate_orbit(results, selected_satellite['Name'])  # Use default interval
    else:
        print("Invalid choice. Defaulting to static 3D plot.")
        plot_orbit(results, selected_satellite['Name'])