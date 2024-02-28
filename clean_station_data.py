import json

# Read the JSON file
with open('station_data.json', 'r') as file:
    data = json.load(file)

# Function to recursively replace NaN with None
def replace_nan_with_none(obj):
    if isinstance(obj, list):
        return [replace_nan_with_none(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: replace_nan_with_none(value) for key, value in obj.items()}
    elif obj is None or (isinstance(obj, float) and math.isnan(obj)):
        return None
    else:
        return obj

import math  # Import the math library for math.isnan

# Replace NaN with None in the JSON data
data = replace_nan_with_none(data)

# Write the modified JSON data back to the file
with open('station_data.json', 'w') as file:
    json.dump(data, file, indent=4)

def remove_single_quotes(obj):
    if isinstance(obj, list):
        return [remove_single_quotes(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: remove_single_quotes(value) for key, value in obj.items()}
    elif isinstance(obj, str):
        return obj.replace("'", "")
    else:
        return obj

# Remove single quotes from the JSON data
data = remove_single_quotes(data)

# Write the modified JSON data back to the file
with open('station_data.json', 'w') as file:
    json.dump(data, file, indent=4)