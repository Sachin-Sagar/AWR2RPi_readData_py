# Real-Time Radar Visualizer for AWR/IWR Boards

This is a Python-based graphical user interface (GUI) for visualizing and logging real-time data from Texas Instruments AWR/IWR series radar sensors (e.g., AWRL1432BOOST-BSD). The application reads, parses, and plots radar data frames, offering a powerful tool for development and debugging.

## Features

- **Real-Time Visualization:** A multi-threaded GUI built with PyQt5 and pyqtgraph ensures smooth, non-blocking visualization of sensor data.
- **Dual-Plot View:** Includes two separate tabs for visualizing:
    - **Point Cloud:** Displays detected objects in a 2D Cartesian space (X, Y).
    - **Range-Doppler Map:** Shows the relationship between the range and velocity of detected objects.
- **Data Logging:** Automatically saves all incoming frame data, including headers, point clouds, and target lists, into a timestamped `.json` file for later analysis.
- **Robust Serial Communication:** Handles hardware communication, including device configuration, baud rate changes, and synchronization to the data stream.
- **Detailed Statistics Panel:** Displays real-time information such as frame number, detection points, target count, CPU load, and sensor temperatures.
- **Cross-Platform Support:** Fully compatible with both **Windows** and **Linux** (including Raspberry Pi).

## System Requirements

### Hardware
- A Texas Instruments AWR/IWR series radar board (e.g., AWRL1432BOOST-BSD)
- A computer or Raspberry Pi to run the application.

### Software
- Python 3.6+
- The following Python libraries are required:
  - `pyserial`
  - `numpy`
  - `PyQt5`
  - `pyqtgraph`

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd <your-repository-directory>
    ```

2.  **Install the required Python libraries:**
    ```bash
    pip install pyserial numpy PyQt5 pyqtgraph
    ```

## Configuration

Before running the application, you must configure the serial COM port.

1.  **Connect the Radar Sensor:** Connect the sensor to your computer via USB. Identify the COM port number assigned to the device.
    - **On Windows:** This will be a `COM` port (e.g., `COM11`). You can find it in the Device Manager.
    - **On Linux/Raspberry Pi:** This will be a device file (e.g., `/dev/ttyACM0`).

2.  **Edit `main.py`:** Open the `main.py` file and update the `CLI_COMPORT_NUM` variable with your port information.

    ```python
    # In main.py
    if sys.platform == "win32":
        # Windows COM Port Name
        CLI_COMPORT_NUM = 'COM11' # <-- ADJUST THIS
    elif sys.platform == "linux":
        # Raspberry Pi (Linux) COM Port Name
        CLI_COMPORT_NUM = '/dev/ttyACM0' # <-- ADJUST THIS
    ```

3.  **Radar Configuration File:** The radar's operational parameters are defined in `profile_80m_40mpsec_bsdevm_16tracks_dyClutter.cfg`. You can modify this file to change the sensor's behavior.

## Usage

To run the application, execute the `main.py` script from your terminal:

```bash
python main.py
The GUI window will appear, and the application will begin configuring the sensor. Once data starts streaming, the plots and statistics will update in real time. A new fHist_YYYYMMDD_HHMMSS.json file will be created in the project directory to log the session's data.

Project Structure
main.py: The main entry point of the application. It handles the GUI, threading, and overall program flow.

parsing_utils.py: Contains the core logic for parsing the radar configuration file and calculating derived parameters.

read_and_parse_frame.py: Responsible for reading a single data frame from the serial port and parsing its binary structure into a Python object.

hw_comms_utils.py: A utility module for handling low-level serial port communication, including port configuration and frame synchronization.

math_utils.py: Provides helper functions for mathematical operations, such as 3D rotations and power-of-2 calculations.

check_pickle.py: A utility script for inspecting and converting data files (originally for .pkl files, now superseded by the JSON logger).

*.cfg: Configuration files that define the radar sensor's parameters.