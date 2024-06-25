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

# Usage
In the main_xxx -files comment or uncomment a call to a function as required. For example, a function declared with the
following line:

> def exhaustive_search_single_day():

can be set to run by adding the line:

> exhaustive_search_single_day()

Into the file which contains the function declaration, in this case in main_angle_estimation.py. Now exhaustive single 
day angle estimation will run each time when the file main_angle_estimation.py is executed.

The parameters used by functions declared in any of the main_xx.py files can be adjusted by modifying variables within
these functions. In the following example, the important parameters are defined in the beginning of the function and 
adjusting parameters such as year_n, first_day, last_day or lattice_point_count will change the behavior of the 
exhaustive search algorithm. Some functions may also have parameters that are defined in at a later point.

	def exhaustive_search_single_day():
		#Sample showing how to solve panel angles using exhaustive search #
	
		###########################################
		### Setting parameters and loading data ###
		###########################################
		year_n = 2019
		site = "Kuopio"
	
		first_day = 120
		last_day = 250
		lattice_point_count = 10000

		# loading system parameters
		if site == "Helsinki":
			latitude = config.latitude_helsinki
			longitude = config.longitude_helsinki
			known_tilt = config.tilt_helsinki
			known_azimuth = config.azimuth_helsinki
			data = solar_power_data_loader2.load_helsinki_csv()
		elif site == "Kuopio":
			latitude = config.latitude_kuopio
			longitude = config.longitude_kuopio
			known_tilt = config.tilt_kuopio
			known_azimuth = config.azimuth_kuopio
			data = solar_power_data_loader2.load_kuopio_csv()

The file config.py contains known parameters of FMI Helsinki and Kuopio installations. They are used by some 
functions as shown above.


