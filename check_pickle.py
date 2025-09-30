import pickle

# --- IMPORTANT ---
# Replace 'your_file_name.pkl' with the actual path to your .pkl file.
file_path = 'fHist_20231027_103000.pkl' # Example filename

# --- Security Warning ---
# Only unpickle data from sources you trust. Loading a malicious pickle
# file can execute arbitrary code on your machine.

try:
    # Open the file in binary read mode ('rb')
    with open(file_path, 'rb') as f:
        # Load the data from the file
        data = pickle.load(f)

    # --- Now you can inspect the loaded data ---
    
    print(f"Successfully loaded data from: {file_path}\n")

    # 1. Check the type of the loaded object
    print(f"The data is of type: {type(data)}\n")

    # 2. If it's a list or dictionary, check its length
    if isinstance(data, (list, dict)):
        print(f"Number of items in the data: {len(data)}\n")

        # 3. Print the first item to see its structure
        if len(data) > 0:
            # For a list, this gets the first element.
            # For a dict, you might want to iterate through keys instead.
            first_item = data[0] if isinstance(data, list) else next(iter(data.items()))
            
            print("--- Inspecting the first item ---")
            print(f"Type of the first item: {type(first_item)}")
            
            # If the item is an object, you can inspect its attributes
            if hasattr(first_item, '__dict__'):
                 print("Attributes of the first item:")
                 # Pretty-print the object's dictionary
                 import pprint
                 pprint.pprint(vars(first_item))
            else:
                print(f"First item's content: {first_item}")
            print("---------------------------------")


except FileNotFoundError:
    print(f"ERROR: The file '{file_path}' was not found.")
except Exception as e:
    print(f"An error occurred while reading the file: {e}")