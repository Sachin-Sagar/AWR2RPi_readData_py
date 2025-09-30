import sys
import time
import serial
import json
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, QGridLayout
from PyQt5.QtCore import QThread, pyqtSignal, QObject
import pyqtgraph as pg
from datetime import datetime
import queue # Added for thread-safe communication

# Local imports
import hw_comms_utils
import parsing_utils
import read_and_parse_frame
from read_and_parse_frame import FrameData

# --- Configuration ---
CLI_COMPORT_NUM = '/dev/ttyACM1'
CHIRP_CONFIG_FILE = 'profile_80m_40mpsec_bsdevm_16tracks_dyClutter.cfg'
INITIAL_BAUD_RATE = 115200

# --- Robust JSON Encoder Class ---
class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, FrameData):
            serializable_dict = {
                "header": obj.header, "num_points": obj.num_points, "num_targets": obj.num_targets,
                "stats_info": obj.stats_info, "point_cloud": obj.point_cloud.tolist(), "target_list": {}
            }
            if obj.target_list:
                for key, value in obj.target_list.items():
                    serializable_dict["target_list"][key] = value.tolist() if isinstance(value, np.ndarray) else value
            return serializable_dict
        if isinstance(obj, np.ndarray): return obj.tolist()
        if isinstance(obj, np.integer): return int(obj)
        if isinstance(obj, np.floating): return float(obj)
        if isinstance(obj, np.bool_): return bool(obj)
        return super().default(obj)

# --- NEW: Dedicated Data Logger ---
class DataLogger(QObject):
    finished = pyqtSignal()

    def __init__(self, filename):
        super().__init__()
        self.filename = filename
        self.data_queue = queue.Queue()
        self.is_running = True
        self.log_file = None
        self.first_frame = True

    def run(self):
        """This method runs in a separate thread and handles all file I/O."""
        try:
            self.log_file = open(self.filename, 'w')
            self.log_file.write('[') # Start of the JSON array
            print(f"--- Logging data to {self.filename} ---")

            while self.is_running or not self.data_queue.empty():
                try:
                    # Wait for data to appear in the queue (with a timeout)
                    frame = self.data_queue.get(timeout=0.1)
                    
                    if not self.first_frame:
                        self.log_file.write(',')
                    
                    json.dump(frame, self.log_file, cls=CustomEncoder, indent=4)
                    self.first_frame = False
                    self.data_queue.task_done()

                except queue.Empty:
                    continue # No data, just loop again

        except Exception as e:
            print(f"ERROR in logger thread: {e}")
        finally:
            if self.log_file:
                self.log_file.write(']') # End of the JSON array
                self.log_file.close()
                print(f"--- Log file {self.filename} finalized. ---")
            self.finished.emit()

    def add_data(self, frame_data):
        """Adds a frame to the queue to be logged."""
        self.data_queue.put(frame_data)

    def stop(self):
        """Signals the logger to finish up and stop."""
        print("--- Stopping data logger... ---")
        self.is_running = False

class Worker(QObject):
    # ... (Worker class remains the same)
    frame_ready = pyqtSignal(object)
    finished = pyqtSignal()

    def __init__(self, h_data_port, params):
        super().__init__()
        self.h_data_port = h_data_port
        self.params = params
        self.is_running = True

    def run(self):
        while self.is_running:
            try:
                frame_data = read_and_parse_frame.read_and_parse_frame(self.h_data_port, self.params)
                if frame_data and frame_data.header:
                    self.frame_ready.emit(frame_data)
            except Exception as e:
                print(f"Error in worker thread: {e}")
                time.sleep(0.1)
        self.finished.emit()

    def stop(self):
        self.is_running = False

class BSDVisualizer(QMainWindow):
    def __init__(self, h_data_port, params):
        super().__init__()
        self.h_data_port = h_data_port
        self.params = params
        self.frame_num = 0

        self.setWindowTitle("AWRL1432 BSD Visualizer")
        self.setGeometry(100, 100, 1600, 900)
        
        # --- Setup GUI ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        # ... (GUI setup remains the same)
        main_layout = QHBoxLayout(central_widget)
        left_panel = QVBoxLayout()
        main_layout.addLayout(left_panel, 1)
        right_panel = QVBoxLayout()
        main_layout.addLayout(right_panel, 4)
        self._create_stats_panel(left_panel)
        self._create_plot_tabs(right_panel)

        # --- Setup Data Processing Thread ---
        self.worker_thread = QThread()
        self.worker = Worker(self.h_data_port, self.params)
        self.worker.moveToThread(self.worker_thread)
        self.worker.frame_ready.connect(self.update_visuals)
        self.worker_thread.started.connect(self.worker.run)
        self.worker_thread.start()

        # --- Setup and Start Data Logging Thread ---
        log_filename = f"fHist_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.logger_thread = QThread()
        self.data_logger = DataLogger(log_filename)
        self.data_logger.moveToThread(self.logger_thread)
        self.logger_thread.started.connect(self.data_logger.run)
        self.logger_thread.start()

    def _create_stats_panel(self, layout):
        # ... (This method remains the same)
        stats_widget = QWidget()
        stats_layout = QGridLayout(stats_widget)
        layout.addWidget(stats_widget)
        self.stats_labels = {}
        stats_to_create = ["Frame", "Detection Points", "Target Count", "CPU (ms)", "UART Tx (ms)", "Temp RFE (C)", "Temp DIG (C)", "Overflow"]
        for i, text in enumerate(stats_to_create):
            label_title = QLabel(f"<b>{text}:</b>")
            label_value = QLabel("0")
            stats_layout.addWidget(label_title, i, 0)
            stats_layout.addWidget(label_value, i, 1)
            self.stats_labels[text] = label_value
        layout.addStretch()


    def _create_plot_tabs(self, layout):
        # ... (This method remains the same)
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        pc_widget = QWidget()
        pc_layout = QVBoxLayout(pc_widget)
        self.pc_plot = pg.PlotWidget()
        self.pc_plot_item = self.pc_plot.plot([], [], pen=None, symbol='o', symbolSize=5, symbolBrush=(255,255,255,150))
        self.pc_plot.setBackground('k')
        self.pc_plot.setLabel('left', 'Y (m)')
        self.pc_plot.setLabel('bottom', 'X (m)')
        self.pc_plot.showGrid(x=True, y=True)
        self.pc_plot.setAspectLocked(True)
        self.pc_plot.setXRange(-40, 40)
        self.pc_plot.setYRange(0, 100)
        pc_layout.addWidget(self.pc_plot)
        tab_widget.addTab(pc_widget, "Point Cloud")
        rd_widget = QWidget()
        rd_layout = QVBoxLayout(rd_widget)
        self.rd_plot = pg.PlotWidget()
        self.rd_plot_item = self.rd_plot.plot([], [], pen=None, symbol='o', symbolSize=5, symbolBrush=(255,255,255,150))
        self.rd_plot.setBackground('k')
        self.rd_plot.setLabel('left', 'Doppler (m/s)')
        self.rd_plot.setLabel('bottom', 'Range (m)')
        self.rd_plot.showGrid(x=True, y=True)
        self.rd_plot.setXRange(0, 100)
        self.rd_plot.setYRange(-40, 40)
        rd_layout.addWidget(self.rd_plot)
        tab_widget.addTab(rd_widget, "Range-Doppler")

    def update_visuals(self, frame_data):
        """Called by the Worker thread. Updates GUI and sends data to the logger."""
        self.frame_num += 1
        
        # Update GUI elements
        self.stats_labels["Frame"].setText(f"{self.frame_num} ({frame_data.header.get('frameNumber', 0)})")
        # ... (rest of stats updates) ...
        if frame_data.num_points > 0:
            pc = frame_data.point_cloud
            self.pc_plot_item.setData(pc[1, :], pc[2, :])
            self.rd_plot_item.setData(pc[0, :], pc[3, :])
        else:
            self.pc_plot_item.clear()
            self.rd_plot_item.clear()
            
        # Send data to the logger's queue
        self.data_logger.add_data(frame_data)

    def closeEvent(self, event):
        """Handles the window closing event to clean up all resources."""
        print("--- Closing application ---")
        
        # Stop all threads and wait for them to finish
        self.worker.stop()
        self.data_logger.stop()

        self.worker_thread.quit()
        self.logger_thread.quit()

        self.worker_thread.wait()
        self.logger_thread.wait()
        
        if self.h_data_port and self.h_data_port.is_open:
            self.h_data_port.close()
            print("--- Serial port closed ---")
            
        event.accept()

def configure_sensor_and_params(cli_com_port, chirp_cfg_file):
    # ... (This function remains the same)
    cli_cfg = parsing_utils.read_cfg(chirp_cfg_file)
    if not cli_cfg: return None, None
    params = parsing_utils.parse_cfg(cli_cfg)
    target_baud_rate = INITIAL_BAUD_RATE
    for command in cli_cfg:
        if command.startswith("baudRate"):
            target_baud_rate = int(command.split()[1])
            break
    h_data_port = hw_comms_utils.configure_control_port(cli_com_port, INITIAL_BAUD_RATE)
    if not h_data_port: return None, None
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
    params, h_data_port = configure_sensor_and_params(CLI_COMPORT_NUM, CHIRP_CONFIG_FILE)
    if params and h_data_port:
        app = QApplication(sys.argv)
        main_window = BSDVisualizer(h_data_port, params)
        main_window.show()
        sys.exit(app.exec_())