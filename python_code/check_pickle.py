import pickle
import json
import numpy as np
import pprint

# Step 1: Define the FrameData class so Python knows what it's loading.
# This should match the class from 'read_and_parse_frame.py'.
class FrameData:
    """A class to hold the parsed data for a single frame."""
    def __init__(self):
        self.header = {}
        self.point_cloud = np.array([])
        self.num_points = 0
        self.target_list = {}
        self.num_targets = 0
        self.stats_info = {}

# Step 2: Create a robust JSON encoder to handle all special data types.
class CustomEncoder(json.JSONEncoder):
    """
    A robust JSON encoder that can handle:
    - FrameData objects and all their nested contents.
    - NumPy ndarray objects.
    - Other basic NumPy data types.
    """
    def default(self, obj):
        # --- Handle FrameData objects explicitly ---
        if isinstance(obj, FrameData):
            # Manually build a dictionary from the FrameData object
            serializable_dict = {
                "header": obj.header,
                "num_points": obj.num_points,
                "num_targets": obj.num_targets,
                "stats_info": obj.stats_info,
                "point_cloud": obj.point_cloud.tolist(), # Convert numpy array to list
                "target_list": {}
            }
            # Also convert any numpy arrays inside the target_list dictionary
            if obj.target_list:
                for key, value in obj.target_list.items():
                    if isinstance(value, np.ndarray):
                        serializable_dict["target_list"][key] = value.tolist()
                    else:
                        serializable_dict["target_list"][key] = value
            return serializable_dict

        # --- Handle NumPy arrays and types generally ---
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.bool_):
            return bool(obj)
            
        # Let the base class default method raise the TypeError for other types
        return super().default(obj)

# --- Configuration ---
pickle_file_path = 'your_fHist_file.pkl' # <-- CHANGE THIS
json_file_path = 'output_data.json'      # <-- CHANGE THIS (optional)
preview_rows = 5                         # Number of rows to display

# --- Main Conversion Logic ---
try:
    print(f"Loading data from '{pickle_file_path}'...")
    with open(pickle_file_path, 'rb') as pkl_file:
        fHist_data = pickle.load(pkl_file)
    
    print("Data loaded successfully.")

    # --- Display the first few rows ---
    if fHist_data:
        print(f"\n--- 🕵️‍♀️ Previewing the first {min(preview_rows, len(fHist_data))} rows ---")
        # To preview, we need to convert the objects to a printable format first
        # We can use our new encoder with json.dumps for a clean preview
        for i, frame in enumerate(fHist_data[:preview_rows]):
            print(f"\n--- Frame {i+1} ---")
            frame_as_dict = json.loads(json.dumps(frame, cls=CustomEncoder))
            pprint.pprint(frame_as_dict)
        print("\n-----------------------------------------")
    else:
        print("\n--- The pickle file is empty. ---")
    
    # --- Convert and save the full data ---
    print(f"\nConverting and writing data to '{json_file_path}'...")
    with open(json_file_path, 'w') as json_file:
        json.dump(fHist_data, json_file, cls=CustomEncoder, indent=4)
        
    print("\nConversion complete! ✨")
    print(f"You can now view your full data in the file: {json_file_path}")

except FileNotFoundError:
    print(f"ERROR: The file '{pickle_file_path}' was not found. Please check the filename.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")