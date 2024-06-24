import pandas as pd
from pvlib import location
from pvlib import irradiance
from datetime import datetime

from helpers import config

"""
Solar irradiance dataframe creation functions are included in this file.
"""


def get_solar_irradiance_poa(year, day, lat, lon, tilt, facing):
    """
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


def __get_irradiance_pvlib(date_start, date_end,latitude, longitude, mod="ineichen"):
    """
    PVlib based clear sky irradiance modeling
    :param date: Datetime object containing a date
    :param mod: One of the 3 models suupported by pvlib
    :return: Dataframe with ghi, dni, dhi. Or only GHI if using haurwitz
    """

    # creating site data required by pvlib poa
    site = location.Location(latitude, longitude, tz=config.timezone)

    # measurement frequency, for example "15min" or "60min"
    measurement_frequency = str(1) + "min"

    times = pd.date_range(start=date_start,
                          end=date_end,  # year + day for which the irradiance is calculated
                          freq=measurement_frequency,  # take measurement every 60 minutes
                          tz=site.tz)  # timezone

    # creating a clear sky and solar position entities
    clearsky = site.get_clearsky(times, model=mod)

    # adds index as a separate time column, for some reason this is required as even a named index is not callable
    # with df[index_name] and df.index is not supported by function apply structures
    clearsky.insert(loc=0, column="time", value=clearsky.index)



    # returning clearsky irradiance df
    return clearsky
