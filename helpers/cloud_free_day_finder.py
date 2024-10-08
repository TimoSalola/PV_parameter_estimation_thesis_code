import math

import matplotlib.pyplot
import numpy
import numpy.fft as fft


from helpers import splitters2

matplotlib.rc('font', **{'family': 'serif', 'serif': ['Computer Modern']})
matplotlib.rc('text', usetex=True)


def find_smooth_days_df(year_df, day_start, day_end, threshold_percent):
    ######################################################################################################
    ### Returns a list of dataframes each of which is a single day from year_df where smoothness after ###
    ### low pass filtering is good                                                                     ###
    ######################################################################################################

    df = splitters2.split_df_day_range(year_df, day_start, day_end)

    smooth_days = []

    for day in df['day'].unique():
        day_df = splitters2.split_df_day_range(df, day, day)

        day_df = day_df.where(day_df.output >= 0.001)
        day_df = day_df.dropna()
        day_df = splitters2.__remove_nonint_dates(day_df)

        day_smoothness = __day_df_smoothness_value(day_df)

        if day_smoothness * 100 <= threshold_percent:
            smooth_days.append(day_df)

    return smooth_days


def __day_df_smoothness_value(day_df):
    ###########################################################################
    ### Calculates a smoothness value for given day_df, low value is better ###
    ###########################################################################
    powers = day_df["output"].values

    # if less than 1 hour of data, return inf
    if len(powers) < 60:
        return math.inf
    powers_from_fourier = __fourier_filter(powers, 7)

    errors = abs(powers_from_fourier - powers)
    errors_sum = sum(errors)
    error_normalized = errors_sum / len(powers)
    error_normalized = error_normalized / max(powers_from_fourier)

    #print(error_normalized)
    #matplotlib.pyplot.plot(range(len(powers_from_fourier)), powers_from_fourier)
    #matplotlib.pyplot.plot(range(len(powers)), powers)
    #matplotlib.pyplot.title("Normalized error: " +str(error_normalized))
    #matplotlib.pyplot.show()

    return error_normalized


############################
#   HELPERS BELOW, ONLY CALL FROM WITHIN THIS FILE
############################


def __day_smoothness_value(day_xa):
    """
    INTERNAL METHOD
    :param day_xa: one day of real measurement data in xa format, has to have fields "minute" and "power"
    :return:  percent value which tells how much longer the distance from point to point is compared to sine/cosine
    fitted curve. Values lower than 1 can be considered good. Returns infinity if too few values in day
    """

    # no values at all, returning infinity
    if len(day_xa["power"].values[0]) == 0:
        return math.inf

    # print("Calculating smoothness value")
    # print(day_xa)
    day_xa = day_xa.dropna(dim="minute")

    # day = day_xa.day.values[0]

    # extracting x and y values
    minutes = day_xa["minute"].values
    powers = day_xa["power"].values[0][0]

    # too few values, returning inf
    if len(powers) < 10:
        return math.inf

    """
    # ALTERNATIVE DELTA MEASUREMENT METHOD, CURVE LENGTH:
    # calculating piecewise distance of measured values
    distances = 0
    for i in range(1, len(minutes)):
        last_x = minutes[i - 1]
        last_y = powers[i - 1]
        this_x = minutes[i]
        this_y = powers[i]

        # for some reason, certain minutes are read as math.inf
        # inf-inf is not well-defined, this needs to be avoided
        if last_y == math.inf or this_y == math.inf:
            continue

        x_delta = last_x-this_x
        x_power = x_delta**2
        y_delta = last_y - this_y
        y_power = y_delta ** 2

        #print("deltay : " +str(y_delta) + " = " + str(last_y) + " - " + str(this_y))
        #print("deltax : " + str(x_delta) + " = " + str(last_x) + " - " + str(this_x))

        distance = math.sqrt(x_power + y_power)
        distances += distance
    """

    # transforming powers into fourier series, removing most values and returning back into time domain
    powers_from_fourier_clean = __fourier_filter(powers, 7)

    # this normalizes error in respect to value count, single value
    errors = abs(powers_from_fourier_clean - powers)
    errors_sum = sum(errors)
    errors_normalized = errors_sum / len(powers)

    # if max of powers is 0.0, then division by 0.0 raises errors. If we check max for 0.0 and return infinity
    # our other algorithm should disregard this day completely
    if max(powers) == 0.0:
        return math.inf
    # normalizing in respect to max value and turning into percents
    errors_normalized = (errors_normalized / max(powers)) * 100
    # this line causes occasional errors, some powers lists are just zeros

    return errors_normalized


def __fourier_filter(values, saved_frequencies):
    """
    :param values: array of values
    :param saved_frequencies: how many of the longest frequencies to spare
    :return: values after shorter frequencies are removed
    """

    # FFT based low pass filter
    # Converting values to Fourier transform frequency representatives

    # values in values_fft represent the frequencies which make up the values array. Structure is as follows:
    # [constant, low, low, ... med, med .... high, high .... med, med .... low,low]
    # this means that by zeroing out most of the values in the center, only the low frequency parts can be chosen

    # zeroing out all of the frequencies higher than given input
    values_fft = fft.fft(values)
    values_fft[1+saved_frequencies:len(values) - saved_frequencies] = 0
    values_ifft = fft.ifft(values_fft).real

    return values_ifft
