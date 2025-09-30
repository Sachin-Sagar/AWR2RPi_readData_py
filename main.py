import sys
import time
import serial
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, QGridLayout
from PyQt5.QtCore import QThread, pyqtSignal, QObject
import pyqtgraph as pg

# Local imports
import hw_comms_utils
import parsing_utils
import read_and_parse_frame

# --- Configuration ---
# TODO: Replace these hardcoded values with a file dialog for user selection.
CLI_COMPORT_NUM = 11  # The Application/User UART port number
CHIRP_CONFIG_FILE = 'profile_80m_40mpsec_bsdevm_16tracks_dyClutter.cfg'
INITIAL_BAUD_RATE = 115200

class Worker(QObject):
    """
    Worker thread for handling serial communication and data parsing.
    Runs in the background to keep the GUI responsive.
    """
    frame_ready = pyqtSignal(object)
    finished = pyqtSignal()

    def __init__(self, h_data_port, params):
        super().__init__()
        self.h_data_port = h_data_port
        self.params = params
        self.is_running = True

    def run(self):
        """Main processing loop."""
        while self.is_running:
            try:
                # Read and parse one frame of data
                frame_data = read_and_parse_frame.read_and_parse_frame(self.h_data_port, self.params)
                
                # If a valid frame is received, emit it for the GUI to display
                if frame_data and frame_data.header:
                    self.frame_ready.emit(frame_data)
            except Exception as e:
                print(f"Error in worker thread: {e}")
                time.sleep(0.1) # Avoid busy-looping on error
        
        self.finished.emit()

    def stop(self):
        """Stops the processing loop."""
        self.is_running = False


class BSDVisualizer(QMainWindow):
    """Main application window."""
    def __init__(self, h_data_port, params):
        super().__init__()
        self.h_data_port = h_data_port
        self.params = params
        self.frame_num = 0
        
        self.setWindowTitle(f"AWRL1432 BSD Visualizer")
        self.setGeometry(100, 100, 1600, 900)
        
        # Main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Left Panel (Stats and Config)
        left_panel = QVBoxLayout()
        main_layout.addLayout(left_panel, 1) # 1/5 of the width

        # Right Panel (Tabs for plots)
        right_panel = QVBoxLayout()
        main_layout.addLayout(right_panel, 4) # 4/5 of the width
        
        # --- Create GUI Elements ---
        self._create_stats_panel(left_panel)
        self._create_plot_tabs(right_panel)

        # --- Setup and start the worker thread ---
        self.thread = QThread()
        self.worker = Worker(self.h_data_port, self.params)
        self.worker.moveToThread(self.thread)
        
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.frame_ready.connect(self.update_visuals)
        
        self.thread.start()

    def _create_stats_panel(self, layout):
        """Creates the statistics display panel."""
        stats_widget = QWidget()
        stats_layout = QGridLayout(stats_widget)
        layout.addWidget(stats_widget)

        self.stats_labels = {}
        stats_to_create = [
            "Frame", "Detection Points", "Target Count", 
            "CPU (ms)", "UART Tx (ms)", "Temp RFE (C)", "Temp DIG (C)", "Overflow"
        ]
        
        for i, text in enumerate(stats_to_create):
            label_title = QLabel(f"<b>{text}:</b>")
            label_value = QLabel("0")
            stats_layout.addWidget(label_title, i, 0)
            stats_layout.addWidget(label_value, i, 1)
            self.stats_labels[text] = label_value
        
        layout.addStretch()

    def _create_plot_tabs(self, layout):
        """Creates the tabbed interface for plots."""
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # Point Cloud Tab
        pc_widget = QWidget()
        pc_layout = QVBoxLayout(pc_widget)
        self.pc_plot = pg.PlotWidget()
        self.pc_plot_item = self.pc_plot.plot([], [], pen=None, symbol='o', symbolSize=5, symbolBrush=(255,255,255,150))
        self.pc_plot.setBackground('k')
        self.pc_plot.setLabel('left', 'Y (m)')
        self.pc_plot.setLabel('bottom', 'X (m)')
        self.pc_plot.showGrid(x=True, y=True)
        self.pc_plot.setAspectLocked(True)
        
        # --- AXIS FIX FOR POINT CLOUD ---
        self.pc_plot.setXRange(-40, 40)
        self.pc_plot.setYRange(0, 100)
        
        pc_layout.addWidget(self.pc_plot)
        tab_widget.addTab(pc_widget, "Point Cloud")

        # Range-Doppler Tab
        rd_widget = QWidget()
        rd_layout = QVBoxLayout(rd_widget)
        self.rd_plot = pg.PlotWidget()
        self.rd_plot_item = self.rd_plot.plot([], [], pen=None, symbol='o', symbolSize=5, symbolBrush=(255,255,255,150))
        self.rd_plot.setBackground('k')
        self.rd_plot.setLabel('left', 'Doppler (m/s)')
        self.rd_plot.setLabel('bottom', 'Range (m)')
        self.rd_plot.showGrid(x=True, y=True)

        # --- AXIS FIX FOR RANGE-DOPPLER ---
        # Setting X-axis (Range) to [0, 100] and Y-axis (Doppler) to [-40, 40]
        self.rd_plot.setXRange(0, 100)
        self.rd_plot.setYRange(-40, 40)

        rd_layout.addWidget(self.rd_plot)
        tab_widget.addTab(rd_widget, "Range-Doppler")

    def update_visuals(self, frame_data):
        """Updates all GUI elements with data from a single frame."""
        self.frame_num += 1
        
        # Update Stats
        self.stats_labels["Frame"].setText(f"{self.frame_num} ({frame_data.header.get('frameNumber', 0)})")
        self.stats_labels["Detection Points"].setText(str(frame_data.num_points))
        self.stats_labels["Target Count"].setText(str(frame_data.num_targets))
        
        if frame_data.stats_info.get('timing'):
            cpu_time = frame_data.stats_info['timing'].get('interFrameProcessingTime', 0) / 1000.0
            uart_time = frame_data.stats_info['timing'].get('transmitOutputTime', 0) / 1000.0
            self.stats_labels["CPU (ms)"].setText(f"{cpu_time:.2f}")
            self.stats_labels["UART Tx (ms)"].setText(f"{uart_time:.2f}")

        if frame_data.stats_info.get('temperature'):
            self.stats_labels["Temp RFE (C)"].setText(str(frame_data.stats_info['temperature'].get('rx', 0)))
            self.stats_labels["Temp DIG (C)"].setText(str(frame_data.stats_info['temperature'].get('dig', 0)))

        overflow = frame_data.header.get('uartOverflow', 0)
        if overflow > 0:
            self.stats_labels["Overflow"].setText(f"<font color='red'>UART: {overflow}</font>")
        else:
            self.stats_labels["Overflow"].setText("None")

        # Update Plots
        if frame_data.num_points > 0:
            pc = frame_data.point_cloud
            # pc layout: [range, x, y, doppler, snr]
            self.pc_plot_item.setData(pc[1, :], pc[2, :]) # X, Y
            self.rd_plot_item.setData(pc[0, :], pc[3, :]) # Range, Doppler
        else:
            self.pc_plot_item.clear()
            self.rd_plot_item.clear()

    def closeEvent(self, event):
        """Handles the window closing event to clean up resources."""
        print("--- Closing application ---")
        self.worker.stop()
        self.thread.quit()
        self.thread.wait()
        if self.h_data_port and self.h_data_port.is_open:
            self.h_data_port.close()
            print("--- Serial port closed ---")
        event.accept()

def configure_sensor_and_params(cli_com_port, chirp_cfg_file):
    """
    Reads config, sends it to the sensor, and handles baud rate changes.
    """
    # Use the robust parsing script
    cli_cfg = parsing_utils.read_cfg(chirp_cfg_file)
    if not cli_cfg:
        return None, None
        
    params = parsing_utils.parse_cfg(cli_cfg)
    
    target_baud_rate = INITIAL_BAUD_RATE
    for command in cli_cfg:
        if command.startswith("baudRate"):
            target_baud_rate = int(command.split()[1])
            break
            
    h_data_port = hw_comms_utils.configure_control_port(cli_com_port, INITIAL_BAUD_RATE)
    if not h_data_port:
        return None, None
        
    for command in cli_cfg:
        h_data_port.write((command + '\n').encode())
        time.sleep(0.05)
        
        if "baudRate" in command:
            time.sleep(0.2)
            try:
                h_data_port.baudrate = target_baud_rate
            except Exception as e:
                print(f"ERROR: Failed to change baud rate: {e}")
                h_data_port.close()
                return None, None
    
    hw_comms_utils.reconfigure_port_for_data(h_data_port)
    return params, h_data_port


if __name__ == '__main__':
    # Use the robust parsing script
    params, h_data_port = configure_sensor_and_params(CLI_COMPORT_NUM, CHIRP_CONFIG_FILE)
    
    if params and h_data_port:
        app = QApplication(sys.argv)
        main_window = BSDVisualizer(h_data_port, params)
        main_window.show()
        sys.exit(app.exec_())