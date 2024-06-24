"""
Irradiance transposition functions. Used for transforming different solar irradiance components to panel
projected irradiance components.

https://www.campbellsci.ca/blog/albedo-resource-assessment

Terminology:
POA: Plane of array irradiance, the total amount of radiation which reaches the panel surface at a given time. This is
the sum of poa projected dhi, dni and ghi.
POA = "dhi_poa" + "dni_poa" + "ghi_poa"


GHI: Global horizontal irradiance
-- irradiance received by an area flat against the ground at a given location and at a given time.

DNI: Direct normal irradiance-irradiance received by a flat received pointing towards the Sun at given time,
given coordinates.

DHI/ DIF: Diffuse horizontal irradiance
— irradiance received from atmospheric scattering and clouds.

"""

import math

import numpy
import pandas
import pvlib.irradiance

import pv_model.astronomical_calculations as astronomical_calculations
from helpers import config


def irradiance_df_to_poa_df(irradiance_df, tilt, azimuth, latitude, longitude):
    """
    This function takes an irradiance dataframe as input. This dataframe should contain ghi, dni and dhi irradiance values
    These values are then projected to the panel surfaces either using simple geometry or more complex equations.

    :param azimuth:
    :param tilt:
    :param longitude:
    :param latitude:
    :param irradiance_df: Solar irradiance dataframe with ghi, dni and dhi components.
    :return: Dataframe with dni, ghi and dhi plane of array irradiance projections
    """

    # 3 projection functions
    def helper_dni_poa(dni, times):
        # DNI to panel surface projection helper function
        return __project_dni_to_panel_surface_using_time(dni, times, tilt, azimuth, latitude, longitude)

    def helper_dhi_poa_perez_fast(dhi, dni, time):
        #print(dhi)
        return __project_dhi_to_panel_surface_perez_fast(time, dhi, dni, tilt, azimuth, latitude, longitude)

    def helper_ghi_poa_dynamic_albedo(ghi, albedo, tilt):
        # GHI to panel surface projection helper function with dynamic albedo = ground reflectivity changes
        # using albedo from df if albedo column exists, otherwise uses config.albedo
        return __project_ghi_to_panel_surface(ghi, albedo, tilt)


    # adding dni poa to df
    irradiance_df["dni_poa"] = helper_dni_poa(irradiance_df["dni"], irradiance_df["time"])

    # adding ghi poa to df
    # ghi_poa calculation uses ground reflections which requires a ground albedo value. If not included in df, read
    # default albedo from config.py
    if "albedo" in irradiance_df.columns:
        irradiance_df["ghi_poa"] = helper_ghi_poa_dynamic_albedo(irradiance_df["ghi"], irradiance_df["albedo"], tilt)
    else:
        irradiance_df["ghi_poa"] = helper_ghi_poa_dynamic_albedo(irradiance_df["ghi"], config.albedo, tilt)


    # adding dhi poa to df
    # making sure no zeros or negative numbers go to dhi_poa function, they will cause divided by zero errors
    irradiance_df.loc[irradiance_df['dhi'] < 0.01, 'dhi'] = 0.01
    irradiance_df["dhi_poa"] = helper_dhi_poa_perez_fast(irradiance_df["dhi"], irradiance_df["dni"],
                                                         irradiance_df["time"])

    # adding the sum of projections to df as poa
    irradiance_df["poa"] = irradiance_df["dhi_poa"] + irradiance_df["dni_poa"] + irradiance_df["ghi_poa"]

    #print("POA transposition done.")
    return irradiance_df


"""
PROJECTION FUNCTIONS
4 functions for 3 components, 2 functions for DNI as either date or angle of incidence can be used for computing the 
same result.
"""


def __project_dni_to_panel_surface_using_time(dni, dt, tilt, azimuth, latitude, longitude):
    """
    Based on https://pvpmc.sandia.gov/modeling-steps/1-weather-design-inputs/plane-of-array-poa-irradiance
    /calculating-poa-irradiance/poa-beam/
    :param DNI: Direct sunlight irradiance component in W
    :param dt: Time of simulation
    :return: Direct radiation per 1m² of solar panel surface
    """
    angle_of_incidence = astronomical_calculations.get_solar_angle_of_incidence(dt, tilt, azimuth, latitude, longitude)

    return __project_dni_to_panel_surface_using_angle(dni, angle_of_incidence)


def __project_dni_to_panel_surface_using_angle(dni, angle_of_incidence):
    """
    :param dni:(list) Direct sunlight irradiance component in W
    :param angle_of_incidence: (list) angle between sunlight and solar panel normal, calculated by astronomical_calculations.py
    :return:(list) Direct radiation hitting solar panel surface.
    """

    # this is super simple geometric projection, result=cos(AOI)*radiation

    # transforming arrays/lists to numpy so that angle unit conversion and cosines are super fast
    dni_numpy_array = dni.to_numpy()
    aoi_numpy_array = angle_of_incidence
    aoi_numpy_array_radians = numpy.radians(aoi_numpy_array)
    aoi_cosined = numpy.cos(aoi_numpy_array_radians)

    # Perform element-wise multiplication
    result = dni_numpy_array * aoi_cosined

    return result


def __project_dhi_to_panel_surface_perez_fast(time, dhi, dni, tilt, azimuth, latitude, longitude):
    """
    dhi to dhi_poa projection is somewhat messy. This "optimized" and "fast" function is messy as well -> the whole
    function is somewhat horrible to look at.
    :param time: (list) timestamps in utc
    :param dhi: (list, watts) dhi irradiance values
    :param dni: (list, watts) dni irradiance values
    :param tilt: (decimal, degrees) panel tilt value
    :param azimuth: (decimal, degrees) panel azimuth value
    :param latitude: (decimal, degrees wgs84) geolocation latitude
    :param longitude: (decimal, degrees wgs84) geolocation longitude
    :return:
    """

    # creating new temporary df with irradiances and times
    df = pandas.concat([time, dhi, dni], axis=1)

    # adding system parameters to this new df
    df["tilt"] = tilt
    df["azimuth"] = azimuth
    df["latitude"] = latitude
    df["longitude"] = longitude

    # and dni extra, this is not very time sensitive as it's a function of earth sun distance variation.
    dni_extra = pvlib.irradiance.get_extra_radiation(time.iloc[0])
    df["dni_extra"] = dni_extra

    # adding sun angles to df
    df["solar_azimuth"], df["solar_zenith"] = astronomical_calculations.get_solar_azimuth_zenith(df["time"],
                                                                                                 df["latitude"],
                                                                                          df["longitude"])
    # adding air mass to df
    airmass = astronomical_calculations.get_air_mass(df["time"], df["latitude"], df["longitude"])
    df["airmass"] = airmass

    # finally, calculating the dhi perez projection
    dhi_perez = pvlib.irradiance.perez(df["tilt"], df["azimuth"], df["dhi"], df["dni"], df["dni_extra"],
                                       df["solar_zenith"], df["solar_azimuth"],
                                       df["airmass"], return_components=False)

    return dhi_perez


def __project_ghi_to_panel_surface(ghi, albedo, tilt):
    """
    Equation from
    https://pvpmc.sandia.gov/modeling-guide/1-weather-design-inputs/plane-of-array-poa-irradiance/calculating-poa-irradiance/poa-ground-reflected/

    Uses ground albedo and panel angles to estimate how much of the sunlight per 1m² of ground is radiated towards solar
    panel surfaces.
    :param ghi: Ground reflected solar irradiance.
    :return: Ground reflected solar irradiance hitting the solar panel surface.
    """
    step1 = (1.0 - math.cos(numpy.radians(tilt))) / 2
    step2 = ghi * albedo * step1
    return step2  # ghi * config.albedo * ((1.0 - math.cos(numpy.radians(config.tilt))) / 2.0)


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
