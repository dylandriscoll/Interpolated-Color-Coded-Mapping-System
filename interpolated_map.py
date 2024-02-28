#This script will generate an interpolated color coded map with the specifications of your choice in the
#area of your choice. It is recommended this script be called from command line using the values from a json 
#object that looks like something like this:
#maps_data.json
#Using this format will allow for custom color schemes as well as adjusting the desired level of detail on the map.
#Default values for the script will be assigned if nothing is inputted, and look like the following:
#--variable", default='AIR_TEMP_F'
#--json-file", default= 'station_data.json'
#--geojson-file", default= 'WA_State_Boundary.geojson'
#--min-lat", type=float, default= 45.543541
#--max-lat", type=float, default= 49.002494
#--min-lon", type=float, default= -124.848974
#--max-lon", type=float, default= -116.916071
#--v-min", type=float, default= -10
#--v-max", type=float, default= 115
#--grid-space", type=float, default= .01
#--variogram-model", default = 'gaussian'
#"--color-scheme",
#    default=[
#        (0, 'darkblue'),
#        (0.2, 'lightblue'),
#        (0.35, 'lightcyan'),
#        (0.5, 'lightgreen'),
#       (0.65, 'green'),
#        (0.8, 'darkgoldenrod'),
#        (0.9, 'orange'),
#        (1.0, 'darkred')
#    ]
#--contour", type=int, default=75
#--nlags", type=int, default = 20
#--projection", default = 'merc'
#It is important to consider all of these variables to get the desired output. This script uses numpy, pandas,
#geopandas, basemap, matpotlib, shapely, pykrige, and basemap.
#Ensure that the json data for the data points contains 'LAT' and 'LNG' for locational data as well as the variable 
#you are using for your interpolation. Additionally, your json data should contain a binary variable called 'MAP_FLAG'.
#1 indicating if a specific point should be used by the kriging algorithm while 0 indicates it should not be used.
#Data accepted into the arrays used for the interpolation will be set as a 16 bit float to limit memory usage. This
#can be adjust as necessary on lines 170-173.

import numpy as np
import pandas as pd
import glob
from pykrige.ok import OrdinaryKriging
from pykrige.kriging_tools import write_asc_grid
import pykrige.kriging_tools as kt
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Path, PathPatch
import json
import geopandas as gpd
from shapely.geometry import Point
import argparse
from matplotlib.colors import BoundaryNorm
from matplotlib.colorbar import ColorbarBase

parser = argparse.ArgumentParser(description="Generate an interpolated map based on JSON data.")
parser.add_argument("--variable", default='AIR_TEMP_F', help= "Variable name to be mapped. This must be the same as the column name in your json data. AIR_TEMP_F by default.")
parser.add_argument("--json-file", default= 'station_data.json', help="JSON data file. Ensure presence of columns with LAT for latitude and LNG for longitude and binary MAP_FLAG for points. station_data.json by default.")
parser.add_argument("--geojson-file", default= 'WA_State_Boundary.geojson', help="GeoJSON boundary file. WA_State_Boundary.geojson by default.")
parser.add_argument("--min-lat", type=float, default= 45.543541, help="Minimum latitude for map. 45.543541 by default.")
parser.add_argument("--max-lat", type=float, default= 49.002494, help="Maximum latitude for map. 49.002494 by default.")
parser.add_argument("--min-lon", type=float, default= -124.848974, help="Minimum longitude for map. -124.848974 by default.")
parser.add_argument("--max-lon", type=float, default= -116.916071, help="Maximum longitude for map. -116.916071 by default.")
parser.add_argument("--v-min", type=float, default= -10, help="Minimum varaible value. -10 by default.")
parser.add_argument("--v-max", type=float, default= 110, help="Maximum variable value. 115 by default.")
parser.add_argument("--grid-space", type=float, default= .01, help="Grid spacing for map. .01 by default.")
parser.add_argument("--variogram-model", default = 'gaussian', help="Variogram model type. Gaussian by default.")
parser.add_argument(
    "--color-scheme",
    default=[
        (0, 'darkblue'),
        (0.2, 'lightblue'),
        (0.35, 'lightcyan'),
        (0.5, 'lightgreen'),
        (0.65, 'green'),
        (0.8, 'darkgoldenrod'),
        (0.9, 'orange'),
        (1.0, 'darkred')
    ],
    help="Color scheme as a list. By default darkblue-lightblue-lightcyan-lightgreen-green-darkgoldenrod-orange-darkred"
)
parser.add_argument("--contour", type=int, default=75, help="Countour levels for color scheme")
parser.add_argument("--nlags", type=int, default = 20, help='Nlag value for kriging object')
parser.add_argument("--projection", default = 'merc', help= "Projection type for map (merc by default)")
parser.add_argument("--steps_for_legend",type=int, default =12, help= "Number of steps for legend. 12 by default.")
args = parser.parse_args()

# Parsing variables from command line
json_file = args.json_file
variable = args.variable
geojson_file = args.geojson_file
min_latitude = args.min_lat
max_latitude = args.max_lat
min_longitude = args.min_lon
max_longitude = args.max_lon
v_min = args.v_min
v_max = args.v_max
grid_space = args.grid_space
contour = args.contour
color_scheme = args.color_scheme
nlags_value = args.nlags
projection_type = args.projection
variogram_model_type = args.variogram_model
steps_for_legend = args.steps_for_legend
output_file = variable+'_BACKGROUND.png'

print("Variables used for this map:")
print("Json source file: "+json_file)
print("Variable name: "+variable)
print("Geojson source file: "+ geojson_file)
print("Minimum latitude: ",min_latitude) 
print("Maximum latitude: ", max_latitude) 
print("Minimum longitude: ",min_longitude) 
print("Maximum longitude: ", max_longitude) 
print("Variable minimum value: ", v_min) 
print("Variable maximum value: ", v_max)
print("Grid spacing: ", grid_space) 
print("Contour levels: ", contour) 
print("Color scheme: ", color_scheme)
print("Number of nlags: ", nlags_value) 
print("Projection to be used: "+ projection_type) 
print("Variogram model to be used: " + variogram_model_type) 
print("Output file name: "+ output_file)

with open(json_file, 'r') as f:
    data = json.load(f)

gdf = gpd.read_file(geojson_file)

# Extract the original geometry coordinates 
geometry = gdf.unary_union

latitudes = []
longitudes = []
variables = []

plt.figure(figsize=(10, 10))

for entry in data:
    try:
        latitude_str = entry["LAT"]
        longitude_str = entry['LNG']
        variable_str = entry[variable]
        map_flag = int(entry['MAP_FLAG'])

        # Check if latitude, longitude, and variable are not None and are valid numeric strings
        if (
            latitude_str is not None
            and longitude_str is not None
            and variable_str is not None
        ):
            latitude = float(latitude_str)
            longitude = float(longitude_str)
            variable_value = float(variable_str)
            
            # Filter out data points with invalid variable values 
            if (
                not np.isnan(variable_value)
                and v_min <= variable_value <= v_max
                and map_flag == 1
            ):
                latitudes.append(latitude)
                longitudes.append(longitude)
                variables.append(variable_value)
    except (ValueError, KeyError):
        pass

# Convert lists to numpy arrays
latitudes = np.array(latitudes, dtype='float16')
longitudes = np.array(longitudes, dtype='float16')
variables = np.array(variables, dtype='float16')

print("latitudes array length: ",len(latitudes))
print("Longitudes array length: ", len(longitudes))
print("Variables array length: ", len(variables))

grid_lon = np.arange(min_longitude, max_longitude, grid_space) 
grid_lat = np.arange(min_latitude, max_latitude, grid_space)
print("Grid succesfully created..")

OK = OrdinaryKriging(
    longitudes, 
    latitudes, 
    variables, 
    variogram_model=variogram_model_type, 
    verbose=True, 
    enable_plotting=False,
    nlags=nlags_value
    )
print("Kriging object succesfully created..")

z1, ss1 = OK.execute('grid', grid_lon, grid_lat)
xintrp, yintrp = np.meshgrid(grid_lon, grid_lat)
print("Interpolation complete..")

fig, ax = plt.subplots(figsize=(10,10))
m = Basemap(
    llcrnrlon= min_longitude,
    llcrnrlat= min_latitude,
    urcrnrlon= max_longitude,
    urcrnrlat= max_latitude, 
    projection=projection_type, 
    resolution='h',
    area_thresh=1000.,
    ax=ax)
print("Map object succesfully created..")

# Convert the coordinates into the map scales
x,y=m(xintrp, yintrp) 
ln,lt=m(longitudes,latitudes)

cmap = LinearSegmentedColormap.from_list('custom_cmap', color_scheme)
print("Color map accepted.. Creating countour..")

cs = ax.contourf(x, y, z1, np.linspace(v_min, v_max, contour), extend='both', cmap=cmap)

# Draw parallels
parallels = np.arange(21.5,26.0,0.5)
m.drawparallels(parallels,labels=[1,0,0,0],fontsize=14, linewidth=0.0) #Draw the latitude labels on the map
print("Map parallels drawn..")

# Draw meridians
meridians = np.arange(119.5,122.5,0.5)
m.drawmeridians(meridians,labels=[0,0,0,1],fontsize=14, linewidth=0.0)
print("Map meridians drawn..")

x0,x1 = ax.get_xlim()
y0,y1 = ax.get_ylim()
map_edges = np.array([[x0,y0],[x1,y0],[x1,y1],[x0,y1]])

# Getting all polygons used to draw the coastlines of the map
polys = [p.boundary for p in m.landpolygons]

# Combining with map edges
polys = [map_edges]+polys[:]

# Creating a PathPatch
codes = [
[Path.MOVETO]+[Path.LINETO for p in p[1:]]
for p in polys
]

polys_lin = [v for p in polys for v in p]

codes_lin = [xx for cs in codes for xx in cs]

path = Path(polys_lin, codes_lin)
patch = PathPatch(path,facecolor='white', lw=0)

ax.add_patch(patch)

# Get the current figure and axis
fig, ax = plt.gcf(), plt.gca()

# Remove any whitespace or border
ax.set_axis_off()

# Save the map without any border or whitespace
plt.savefig(output_file, bbox_inches='tight', pad_inches=0, transparent=True)
print("Map image saved as: "+output_file)

# Create a colormap legend
legend_fig= plt.figure(figsize=(1, 10))
legend_cax = legend_fig.add_axes([0.2, 0.2, 0.6, 0.6])  # [left, bottom, width, height]
norm = BoundaryNorm(np.linspace(v_min, v_max, contour), cmap.N, clip=True)
cb = ColorbarBase(legend_cax, cmap=cmap, norm=norm, orientation='vertical')

even_step = (v_max - v_min) / steps_for_legend  

# Generate tick positions on even steps
custom_ticks = np.arange(v_min, v_max + even_step, even_step)

# Generate tick labels as floats
custom_tick_labels = [float(tick) for tick in custom_ticks]  # Customize labels as needed

# Set the custom ticks and labels
cb.set_ticks(custom_ticks)
cb.set_ticklabels(custom_tick_labels)

cb.ax.tick_params(labelsize=10)

# Save the legend
legend_output_file = output_file.replace('.png', '_LEGEND.png')
legend_fig.savefig(legend_output_file, bbox_inches='tight', pad_inches=0, transparent=True)
print("Legend image saved as: " + legend_output_file)

# Uncomment below to show the created map or maps for testing
#plt.show()