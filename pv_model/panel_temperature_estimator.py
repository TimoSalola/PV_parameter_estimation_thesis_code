"""
Corrections for taking into account panel reflections, temperature induced losses and other factors which
are not built into other functions.


"""
import math

from helpers import config


def add_estimated_panel_temperature(df):
    """
    Adds an estimate for panel temperature based on wind speed, air temperature and absorbed radiation.
    If air temperature, wind speed or absorbed radiation columns are missing, aborts.
    If columns exists but temperature function returns nan due to faulty input, uses air temperature which should always
    be present in df.
    :param df:
    :return:
    """

    # checking that all required variables exist in df

    if "T" not in df.columns:
        print("No air temperature variable in given dataframe")
        print("Aborting")
        return df

    if "wind" not in df.columns:
        print("No wind speed variable in given dataframe")
        print("Aborting")
        return df

    if "poa_ref_cor" not in df.columns:
        print("no reflection corrected poa value in df 'poa_ref_cor'")
        print("Aborting")
        return df

    def helper_add_panel_temp_fast(poa_ref_cor, wind, T):
        return temperature_of_module(poa_ref_cor, wind, config.module_elevation, T)

    # applying helper function to dataset and storing result as a new column
    df["module_temp"] = helper_add_panel_temp_fast(df["poa_ref_cor"], df["wind"], df["T"])

    return df


def add_dummy_wind_and_temp(df, wind=2, temp=20):
    """
    Adds dummy wind speed and air temperature values. 20 Celsius and 2 m/s wind by default.
    :param df:
    :param wind:
    :param temp:
    :return:
    """

    if "T" not in df.columns:
        df = add_dummy_temperature(df, temp)

    if "wind" not in df.columns:
        df = add_dummy_wind(df, wind)

    return df


def add_dummy_temperature(df, temp=20):
    df["T"] = temp
    return df


def add_dummy_wind(df, wind=2):
    df["wind"] = wind
    return df


def temperature_of_module(absorbed_radiation, wind, module_elevation, air_temperature):
    """
    :param wind: Wind speed in meters per second
    :param absorbed_radiation: radiation hitting a solar panel after reflections are accounted for in W
    :param module_elevation: module elevation from the ground, in meters
    :param air_temperature: air temperature near at 10m? Kelvin?
    :return: module temperature in Kelvin?

    Based on chapter "3.1.3 Deriving PV module temperature" in "Detecting clear-sky instants from photovoltaic power
    measurements" by William Wandji
    """

    # two empirical constants
    constant_a = -3.47
    constant_b = -0.0594

    # wind is sometimes given as west/east components

    # wind speed at model elevation, assumes 0 speed at ground, wind speed vector len at 10m and forms a
    # curve which describes the wind speed transition from 0 to 10m wind speed to higher
    wind_speed = (module_elevation / 10) ** 0.1429 * wind

    module_temperature = absorbed_radiation * math.e ** (constant_a + constant_b * wind_speed) + air_temperature

    return module_temperature
