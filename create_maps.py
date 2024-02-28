import json
import subprocess
import time

# Load the map configurations from maps_data.json
with open('maps_data.json', 'r') as config_file:
    map_configs = json.load(config_file)

# Define the path to your map creation script
map_creation_script = 'interpolated_map.py'  

# Iterate through each map configuration and call the map creation script
for map_config in map_configs:
    variable_name = map_config['variable']
    # Convert the map configuration to command line arguments
    cmd_args = [
        map_creation_script,
        '--variable', map_config['variable'],
        '--json-file', map_config['json_file'],
        '--geojson-file', map_config['geojson_file'],
        '--min-lat', str(map_config['min_lat']),
        '--max-lat', str(map_config['max_lat']),
        '--min-lon', str(map_config['min_lon']),
        '--max-lon', str(map_config['max_lon']),
        '--v-min', str(map_config['v_min']),
        '--v-max', str(map_config['v_max']),
        '--grid-space', str(map_config['grid_space']),
        '--variogram-model', map_config['variogram_model'],
        '--contour', str(map_config['contour']),
        '--nlags', str(map_config['nlags']),
        '--projection', map_config['projection']
    ]
    
    print(cmd_args)
    # Execute the map creation script with the provided arguments
    try:
        subprocess.run(cmd_args, check=True)
        print(f"Map for variable '{variable_name}' created successfully.")
        time.sleep(1)
    except subprocess.CalledProcessError as e:
        print(f"Error creating map for variable '{variable_name}': {e}")
