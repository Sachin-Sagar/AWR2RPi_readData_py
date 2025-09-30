import numpy as np

def rotate_and_translate_point(pos, azim, elev):
    """
    Applies a 3D rotation to a point based on azimuth and elevation angles.

    Args:
        pos (np.ndarray): A 3x1 vector representing the [x, y, z] position.
        azim (float): The azimuth rotation angle (in radians).
        elev (float): The elevation rotation angle (in radians).

    Returns:
        np.ndarray: The rotated 3x1 position vector.
    """
    # Z-axis rotation matrix for azimuth
    rot_z = np.array([
        [np.cos(azim), np.sin(azim), 0],
        [-np.sin(azim), np.cos(azim), 0],
        [0, 0, 1]
    ])
    
    # X-axis rotation matrix for elevation
    rot_x = np.array([
        [1, 0, 0],
        [0, np.cos(elev), -np.sin(elev)],
        [0, np.sin(elev), np.cos(elev)]
    ])
    
    # Apply rotations: RotZ * RotX * pos
    # In numpy, @ is the operator for matrix multiplication.
    pos_rt = rot_z @ rot_x @ pos
    return pos_rt

def pow2_roundup(x):
    """
    Finds the smallest power of 2 that is greater than or equal to the input.
    Used for FFT padding.

    Args:
        x (int): An integer number.

    Returns:
        int: The next power of 2.
    """
    y = 1
    while x > y:
        y *= 2
    return y
    # A more "Pythonic" and faster way to do this is:
    # return 1 << (x - 1).bit_length()

def compute_h(state_vector_type, s):
    """
    Converts a tracker's Cartesian state vector into a measurement vector
    (e.g., range, azimuth, doppler) for a Kalman filter.

    Args:
        state_vector_type (str): '2DA' or '3DA' specifying the state vector format.
        s (np.ndarray): The state vector [pos_x, pos_y, (pos_z), vel_x, vel_y, (vel_z), ...].

    Returns:
        np.ndarray: The computed measurement vector H.
    """
    if state_vector_type == '2DA':
        # State vector: [pos_x, pos_y, vel_x, vel_y, ...]
        pos_x, pos_y = s[0], s[1]
        vel_x, vel_y = s[2], s[3]
        
        range_val = np.sqrt(pos_x**2 + pos_y**2)
        
        if pos_y == 0:
            azimuth = np.pi / 2
        elif pos_y > 0:
            azimuth = np.arctan(pos_x / pos_y)
        else:
            azimuth = np.arctan(pos_x / pos_y) + np.pi
            
        doppler = (pos_x * vel_x + pos_y * vel_y) / range_val
        
        return np.array([range_val, azimuth, doppler])
        
    elif state_vector_type == '3DA':
        # State vector: [pos_x, pos_y, pos_z, vel_x, vel_y, vel_z, ...]
        pos_x, pos_y, pos_z = s[0], s[1], s[2]
        vel_x, vel_y, vel_z = s[3], s[4], s[5]
        
        range_val = np.sqrt(pos_x**2 + pos_y**2 + pos_z**2)
        
        if pos_y == 0:
            azimuth = np.pi / 2
        elif pos_y > 0:
            azimuth = np.arctan(pos_x / pos_y)
        else:
            azimuth = np.arctan(pos_x / pos_y) + np.pi
            
        elev = np.arctan(pos_z / np.sqrt(pos_x**2 + pos_y**2))
        doppler = (pos_x * vel_x + pos_y * vel_y + pos_z * vel_z) / range_val
        
        return np.array([range_val, azimuth, elev, doppler])
        
    else:
        raise ValueError("Unsupported state vector type. Must be '2DA' or '3DA'.")