

timezone = "UTC"
# albedo is used for ground reflected irradiance calculations
albedo = 0.151
# module elevation is used for 2m wind speed to wind speed at module altitude calculation
module_elevation = 10

# latitude and longitude coordinates of the estimated system. These are used for angle estimation.
latitude = 60.2044
longitude = 24.9625

# known parameters of fmi installations
latitude_helsinki = 60.2044
longitude_helsinki = 24.9625

latitude_kuopio = 62.8919
longitude_kuopio = 27.6349


elevation_helsinki = 17
elevation_kuopio = 10

tilt_helsinki = 15
tilt_kuopio = 15

azimuth_helsinki = 135
azimuth_kuopio = 217

rated_power_kuopio = 20.28
rated_power_helsinki = 21

############################
#   COLORS
############################
ORANGE = "#ff7700"
PURPLE = "#6633ff"
TEAL = "#33ffff"
GOLD = "#ffff33"

def set_params_helsinki():
    latitude = latitude_helsinki
    longitude = longitude_helsinki
    tilt = tilt_helsinki
    azimuth = azimuth_helsinki
    rated_power = rated_power_helsinki
    module_elevation = elevation_helsinki

def set_params_kuopio():
    latitude = latitude_kuopio
    longitude = longitude_kuopio
    tilt = tilt_kuopio
    azimuth = azimuth_kuopio
    rated_power = rated_power_kuopio
    module_elevation = elevation_kuopio

