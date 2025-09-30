AWRL1432 Blind Spot Detection (BSD) Visualizer - Python Port
1. Project Goal
This project is a direct port of the original MATLAB-based "AWRL1432 Blind Spot Detection (BSD) Radar Visualizer" to a standalone Python application. The primary goal is to create a real-time, high-performance visualizer that can run on a low-power embedded system like a Raspberry Pi 4B.

This involves translating all core functionalities, including hardware communication, binary data parsing, and GUI rendering, from MATLAB to Python.

2. Current Status: In-Progress ⚠️
The project has successfully transitioned from the planning phase to implementation. All of the core, non-GUI modules from the original MATLAB application have been ported to Python. A modern, multi-threaded GUI application has been built to ensure a responsive user experience.

However, the application is currently non-functional due to a persistent runtime bug that occurs during the initial configuration phase.

Current Roadblock:

A recurring AttributeError: 'float' object has no attribute 'bit_length' error occurs in the parsing_utils.py module.

This error happens during the calculation of derived radar parameters from the .cfg file. The logic mismatch between MATLAB's handling of floating-point numbers and Python's strict typing for bitwise operations is the root cause.

3. Technology Stack
The application is built using a modern Python 3 technology stack, chosen for performance and suitability for the Raspberry Pi platform:

Language: Python 3

GUI Framework: PyQt5 (for a robust and feature-rich user interface)

Real-Time Plotting: pyqtgraph (chosen for its high performance in real-time data visualization)

Numerical Computation: NumPy (for efficient handling of arrays and mathematical operations)

Serial Communication: pySerial (for interfacing with the AWRL1432 EVM's UART ports)

4. Project Structure & Modules
The modular architecture of the original MATLAB project has been preserved in the Python port. The following modules have been created:

bsd_visualizer_main.py:

The main entry point for the application.

Initializes the GUI, configures the sensor, and manages a separate worker thread for data processing to keep the UI from freezing.

hw_comms_utils.py:

Handles all low-level serial port communication.

Includes the critical, robust byte-by-byte search for the 8-byte sync pattern to ensure data stream synchronization.

parsing_utils.py:

Responsible for reading and parsing the text-based .cfg chirp configuration files.

Calculates all derived radar parameters (e.g., range resolution, doppler bins) needed for data processing. This module contains the current bug.

read_and_parse_frame.py:

Performs the real-time parsing of the incoming binary data stream from the sensor.

Decodes the frame header and the custom Type-Length-Value (TLV) payload structure, including the critical TLV offset correction logic identified in the original project.

math_utils.py:

A utility module containing mathematical helper functions, such as 3D point rotation, which were translated from the original codebase.

5. Next Steps
Resolve the AttributeError: The immediate and only priority is to fix the data type mismatch in parsing_utils.py so the application can successfully initialize.

Live Hardware Testing: Once the application runs, perform extensive testing with the AWRL1432 EVM to validate the data parsing and visualization in real-time.

Add User Input Dialogs: Replace the hardcoded COM port and configuration file paths in bsd_visualizer_main.py with user-friendly file and port selection dialogs.

Deployment and Optimization: Deploy the application on the target Raspberry Pi 4B and perform performance profiling and optimization as needed.