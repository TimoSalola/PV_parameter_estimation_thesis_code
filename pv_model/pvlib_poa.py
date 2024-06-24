import time
from datetime import datetime

import pandas
from pvlib import location
from pvlib import irradiance
import pandas as pd

from pv_model import __solar_irradiance_estimator
from pv_model import geometric_projections
from pv_model import reflection_estimator
from pv_model import panel_temperature_estimator
from pv_model import output_estimator


############################
#   FUNCTIONS FOR CREATING PLANE OF ARRAY IRRADIANCE CURVES
############################

def print_full(x):
    """
    Prints a dataframe without leaving any columns or rows out. Useful for debugging.
    """
    pandas.set_option('display.max_rows', None)
    pandas.set_option('display.max_columns', None)
    pandas.set_option('display.width', 1400)
    pandas.set_option('display.float_format', '{:10,.2f}'.format)
    pandas.set_option('display.max_colwidth', None)
    print(x)
    pandas.reset_option('display.max_rows')
    pandas.reset_option('display.max_columns')
    pandas.reset_option('display.width')
    pandas.reset_option('display.float_format')
    pandas.reset_option('display.max_colwidth')

def pvlib_complex(year, day, latitude, longitude, tilt, azimuth, rated_power=1):
    """
    This function shows the steps used for generating power output data with pvlib. Also returns the power output.
    PVlib is fully simulated, no restrictions on day range.
    :return: Power output dataframe
    """
    # date for simulation:
    simulation_date_start = datetime.strptime(str(year) + "-" + str(day), "%Y-%j").strftime("%m-%d-%Y")
    simulation_date_end = datetime.strptime(str(year) + "-" + str(day + 1), "%Y-%j").strftime("%m-%d-%Y")

    #start_time = time.time()
    data_pvlib = __solar_irradiance_estimator.__get_irradiance_pvlib(simulation_date_start, simulation_date_end, latitude,
                                                                   longitude)
    #print("--- %s irradiance simulation seconds ---" % (time.time() - start_time))


    #start_time = time.time() #Almost instant to compute!
    # step 2. project irradiance components to plane of array:
    data_pvlib = geometric_projections.irradiance_df_to_poa_df(data_pvlib, tilt, azimuth,  latitude, longitude)
    #print("--- %s geo_projection seconds ---" % (time.time() - start_time))


    #start_time = time.time()
    # step 3. simulate how much of the irradiance components is absorbed:
    data_pvlib = reflection_estimator.add_reflection_corrected_poa_components_to_df(data_pvlib, tilt, azimuth, latitude, longitude)
    #print("--- %s reflection estimation simulation seconds ---" % (time.time() - start_time))

    start_time = time.time()

    # step 4. compute sum of reflection-corrected components:
    data_pvlib = reflection_estimator.add_reflection_corrected_poa_to_df(data_pvlib, tilt, azimuth, latitude, longitude)
    #print("--- %s absorbed sum seconds ---" % (time.time() - start_time))

    # step 4.1. add dummy wind and air temp data
    data_pvlib = panel_temperature_estimator.add_dummy_wind_and_temp(data_pvlib, 2, 7)

    # step 5. estimate panel temperature based on wind speed, air temperature and absorbed radiation

    data_pvlib = panel_temperature_estimator.add_estimated_panel_temperature(data_pvlib)

    # step 6. estimate power output
    data_pvlib = output_estimator.add_output_to_df(data_pvlib, rated_power=rated_power)


    return data_pvlib


def get_irradiance_with_multiplier(year, lat, lon, day, tilt, facing, multiplier):
    """
    :param year: Year to simulate for, example: 2021
    :param lat: Geographic latitude of the installation
    :param lon: Geographic longitude of the installation
    :param day: Day of year which the model is created for
    :param tilt: Panel tilt, angle from horizon towards zenith
    :param facing: Horizontal component of panel angle, 0 for north, 90 for east, 180 for south
    :param multiplier: Related to panel area and efficiency. Useful for matching a POA curve with measurements
    :return: Pandas dataframe containing timestamps and irradiance values, resolution 1/minute
    """
    # Creating a pandas dataframe with one day of irradiance data
    irradiance_day = get_irradiance(year, day, lat, lon, tilt, facing)

    # multiplying plane of array irradiance value by multiplier
    irradiance_day["POA"] = irradiance_day["POA"] * multiplier

    return irradiance_day


def get_poa_solar_noon_v2(year, day, latitude, longitude):
    """
    Simpler solar noon function, uses basic POA and does not use any compensation etc. Does not disregard
    long or short days.
    """

    poa = get_irradiance(year, day, latitude, longitude, 45,180)

    poa = poa[poa['POA'] != 0.0]

    first_minute = poa['minute'].iloc[0]
    last_minute = poa['minute'].iloc[-1]

    solar_noon = (first_minute+last_minute)/2.0

    return solar_noon

def get_solar_noon(year, day, latitude, longitude):
    """
    Returns POA approximated solar noon minute
    :param year:
    :param day: day in 1 to 365
    :param latitude: -90 to 90
    :param longitude: -180 to 180
    :return: minute in range 0 to 1440
    """
    fmin, lmin = get_first_and_last_nonzero_minute(latitude, longitude, year, day)

    if fmin is None or lmin is None:
        return None

    solar_noon = (fmin + lmin) / 2
    if solar_noon > 1439:
        return solar_noon - 1440
    else:
        return solar_noon


def get_first_and_last_nonzero_minute(latitude, longitude, year, day):
    """
    BROKEN FUNCTION
    Returns solar noon minute when longitude, latitude, year and day are known.
    :param latitude:
    :param longitude:
    :param year:
    :param day:
    :return:
    """
    poa = get_irradiance(year, day, latitude, longitude, 15, 180)
    poa = poa.where(poa["POA"] > 0)
    poa = poa.dropna()

    minutes = poa.minute.values

    if len(minutes) > 1420:
        #print("midnight sun, returning none, none")
        return None, None

    if len(minutes) == 0:
        #print("Polar night, returning none as first and last non-zero power minutes")
        return None, None

    first_min = minutes[0]
    last_min = minutes[len(minutes) - 1]

    # 3 easy cases,
    if first_min != 0 and last_min != 1439:
        # ----#####----
        return first_min, last_min

    if first_min == 0 and last_min != 1439:
        # ####-----
        return first_min, last_min

    if first_min != 0 and last_min == 1439:
        # -----####
        return first_min, last_min

    if first_min == 0 and last_min == 1439:
        # #####---##### and ###############
        if len(minutes) == 1440:
            # case #################
            print("midnight sun or equivalent phenomena, returning None, None for first and last minutes of the day")
            return None, None
        else:
            # case #######---######
            for i in range(len(minutes) - 1):
                min1 = minutes[i]
                min2 = minutes[i + 1]
                delta = min2 - min1
                if delta > 1:

                    ## data has a gap

                    #print("data gap,")
                    #print(min1)
                    #print(min2)
                    middle = (min1 + min2) / 2

                    if middle > 1440 / 2:
                        # gap happens on end part
                        return min2 - 1440, min1

                    if middle <= 1440 / 2:
                        # gap in beginning
                        return min2, min1 + 1440

                    return None, None


def get_irradiance(year, day, lat, lon, tilt, facing):
    """
    Returns a basic time to POA table


    Main irradiance estimation function. Based on code from pvlib tutorial:
    https://pvlib-python.readthedocs.io/en/stable/gallery/irradiance-transposition/plot_ghi_transposition.html
    """

    # creating site data required by pvlib poa
    tz = 'GMT'  # assuming that measurements are in UTZ GMT time
    #year = config.YEAR  # loading year from config file
    site = location.Location(lat, lon, tz=tz)

    # creating a pandas entity containing the times for which the irradiance is modeled for
    date = datetime.strptime(str(year) + "-" + str(day), "%Y-%j").strftime("%m-%d-%Y")

    times = pd.date_range(date,  # year + day for which the irradiance is calculated
                          freq='1min',  # take measurement every 1 minute
                          periods=60 * 24,  # how many measurements, 60 * 24 for 60 times per 24 hours = 1440
                          tz=site.tz)  # timezone, using gmt

    # creating a clear sky and solar position entities
    clearsky = site.get_clearsky(times)
    solar_position = site.get_solarposition(times=times)

    # creating PVlib plane of array irradiance dataframe
    POA_irradiance = irradiance.get_total_irradiance(
        surface_tilt=tilt,
        surface_azimuth=facing,
        dni=clearsky['dni'],
        ghi=clearsky['ghi'],
        dhi=clearsky['dhi'],
        solar_zenith=solar_position['apparent_zenith'],
        solar_azimuth=solar_position['azimuth'])

    # turning the times dataframe to a list of minutes
    times = clearsky.index.time
    minutes = []
    for time in times:
        minutes.append(time.hour * 60 + time.minute)

    # creating the output dataframe which consists of only necessary data, minutes and corresponding poa values
    output_df = pd.DataFrame(
        {
            "minute": minutes,
            'POA': POA_irradiance['poa_global']
        }
    )

    return output_df


def create_poa_df_for_year(year, lat, lon, tilt, facing):
    """
    :param year:   year to create poa for
    :param lat:     latitude
    :param lon:     longitude
    :param tilt:    panel tilt
    :param facing:  panel facing
    :return: pandas dataframe containing 365 poa models, one for each day of the year with given parameters
    """
    return create_poa_df_for_range(year, range(0, 365), lat, lon, tilt, facing)


def create_poa_df_for_range(year, list_of_day_numbers, lat, lon, tilt, azimuth):
    """
    Creates a POA DF for each day in list of day numbers, using given latitude, longitude, tilt and facing
    """

    poa_days = []
    for day in list_of_day_numbers:
        poa_day = get_irradiance(year, day, lat, lon, tilt, azimuth)
        poa_day["day"] = day
        poa_days.append(poa_day)

    year_poa_df = pandas.concat(poa_days)

    return year_poa_df
