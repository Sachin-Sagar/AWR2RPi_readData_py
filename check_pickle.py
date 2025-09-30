import pickle
import json
import numpy as np

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

# Step 2: Create a custom JSON encoder to handle special data types.
class CustomEncoder(json.JSONEncoder):
    """
    A custom JSON encoder that can handle:
    - NumPy ndarray objects (converts them to nested lists)
    - FrameData objects (converts them to dictionaries)
    """
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            # Convert NumPy arrays to Python lists
            return obj.tolist()
        if isinstance(obj, FrameData):
            # Convert our custom FrameData object to a dictionary
            return {
                "header": obj.header,
                "num_points": obj.num_points,
                "num_targets": obj.num_targets,
                "stats_info": obj.stats_info,
                "point_cloud": obj.point_cloud.tolist(), # Also convert internal numpy array
                "target_list": obj.target_list,
            }
        # Let the base class default method raise the TypeError for other types
        return json.JSONEncoder.default(self, obj)

# --- Configuration ---
# Set the input .pkl file and the desired output .json file
pickle_file_path = 'your_fHist_file.pkl' # <-- CHANGE THIS
json_file_path = 'output_data.json'      # <-- CHANGE THIS (optional)

# --- Main Conversion Logic ---
try:
    print(f"Loading data from '{pickle_file_path}'...")
    # Open the pickle file in binary read mode
    with open(pickle_file_path, 'rb') as pkl_file:
        # Load the entire list of FrameData objects
        fHist_data = pickle.load(pkl_file)
    
    print("Data loaded successfully.")
    print(f"Converting and writing data to '{json_file_path}'...")
    
    # Open the JSON file in write mode
    with open(json_file_path, 'w') as json_file:
        # Use json.dump() with our custom encoder and add indentation for readability
        json.dump(fHist_data, json_file, cls=CustomEncoder, indent=4)
        
    print("\nConversion complete! ✨")
    print(f"You can now view your data in the file: {json_file_path}")

except FileNotFoundError:
    print(f"ERROR: The file '{pickle_file_path}' was not found. Please check the filename.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")