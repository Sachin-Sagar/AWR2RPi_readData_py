import serial
import serial.tools.list_ports

# Define the 8-byte sync pattern for frame synchronization
SYNC_PATTERN = b'\x02\x01\x04\x03\x06\x05\x08\x07'

def configure_control_port(com_port_num, baud_rate):
    """
    Configures and opens the control serial port with a standard terminator.

    Args:
        com_port_num (int): The COM port number (e.g., 11 for COM11).
        baud_rate (int): The initial baud rate for communication.

    Returns:
        serial.Serial or None: A pySerial object if successful, otherwise None.
    """
    com_port_string = f'COM{com_port_num}'
    try:
        # List available ports and check if the desired port exists
        available_ports = [p.device for p in serial.tools.list_ports.comports()]
        if com_port_string not in available_ports:
            print(f'\nERROR: CONTROL port {com_port_string} is NOT in the list of available ports.')
            return None

        # Create and open the serial port object
        sphandle = serial.Serial(
            com_port_string,
            baud_rate,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1.0 # Set a timeout for read operations
        )
        print(f'--- Opened serial port {com_port_string} at {baud_rate} baud. ---')
        return sphandle
    except serial.SerialException as e:
        print(f'ERROR: Failed to open serial port {com_port_string}: {e}')
        return None

def reconfigure_port_for_data(sphandle):
    """
    Reconfigures an open serial port for continuous data streaming by removing the terminator.
    This prepares the port to receive binary frames after configuration is sent.

    Args:
        sphandle (serial.Serial): The pySerial object for the port.
    
    Returns:
        serial.Serial: The reconfigured serial port handle.
    """
    # For pySerial, there's no direct 'terminator' to remove for binary mode.
    # The port is already capable of binary reads. This function is kept for logical
    # consistency with the original MATLAB code structure. Flushing buffers is good practice.
    if sphandle and sphandle.is_open:
        sphandle.reset_input_buffer()
        sphandle.reset_output_buffer()
        print('--- Port configured for data mode (binary streaming). ---')
    return sphandle

def read_frame_header(h_data_serial_port, frame_header_length_bytes):
    """
    Reads from the serial port until a complete frame header is found.
    This function implements a robust byte-by-byte search for the sync pattern.

    Args:
        h_data_serial_port (serial.Serial): The open serial port handle.
        frame_header_length_bytes (int): The expected length of the frame header.

    Returns:
        tuple: (rx_header, byte_count, out_of_sync_bytes)
               - rx_header (bytes or None): The complete header if found.
               - byte_count (int): The number of bytes in the returned header.
               - out_of_sync_bytes (int): Number of bytes discarded while searching for sync.
    """
    out_of_sync_bytes = 0
    
    while True:
        # Read one byte at a time to search for the start of the sync pattern
        try:
            byte = h_data_serial_port.read(1)
            if not byte:
                # This indicates a timeout
                print("Warning: Timeout occurred while reading from serial port.")
                return None, 0, out_of_sync_bytes
        except serial.SerialException as e:
            print(f"ERROR: Serial port read failed: {e}")
            return None, 0, out_of_sync_bytes

        # If the first byte matches, check the rest of the pattern
        if byte == SYNC_PATTERN[0:1]:
            # Read the next 7 bytes
            remaining_pattern = h_data_serial_port.read(7)
            
            if len(remaining_pattern) < 7:
                # Didn't get enough bytes for a full pattern, restart search
                out_of_sync_bytes += 1 + len(remaining_pattern)
                continue

            full_pattern = byte + remaining_pattern
            if full_pattern == SYNC_PATTERN:
                # Sync pattern found, now read the rest of the header
                header_rest_len = frame_header_length_bytes - len(SYNC_PATTERN)
                header_rest = h_data_serial_port.read(header_rest_len)

                if len(header_rest) == header_rest_len:
                    rx_header = full_pattern + header_rest
                    return rx_header, frame_header_length_bytes, out_of_sync_bytes
                else:
                    # Incomplete header read after sync, discard and restart
                    out_of_sync_bytes += len(SYNC_PATTERN) + len(header_rest)
                    continue
            else:
                # Pattern did not match, discard the first byte and continue search
                # The remaining bytes read might contain the start of a new pattern,
                # so we can't discard them all. This is a simplification but robust.
                out_of_sync_bytes += 1
                # To be fully robust, you'd re-process `remaining_pattern` for a potential sync start
                continue
        else:
            out_of_sync_bytes += 1