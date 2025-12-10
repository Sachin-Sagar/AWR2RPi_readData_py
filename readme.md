# Real-Time Radar Data Visualizer for AWR1432BOOST

This project is a multi-threaded Python application that provides a real-time graphical user interface (GUI) for visualizing data from a Texas Instruments AWR1432BOOST-BSD radar board. It is designed to run on a Raspberry Pi 4B but is also compatible with other systems.

The application reads, parses, and displays radar data in real-time, offering visual insights into the detected point cloud and targets. It also logs all incoming data to a JSON file for post-processing and analysis.

## Features

*   **Real-Time GUI**: A user-friendly interface built with PyQt5 that displays radar data as it is received.
*   **Multi-Plot Visualization**: Includes two main plots:
    *   Point Cloud Plot: Shows the detected points in a 2D (X, Y) Cartesian space.
    *   Range-Doppler Plot: Visualizes the range and velocity of detected points.
*   **Live Statistics Panel**: Displays real-time statistics from the radar frame, including:
    *   Frame Number
    *   Number of Detection Points
    *   Number of Tracked Targets
    *   CPU and UART Load
    *   Sensor Temperatures
*   **Multi-Threaded Architecture**: Utilizes separate threads for data processing, data logging, and the GUI to ensure a smooth, non-blocking user experience.
*   **JSON Data Logging**: Automatically saves all parsed frame data, including a local timestamp, into a timestamped `.json` file within the `output/` directory. This structured format is perfect for playback or further analysis.
*   **Robust Serial Communication**: Efficiently handles communication with the radar board, including configuration and continuous data streaming.

## Data Flow Diagram

The application operates on a multi-threaded model to handle data acquisition, processing, visualization, and logging concurrently.

+------------------+      +--------------------------+      +----------------------+
|                  |      |                          |      |                      |
|  Radar Hardware  |----->|  Data Processing Thread  |----->|   GUI Thread         |
| (AWR1432BOOST)   |      |    (Worker)              |      |  (BSDVisualizer)     |
|                  |      |                          |      |                      |
+------------------+      +--------------------------+      +-----------+----------+
                             |                                          |
                             | (Pushes FrameData)                       | (Updates Plots & Stats)
                             |                                          v
                             v                                     +----------+
                        +----------------------+                   |          |
                        |                      |                   |   User   |
                        | Data Logging Thread  |                   |          |
                        |    (DataLogger)      |                   +----------+
                        |                      |
                        +-----------+----------+
                                    |
                                    | (Writes to file)
                                    v
                              +--------------+
                              |              |
                              | output/fHist_*.json |
                              |              |
                              +--------------+

*   **Radar Hardware**: The AWR1432 board sends configuration commands and streams binary frame data over the serial port.
*   **Data Processing Thread**: A background thread continuously listens to the serial port, searches for the frame sync pattern, reads the binary data, and parses it into a structured `FrameData` object.
*   **GUI Thread**: The main thread of the application. It receives the `FrameData` object from the processing thread via a thread-safe queue and updates the plots and statistics labels on the screen.
*   **Data Logging Thread**: This thread also receives the `FrameData` object and writes it to a `.json` file in the `output/` directory, ensuring that file I/O does not block the GUI or data acquisition.

## Requirements

To run this application, you need Python 3 and the following libraries.

1.  **System-wide PyQt5 (for Raspberry Pi/Linux)**:
    *   On Raspberry Pi OS (and other Debian-based systems), install PyQt5 using your system's package manager:
        ```bash
        sudo apt update
        sudo apt install python3-pyqt5
        ```
2.  **Python Libraries**: The remaining Python dependencies are listed in `pyproject.toml`. You can install them using `uv` (or `pip`):
    ```bash
    uv pip install -e .
    # or
    pip install -e .
    ```
    *   `pyqtgraph`: For high-performance plotting within the GUI.
    *   `pyserial`: For communication with the radar board via the serial port.
    *   `numpy`: For efficient numerical data manipulation.
    *   `matplotlib`: For plotting analysis results in `analyze_radar_log.py`.

## How to Run

### 1. Connect the Hardware
Connect the AWR1432BOOST-BSD board to your computer.

### 2. Configure the Port
Open the `main.py` file and update the `CLI_COMPORT_NUM` variable to match the serial port of your radar board (e.g., `'COM3'` on Windows or `'/dev/ttyACM0'` on Linux/Raspberry Pi).

### 3. Run the Application
Execute the `main.py` script from your terminal:

```bash
python main.py
```
The GUI window will appear, and if the connection is successful, you will see the plots and statistics updating in real-time. A `fHist_... .json` file will be created in the `output/` directory to log the data.

### 4. Analyze Log Files
After generating log files, you can use the `analyze_radar_log.py` script to inspect frame timing and missed frames:

```bash
python analyze_radar_log.py
```
This will automatically find and process the most recently created log file in the `output/` directory.

You can also specify a particular log file:
```bash
python analyze_radar_log.py output/fHist_YYYYMMDD_HHMMSS.json
```
The script will display plots showing the distribution of inter-frame intervals and a timeline of intervals, highlighting any detected gaps.
