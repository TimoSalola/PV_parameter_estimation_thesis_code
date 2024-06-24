import numpy

from helpers import splitters2
from pv_model import pvlib_poa


def slopematch_estimate_latitude_single_year(df_year, year_n, first_day, last_day):
    # creating slope to latitude models with PVlib
    model_first_mins, model_last_mins = __get_poa_slope_models_for_day_ranges(year_n, first_day, last_day, 55, 70)

    ##########################################
    ## using measurements to extract slopes ##
    ##########################################

    #splitting range from input year df
    df_year = splitters2.split_df_day_range(df_year, first_day, last_day)

    # lists of first and last non-zero minutes from real measurements
    first_minute_list, last_minute_list, day_n_list = __df_get_first_last_minutes_year(df_year)

    #print("first and last minute lists ID1")
    #print(first_minute_list)
    #print(last_minute_list)
    first_minutes_model = numpy.polynomial.polynomial.polyfit(day_n_list, first_minute_list, 1)
    last_minutes_model = numpy.polynomial.polynomial.polyfit(day_n_list, last_minute_list, 1)

    ###############################################################
    ## Using slopes from real measurements to estimate latitudes ##
    ###############################################################

    # input of 3rd degree poly function is the 3rd degree poly model and slope from line fit
    latitude_firsts = __3rd_degree_poly_at_x(model_first_mins, first_minutes_model[1])
    latitude_lasts = __3rd_degree_poly_at_x(model_last_mins, last_minutes_model[1])

    return latitude_firsts, latitude_lasts


def slopematch_estimate_latitude_multi_year(df_data, first_day, last_day):
    grouped = df_data.groupby('year')

    latitudes1 = []
    latitudes2 = []
    years = []
    for year_n, year_df in grouped:
        lat1, lat2 = slopematch_estimate_latitude_single_year(year_df, year_n, first_day, last_day)
        latitudes1.append(round(lat1, 4))
        latitudes2.append(round(lat2, 4))
        years.append(year_n)

    return latitudes1, latitudes2, years


def __get_poa_slope_models_for_day_ranges(year, first_day, last_day, latitude_low, latitude_high):
    """
    returns 3rd degree polynomial models, the input of which should be the measured slope,

    :param year: year to generate model for
    :param first_day: first day in day range, 250 recommended
    :param last_day: last day in day range, 300 recommended
    :param latitude_low:
    :param latitude_high:
    :return:
    """

    slopes_firsts = []
    slopes_lasts = []

    latitudes = []

    for latitude in range(latitude_low, latitude_high + 1):
        fmins = []
        days = []
        lmins = []
        for d in range(first_day, last_day + 1, 10):
            fmin, lmin = pvlib_poa.get_first_and_last_nonzero_minute(latitude, 0, year, d)
            if fmin is None or lmin is None:
                continue
            fmins.append(fmin)
            lmins.append(lmin)
            days.append(d)

        if len(days) < 4:
            continue

        first_minutes_model = numpy.polynomial.polynomial.polyfit(days, fmins, 1)
        last_minutes_model = numpy.polynomial.polynomial.polyfit(days, lmins, 1)
        slopes_firsts.append(first_minutes_model[1])
        slopes_lasts.append(last_minutes_model[1])
        latitudes.append(latitude)

    first_model = numpy.polynomial.polynomial.polyfit(slopes_firsts, latitudes, 3)
    last_model = numpy.polynomial.polynomial.polyfit(slopes_lasts, latitudes, 3)
    return first_model, last_model


def __df_get_first_last_minutes_year(df_year):
    """
    Breaks year into days and gets the per day first non-zero power minute with another function
    :param df_year: one year of power measurements
    :return: (fist_minute_list, last_minute_list, day_n_list)
    """

    first_minute_list = []
    last_minute_list = []
    day_n_list = []

    grouped = df_year.groupby('day')
    for day_n, day_df in grouped:
        fmin, lmin = __df_get_first_last_minutes_day(day_df)
        if lmin is not None:
            first_minute_list.append(fmin)
            last_minute_list.append(lmin)
            day_n_list.append(day_n)

    return first_minute_list, last_minute_list, day_n_list


def __df_get_first_last_minutes_day(df_day):
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


def __3rd_degree_poly_at_x(poly, x):
    """
    :param poly: polynomial model from numpy.polynomial.polynomial.polyfit, 3rd degree or higher
    :param x: intended to be slope angle
    :return: intended to return estimated latitude
    """
    # uncommenting this line prints the equations to terminal
    #print(str(round(poly[0],3)) + " + " + str(round(poly[1],3)) + "x + " + str(round(poly[2],3)) + "x^2 +"+ str(round(poly[3],3)) + "x^3")
    return poly[0] + poly[1] * x + poly[2] * (x ** 2) + poly[3] * (x ** 3)
