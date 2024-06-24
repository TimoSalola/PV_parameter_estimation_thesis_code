import statistics

import matplotlib.pyplot
import pandas as pd

from pv_model import pvlib_poa
from helpers import splitters2
from helpers import config


###############################################################
#   Longitude estimation functions
#   The functions here perform well for both Kuopio and Helsinki datasets
#   Accuracy for these datasets is somewhere in less than 1 degree of delta.
#
###############################################################

def longitude_from_solar_noon_solar_noon_poa(long0, solar_noon, solar_noon_poa):
    """
    Improved longitude estimation function
    :param long0: longitude used for simulating solar_noon_poa
    :param solar_noon: measured solar noon minute
    :param solar_noon_poa: simulated solar noon minute
    :return: estimated longitude
    """
    return long0 - (360 / 1440) * (solar_noon - solar_noon_poa)


def longitude_from_solar_date_solar_noon(year, day, solar_noon):
    sim_latitude = 40
    sim_longitude = 40

    sim_solar_noon = pvlib_poa.get_poa_solar_noon_v2(year, day, sim_latitude, sim_longitude)

    longitude = longitude_from_solar_noon_solar_noon_poa(sim_longitude, solar_noon, sim_solar_noon)

    return longitude


def estimate_longitude_based_on_year_df(year_df):
    """
    Estimates the longitude of a solar PV installation when one year of data is given.
    Hard coded values
    simulation_longitude = 25
    simulation_latitude = 60
    Should be changed to better reflect the region where the installations are expected to be if the algorithm is used
    for installations outside of Finland

    :param year_df: One year long of pv data in df
    :return: estimated longitude
    """

    # reading year from year_df
    year = year_df.year.values[0]
    # reading days from year_df

    days = year_df.day.unique()

    # listing simulation parameters
    simulation_longitude = 25
    simulation_latitude = 00

    # list for simulated longitude values, needed as one value is simulated for each day
    longitudes = []

    first_minutes = []
    last_minutes = []
    solar_noons = []
    day_n_list = []

    # calculating a longitude for each day in year_xa
    for day_n in days:
        # spitting needed day from xa
        day_df = splitters2.split_df_day_range(year_df, day_n, day_n)

        # taking first and last minute values
        fmin, lmin = __df_get_first_last_minutes(day_df)
        if fmin is None or lmin is None:
            # skipping if returned none
            continue
        first_minutes.append(fmin)
        last_minutes.append(lmin)
        solar_noons.append((fmin + lmin) / 2.0)
        day_n_list.append(day_n)

        # estimating solar noon based on them
        estimated_solar_noon = (fmin + lmin) / 2

        # simulating solar noon minute
        simulated_solar_noon = pvlib_poa.get_solar_noon(year, day_n, simulation_latitude, simulation_longitude)

        # estimating longitude with the help of estimated solar noon, simulated solar noon and simulated solar noon parameters
        estimated_longitude = longitude_from_solar_noon_solar_noon_poa(simulation_longitude, estimated_solar_noon,
                                                                       simulated_solar_noon)
        longitudes.append(estimated_longitude)

    '''
    matplotlib.pyplot.scatter(first_minutes, day_n_list, label="First minute", c=config.PURPLE)
    matplotlib.pyplot.scatter(last_minutes, day_n_list, label="Last minute", c=config.ORANGE)
    matplotlib.pyplot.scatter(solar_noons, day_n_list, label="Solar noon", c="black")
    matplotlib.pyplot.xlabel("Minute")
    matplotlib.pyplot.ylabel("Day")
    matplotlib.pyplot.legend()
    matplotlib.pyplot.show()

    matplotlib.pyplot.scatter(longitudes, day_n_list, label="Estimated longitude", c=config.ORANGE)
    matplotlib.pyplot.xlabel("Longitude")
    matplotlib.pyplot.ylabel("Day")
    matplotlib.pyplot.legend()
    matplotlib.pyplot.show()
    '''

    results_df = pd.DataFrame(
        {'year': [year] * len(longitudes),
         'day': day_n_list,
         'longitude': longitudes
         })

    # returning statistical mean of estimated longitudes
    return results_df  #statistics.mean(longitudes)


def estimate_longitude_single_day_df(day_df):
    year_n = day_df.year.unique()[0]
    day_n = day_df.day.unique()[0]

    print("Estimating longitude using day " + str(year_n) + "-" + str(day_n))

    fmin, lmin = __df_get_first_last_minutes(day_df)
    measured_solar_noon = (fmin + lmin) / 2

    sim_latitude = 40
    sim_longitude = 40

    sim_solar_noon = pvlib_poa.get_poa_solar_noon_v2(year_n, day_n, sim_latitude, sim_longitude)

    longitude = longitude_from_solar_noon_solar_noon_poa(sim_longitude, measured_solar_noon, sim_solar_noon)
    print(longitude)


def __df_get_first_last_minutes_poa(poa):
    return __df_get_first_last_minutes(poa)


def __df_get_first_last_minutes(df_day):
    # this filtering here is extremely important for longitude prediction accuracy
    df_day = df_day[df_day['output'] > 0.0]
    #print(df_day)
    try:
        fmin = df_day["minute"].values[0]
        #print(fmin)
        lmin = df_day["minute"].values[len(df_day) - 1]
        #print(lmin)
        return fmin, lmin
    except:
        return None, None
