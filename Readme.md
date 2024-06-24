# Code documentation


**Project structure:**
* estimators/
	* angler.py
	* geolocator.py
* helpers/
	* angler.py
	* cloud_free_day_finder.py
	* config.py
	* multiplier_matcher.py
	* solar_power_data_loader2.py
	* splitters2.py
* pv_model/
	* astronomical_calculations.py
	* geometric_projections.py
	* output_estimator.py
	* panel_temperature_estimator.py
	* pvlib_poa.py
	* reflection_estimator.py
	* __solar_irradianceestimator.py
* main.py
* main_angle_estimation.py
* main_geolocation_estimation.py



### Code reading tips
1. Functions with __ -prefix are not supposed to be called from functions outside the file they are in.
2. First code revisions had multiple uses of a "function - apply" -structure. This is slow and should be avoided. Remainders of this structure are seen in function names with "fast" in them. Similarly in each case where a function is defined within a function is caused by this.

## Folders

### estimators/
This folder contains the three main system parameter files angler.py, geoguesser_latitude.py and geoguesser_longitude.py. Functions in angler.py are called from main_angle_estimation.py and geolocator functions from main_geolocation_estimation.py.

### helpers/
This directory includes various helper files and functions. Functions for cloud free day finding, multiplier matching, solar pv data loading and dataframe splitting and the config file. 

### pv_model/
Files in directory pv_model/ contain functions required for solar irradiance simulations. These files are required by the improved PV model used in the thesis.

## Mains
main_ -files are ment for actually using and running the code. The generic main.py is for feature testing and plotting figures which are not either angle or geolocation estimation related.


## Package versions
This program was developed and tested using following python and python package versions:
* Python 3.10
* Pvlib 0.10.5
* Pandas 2.2.2
* Matplotlib 3.9.0
* Numpy 1.26.4


