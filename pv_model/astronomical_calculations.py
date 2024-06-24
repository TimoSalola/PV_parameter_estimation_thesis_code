import numpy
import pvlib.atmosphere

from helpers import config
from pvlib import location, irradiance

"""
Astronomical functions
Currently supports:
*angle of incidence(AOI)
*solar angle estimations, Apparent solar zenith and azimuth
*Air mass 

Angle of incidence is the angle between the solar panel normal angle and the angle of sunlight hitting the panel.
Solar azimuth and Zenith are the spherical coordinate angles used for describing the angle of the sun.
More info:https://pvpmc.sandia.gov/modeling-guide/1-weather-design-inputs/plane-of-array-poa-irradiance/calculating-poa-irradiance/angle-of-incidence/

Both angles are useful for reflection and geometric projection functions.

Air mass, constant which which describes how many atmosphere equivalents direct sunlight has to pass
though before reaching solar pv panel surface. 1 if sun is directly above.
More info: https://pvpmc.sandia.gov/modeling-guide/1-weather-design-inputs/irradiance-insolation/air-mass/



"""


def get_solar_angle_of_incidence(dt, tilt, azimuth, latitude, longitude):
    """
    Estimates solar angle of incidence at given datetime. Other parameters, tilt, azimuth and geolocation are from
    config.py.
    :param longitude:
    :param latitude:
    :param azimuth:
    :param tilt:
    :param dt: Datetime object, should include date and time.
    :return: Angle of incidence in degrees. Angle between sunlight and solar panel normal
    """

    solar_azimuth, solar_apparent_zenith = get_solar_azimuth_zenith(dt, latitude, longitude)
    panel_tilt = tilt
    panel_azimuth = azimuth

    # angle of incidence, angle between direct sunlight and solar panel normal
    angle_of_incidence = irradiance.aoi(panel_tilt, panel_azimuth, solar_apparent_zenith, solar_azimuth)

    # setting the upper limit of 90 degrees to avoid issues with projection functions. If light comes with an angle of 90
    # deg AOI, none should be absorbed. The same goes with angles of 90+deg

    # if dt is list, using this
    if isinstance(angle_of_incidence, numpy.ndarray):
        angle_of_incidence[angle_of_incidence > 90] = 90
        return angle_of_incidence

    # if dt is single value, using this
    if angle_of_incidence > 90:
        return 90

    return angle_of_incidence


def get_air_mass(time, latitude, longitude):
    """
    Generates air mass at time + solar zenith angle by using the default model
    :param longitude:
    :param latitude:
    :param time:
    :return:
    """

    solar_zenith = get_solar_azimuth_zenith(time, latitude, longitude)[1]
    air_mass = pvlib.atmosphere.get_relative_airmass(solar_zenith)
    return air_mass


def get_solar_azimuth_zenith(dt, latitude, longitude):
    """
    Returns apparent solar zenith and solar azimuth angles in degrees.
    :param longitude:
    :param latitude:
    :param dt: time to compute the solar position for.
    :return: azimuth, zenith
    """

    # panel location and installation parameters
    panel_latitude = latitude
    panel_longitude = longitude

    # panel location object, required by pvlib
    panel_location = location.Location(panel_latitude, panel_longitude, tz=config.timezone)

    # solar position object
    solar_position = panel_location.get_solarposition(dt)

    # apparent zenith and azimuth, Using apparent for zenith as the atmosphere affects sun elevation.
    # apparent_zenith = Sun zenith as seen and observed from earth surface
    # zenith = True Sun zenith, would be observed if Earth had no atmosphere
    solar_apparent_zenith = solar_position["apparent_zenith"].values
    solar_azimuth = solar_position["azimuth"].values

    return solar_azimuth, solar_apparent_zenith


def __debug_add_solar_angles_to_df(df, panel_tilt, panel_azimuth, latitude, longitude):
    """
    This function is not normally used, but it has proven to be useful for debugging
    """

    def helper_add_zenith(dfn):
        azimuth, zenith = get_solar_azimuth_zenith(dfn["time"], latitude, longitude)
        return zenith

    # applying helper function to dataset and storing result as a new column
    df["zenith"] = df.apply(helper_add_zenith, axis=1)

    def helper_add_azimuth(dfn):
        azimuth, zenith = get_solar_azimuth_zenith(dfn["time"], latitude, longitude)
        return azimuth

    # applying helper function to dataset and storing result as a new column
    df["azimuth"] = df.apply(helper_add_azimuth, axis=1)

    def helper_add_aoi(dfn):
        aoi = get_solar_angle_of_incidence(dfn["time"], panel_tilt, panel_azimuth, latitude, longitude)
        return aoi

    # applying helper function to dataset and storing result as a new column
    df["aoi"] = df.apply(helper_add_aoi, axis=1)

    return df
