import math
import time
import matplotlib.pyplot
import numpy
import pandas
from helpers import cloud_free_day_finder
from helpers import config
import pv_model.pvlib_poa as pvlib_poa

############################
#   FUNCTIONS FOR ESTIMATING PANEL ANGLES
#   USE find_best_multiplier_for_poa_to_match_single_day_using_integral FOR COMPUTING THE MULTIPLIER IF ANGLES ARE KNOWN
#   OTHER __FUNCTIONS ARE HELPERS, INTENDED FOR INTERNAL USE
############################


# Functions from this file are used in chapter "5 Estimating panel angles"

font = {'family': 'normal',
        'weight': 'bold',
        'size': 22}

matplotlib.rc('font', **font)


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


def test_single_pair_of_angles_improved(day_df, latitude, longitude, tilt, azimuth, plot=False):
    """
    Tests a single day with known latitude and longitude, using a guessed tilt and azimuth.
    :param day_df:
    :param latitude:
    :param longitude:
    :param tilt:
    :param azimuth:
    :return: Average per minute error between day_df and simulated power output
    """

    # simulation year and day
    day_n = day_df["day"].values[0]
    year_n = day_df["year"].values[0]
    day_df = day_df[["time", "year", "day", "minute", "output"]]

    # simulation
    simulated_1kw_data = pvlib_poa.pvlib_complex(year_n, day_n, latitude, longitude, tilt, azimuth)

    # matching multipliers ###########################
    # columns in simulated 1kw data:['time', 'ghi', 'dni', 'dhi', 'dni_poa', 'dhi_poa', 'ghi_poa', 'poa', 'dni_rc',
    # 'dhi_rc', 'ghi_rc','poa_ref_cor', 'T', 'wind', 'module_temp', 'output']

    start_time = time.time()
    simulated_power_sum = sum(simulated_1kw_data.output.values)

    measured_powers = day_df["output"].values  # includes nan
    measured_powers = measured_powers[~numpy.isnan(measured_powers)]  # nan removed
    measured_power_sum = sum(measured_powers)
    ratio = measured_power_sum / simulated_power_sum
    simulated_1kw_data["output"] = simulated_1kw_data["output"] * ratio

    # removing zero powers from measurement data from measurement data
    simulated_1kw_data = simulated_1kw_data.where(simulated_1kw_data.output >= 0.001)
    simulated_1kw_data = simulated_1kw_data.dropna()

    # cleaning up simulated data
    simulated_1kw_data = simulated_1kw_data[["time", "output"]]

    # merging simulated powers to known power df
    merged = pandas.merge(day_df, simulated_1kw_data, on='time', how='outer')

    merged["output_x"] = merged["output_x"].fillna(0)
    merged["output_y"] = merged["output_y"].fillna(0)

    # computing delta value
    # equation = sum(abs(measured-simulated))/1440
    merged["output_delta"] = (merged["output_x"] - merged["output_y"]).abs()
    delta_values = merged["output_delta"].values
    delta_avg = sum(delta_values) / 1440
    delta_norm = delta_avg

    if plot:
        matplotlib.pyplot.plot(merged["minute"], merged["output_x"], label="Measured power")
        matplotlib.pyplot.plot(merged["minute"], merged["output_y"], label="Simulated power")
        matplotlib.pyplot.plot(merged["minute"], merged["output_delta"], label="Absolute delta")
        #matplotlib.pyplot.xticks(False)
        matplotlib.pyplot.legend()
        matplotlib.pyplot.title("Average delta: " + str(round(delta_norm, 2)) + "W")
        matplotlib.pyplot.show()

    return delta_norm


def get_best_from_tilt_azimuth_list(df, latitude, longitude, tilts, azimuths):
    """
    :param df:
    :param latitude:
    :param longitude:
    :param tilts:
    :param azimuths:
    :return: tilt deg, azimuth deg, fit watts
    """

    best_fit = math.inf
    best_tilt = None
    best_azimuth = None
    found_new_best = False

    for i in range(len(tilts)):
        tilt = tilts[i]
        azimuth = azimuths[i]
        fitness = test_single_pair_of_angles_improved(df, latitude, longitude, tilt, azimuth)
        # print("got fitness " +str(round(fitness, 4)))

        if fitness < best_fit:
            # print("new best at subspace point: " + str(round(tilt, 4)) + " | "+ str(round(azimuth,4)))
            best_fit = fitness
            best_tilt = tilt
            best_azimuth = azimuth
            found_new_best = True

    return best_tilt, best_azimuth, best_fit


def points_around_center_x_y_in_tilt_azimuth(x, y, distance):
    """
    Returns
    :param x: unit circle x value
    :param y: unit circle y value
    :param distance: distance from xy point
    :return: [tilts], [azimuths] of 4 nearby points
     """

    #print("centerpoint " + str(round(x,4)) + " " + str(round(y,4)))

    tilts, azimuths = [], []

    t1, a1 = unit_circle_point_to_tilt_azimuth(x + distance, y)
    tilts.append(t1)
    azimuths.append(a1)

    t1, a1 = unit_circle_point_to_tilt_azimuth(x - distance, y)
    tilts.append(t1)
    azimuths.append(a1)

    t1, a1 = unit_circle_point_to_tilt_azimuth(x, y + distance)
    tilts.append(t1)
    azimuths.append(a1)

    t1, a1 = unit_circle_point_to_tilt_azimuth(x, y - distance)
    tilts.append(t1)
    azimuths.append(a1)

    # comment/uncomment these for enabling corner points
    """
    t1, a1 = unit_circle_point_to_tilt_azimuth(x+distance, y+distance)
    tilts.append(t1)
    azimuths.append(a1)
    t1, a1 = unit_circle_point_to_tilt_azimuth(x + distance, y - distance)
    tilts.append(t1)
    azimuths.append(a1)
    t1, a1 = unit_circle_point_to_tilt_azimuth(x - distance, y + distance)
    tilts.append(t1)
    azimuths.append(a1)
    t1, a1 = unit_circle_point_to_tilt_azimuth(x - distance, y - distance)
    tilts.append(t1)
    azimuths.append(a1)
    """

    # print("4 near points:")
    # print("tilts: " + str(tilts))
    # print("azimuths: " + str(azimuths))

    return tilts, azimuths


def unit_circle_point_to_tilt_azimuth(x, y):
    """
    This functions transforms a point inside unit circle to a tilt/azimuth pair
    :return [tilts], [azimuths] both in degrees
    """
    distance_from_origin = math.sqrt(x * x + y * y)
    # print("Distance from origin: " + str(round(distance_from_origin, 4)))

    if distance_from_origin == 0:
        return 0, 0
    x_n = x / distance_from_origin
    y_n = y / distance_from_origin

    azimuth = math.degrees(math.atan2(y_n, x_n))

    if azimuth < 0:
        azimuth = azimuth + 360

    if distance_from_origin > 1:
        tilt = 90
    else:
        tilt = distance_from_origin * 90

    # print("Returning tilt: " + str(round(tilt, 4))+ " azimuth:" + str(round(azimuth, 4)))
    return tilt, azimuth


def angle_clear_days_from_df_with_n_point_fibo(df, latitude, longitude, clear_day_threshold, points):
    """
    Finds the best angle fits for multiple days in given dataframe with known geolocation.
    :param df: Multi-day one year df
    :param latitude: known geolocation latitude
    :param longitude: known geolocation longitude
    :param clear_day_threshold:  smoothness coefficient, 1.0 is OK for good installations. Lower values mean higher
    smoothness required
    :param points: Fibonacci lattice point count used for exhaustive search.
    :return:
    """

    # reading year from df
    year_n = df["year"].values[0]

    # extracting clear days from dataframe which pass the required threshold
    clear_days = cloud_free_day_finder.find_smooth_days_df(df, 120, 200, clear_day_threshold)

    print("Angling using " + str(len(clear_days)) + " days from year " + str(year_n))

    # solving best fit for each of the clear days
    best_tilts = []
    best_azimuths = []
    best_fitnesses = []

    for clear_day in clear_days:
        tilt, azimuth, fitness = evaluate_1_day_against_n_fibo_points(clear_day, latitude, longitude, points)
        if tilt is not None:
            best_tilts.append(tilt)
            best_azimuths.append(azimuth)
            best_fitnesses.append(fitness)

    # calculating tilt, azimuth and fit ranges
    min_tilt = min(best_tilts)
    max_tilt = max(best_tilts)
    min_azimuth = min(best_azimuths)
    max_azimuth = max(best_azimuths)
    min_fit = min(best_fitnesses)
    max_fit = max(best_fitnesses)

    # calculating tilt, azimuth and fit averages
    average_tilt = sum(best_tilts) / len(best_tilts)
    average_azimuth = sum(best_azimuths) / len(best_azimuths)
    average_fit = sum(best_fitnesses) / len(best_fitnesses)

    # calculating delta, note that this can only be done if the installation location is known
    delta = angular_distance_between_points(average_tilt, average_azimuth, config.tilt_kuopio, config.azimuth_kuopio)
    print("average delta angle: " + str(round(delta, 3)))

    # printing averages and ranges for results
    print(
        "Average tilt:" + str(round(average_tilt, 2)) + " azimuth:" + str(round(average_azimuth, 2)) + " fitness" + str(
            round(average_fit)))
    print("Tilt range: " + str(round(min_tilt, 2)) + " to " + str(round(max_tilt, 2)))
    print("Azimuth range: " + str(round(min_azimuth, 2)) + " to " + str(round(max_azimuth, 2)))
    print("Normalized delta range: " + str(round(min_fit)) + " to " + str(round(max_fit)))

    # creating polar plot base plot
    f = matplotlib.pyplot.figure(figsize=(13, 8))
    global polar_ax
    polar_ax = matplotlib.pyplot.subplot(111, projection='polar')
    # setting zero at clock 12 and rotation as clockwise
    polar_ax.set_theta_zero_location("N")
    polar_ax.set_theta_direction(-1)
    polar_ax.set_xlim([0.0, 2 * math.pi])  # angle limit from 0 to 2pi
    polar_ax.set_ylim([0.0, 90.0])  # distance limit to 0 to 90 degrees

    # plotting fibo grid used for by evaluation algorithm
    tilts, azimuths = get_fibonacci_distribution_tilts_azimuths(points)
    scatter = polar_ax.scatter(azimuths, numpy.degrees(tilts), c="grey", alpha=0.2, marker="o", label="Lattice points")

    # plotting known installation angles, comment this out if unknown
    scatter = polar_ax.scatter(numpy.radians(config.azimuth), config.tilt, c=config.ORANGE, marker="o",
                               label="Known angles")

    # plotting found best fits for each cloud free day
    scatter = polar_ax.scatter(numpy.radians(best_azimuths), best_tilts, c=config.PURPLE, alpha=0.5, marker="o",
                               label=str(len(best_tilts)) + " best fits")

    # adding title, modify accordingly
    title_string = config.installation_name + " year: " + str(year_n) + " angle estimation using " + str(
        len(best_tilts)) + " days"
    matplotlib.pyplot.title(title_string)

    matplotlib.pyplot.legend(loc="upper left")

    # saving/showing plot
    filename = config.installation_name + str(year_n) + ".png"
    matplotlib.pyplot.savefig(filename, bbox_inches='tight')
    matplotlib.pyplot.cla()  # clearing all data from plot
    # matplotlib.pyplot.show()


def evaluate_1_day_against_n_fibo_points(clear_day, latitude, longitude, points):
    """
    Evaluating one clear day with a Fibonacci lattice of n points.
    :param clear_day : One clear day from df
    :param latitude : installation latitude in degrees
    :param longitude : installation longitude in degrees
    :param points : point count of lattice to be generated
    :return tilt, azimuth, fitness of best fit. None, None, None if errors encountered
    """

    # lattice points in radians
    tilt_angles_radian, azimuth_angles_radian = get_fibonacci_distribution_tilts_azimuths(points)

    # storing best found fit in these variables
    best_fit = math.inf
    best_fit_tilt = None
    best_fit_azimuth = None

    # evaluating all points
    for i in range(len(tilt_angles_radian)):
        # Progress printing
        if (i + 1) % 50 == 0:
            print("Evaluated " + str(i + 1) + "/" + str(len(tilt_angles_radian)) + " angle pairs.")

        # panel angles in radians and in degrees
        tilt_radian = tilt_angles_radian[i]
        azimuth_radian = azimuth_angles_radian[i]
        tilt_deg = numpy.degrees(tilt_radian)
        azimuth_deg = numpy.degrees(azimuth_radian)

        # calculating fitness
        fitness = test_single_pair_of_angles_improved(clear_day, latitude, longitude, tilt_deg, azimuth_deg)

        if fitness < best_fit:
            best_fit_tilt = tilt_deg
            best_fit_azimuth = azimuth_deg
            best_fit = fitness

    return best_fit_tilt, best_fit_azimuth, best_fit


def solve_panel_angles_single_day_iterative(clear_day, latitude, longitude, search_distance):
    year_n = clear_day["year"].values[0]
    day_n = clear_day["day"].values[0]

    print("Evaluating day year:" + str(year_n) + " day: " + str(day_n))

    # starting point coordinates
    center_tilt = 60
    center_azimuth = 270

    center_fit = test_single_pair_of_angles_improved(clear_day, config.latitude, config.longitude, center_tilt,
                                                     center_azimuth)
    distance = search_distance

    for i in range(30):
        center_x, center_y = tilt_azimuth_to_unit_circle_point(center_tilt, center_azimuth)

        tilts, azimuths = points_around_center_x_y_in_tilt_azimuth(center_x, center_y, distance)

        new_tilt, new_azimuth, new_fit = get_best_from_tilt_azimuth_list(clear_day, latitude, longitude, tilts,
                                                                         azimuths)

        if new_fit < center_fit:
            center_tilt = new_tilt
            center_azimuth = new_azimuth
            center_fit = new_fit
        else:
            print("no new found, decreasing distance")
            distance = distance / 2

    return center_tilt, center_azimuth, center_fit


############################
#   GLOBAL HELPERS
############################

def tilt_azimuth_to_unit_circle_point(tilt, azimuth):
    """
    This functions transforms a tilt azimuth pair to x-y pair
    :param tilt : Tilt in degrees
    :param azimuth : Azimuth in degrees
    :return x,y in -1 to 1 ranges
    """
    distance_from_origin = tilt / 90

    # unit circle point with the given azimuth angle
    y = math.sin(math.radians(azimuth))
    x = math.cos(math.radians(azimuth))

    # unit circle point normalization with tilt-derived distance
    y_n = distance_from_origin * y
    x_n = distance_from_origin * x

    return x_n, y_n


def get_best_fitness_out_of_results(tilt_rads, azimuth_rads, fitnesses):
    """
    Returns tilt and azimuth values for lowest fitness value
    :param tilt_rads:
    :param azimuth_rads:
    :param fitnesses:
    :return: best_azimuth, best_tilt, best_fitness
    """

    best_azimuth = 0
    best_tilt = 0
    best_fit = math.inf
    for i in range(len(tilt_rads)):
        azimuth = azimuth_rads[i]
        tilt = tilt_rads[i]
        fitness = fitnesses[i]
        if fitness < best_fit:
            best_azimuth = azimuth
            best_tilt = tilt
            best_fit = fitness

    return best_tilt, best_azimuth, best_fit


def get_fibonacci_distribution_tilts_azimuths(samples):
    """
    Returns tilt and azimuth values for the upper half of a fibonacci half sphere
    :param samples: approximate count for fibonacci half sphere points
    :return: [tilts(rad)], [azimuths(rad)], len(tilts) ~ samples
    """

    # x y and z values for matplotlib test plotting
    xvals, yvals, zvals = [], [], []

    # actual tilt and azimuth values
    phis, thetas = [], []

    # doubling sample count as negative half of sphere is not needed
    # this sould result in
    iterations = samples * 2
    for i in range(iterations):

        # using helper to get 5 values
        values = __get_fibonacci_sample(i, iterations)

        # if z is > 0, skip this loop iteration as bottom half of sphere is not needed
        if values[2] < 0:
            continue

        # add values to lists
        xvals.append(values[0])
        yvals.append(values[1])
        zvals.append(values[2])
        phis.append(values[3])
        thetas.append(values[4])

    # test plotting, shows the points in 3d space. Can be used for verification
    # fig = matplotlib.pyplot.figure()
    # ax = fig.add_subplot(projection='3d')
    # ax.scatter3D(xvals, yvals, zvals)
    # matplotlib.pyplot.show()

    # returning tilt and azimuth values
    return phis, thetas


############################
#   HELPERS BELOW, CALL ONLY FROM WITHIN THIS FILE
############################


def __get_fibonacci_sample(sample, sample_max):
    """
    :param sample: sample number when there are sample_max samples
    :param sample_max: highest sample number
    :return: x(-1,1), y(-1, 1), z(-1,1), tilt(rad) and azimuth(rad) values for a single point on a fibonacci sphere
    """

    # Code based on sample at https://medium.com/@vagnerseibert/distributing-points-on-a-sphere-6b593cc05b42

    k = sample + 0.5

    # degrees from top to bottom in radians
    phi = math.acos(1 - 2 * k / sample_max)
    # azimuth, goes super high superfast, this is why modulo is used to scale values down
    theta = math.pi * (1 + math.sqrt(5)) * k
    theta = theta % (math.pi * 2)

    x = math.cos(theta) * math.sin(phi)
    y = math.sin(theta) * math.sin(phi)
    z = math.cos(phi)

    return x, y, z, phi, theta


def angular_distance_between_points(tilt1, azimuth1, tilt2, azimuth2):
    """
    Calculates the angular distance in degrees between two points in angle space
    :param tilt1: point 1 tilt angle in degrees
    :param azimuth1: point 1 azimuth angle in degrees
    :param tilt2: point 2 tilt angle in degrees
    :param azimuth2: point 2 azimuth angle in degrees
    :return: sphere center angle between the two points
    """
    tilt1_rad = numpy.radians(tilt1)
    azimuth1_rad = numpy.radians(azimuth1)
    tilt2_rad = numpy.radians(tilt2)
    azimuth2_rad = numpy.radians(azimuth2)

    # print("Computing angular distance between two angle space points...")

    x1 = math.sin(tilt1_rad) * math.cos(azimuth1_rad)
    y1 = math.sin(tilt1_rad) * math.sin(azimuth1_rad)
    z1 = math.cos(tilt1_rad)

    # print("Point 1 x,y,z: " + str(round(x1, 2)) + " " + str(round(y1, 2)) + " " + str(round(z1,2)))

    x2 = math.sin(tilt2_rad) * math.cos(azimuth2_rad)
    y2 = math.sin(tilt2_rad) * math.sin(azimuth2_rad)
    z2 = math.cos(tilt2_rad)

    # print("Point 2 x,y,z: " + str(round(x2, 2)) + " " + str(round(y2, 2)) + " " + str(round(z2, 2)))

    euclidean_distance = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2 + (z1 - z2) ** 2)

    center_angle = numpy.degrees(math.acos((2 - euclidean_distance ** 2) / 2))

    # print("Euclidean distance was: " + str(round(euclidean_distance, 4)) + " , angle delta: " +  str(round(center_angle, 4)) + " degrees")

    return center_angle


def __get_measurement_to_poa_delta(xa_day, poa):
    """
    Returns a list of deltas and percentual deltas which can be used for analytics
    :param xa_day: one day of measurements in xarray format
    :param poa: one day of measurements in numpy dataframe
    :return: list of deltas and list of percentual deltas
    """
    # removing the lowest values and nans
    xa_day = xa_day.where(xa_day.power >= 2)
    xa_day = xa_day.dropna(dim="minute")

    # loading poa minutes and powers
    poa_powers = poa["POA"].values
    poa_minutes = poa["minute"].values

    # loading xa minutes and powers
    xa_minutes = xa_day.minute.values
    xa_powers = xa_day.power.values[0][0]

    deltas = []  # absolute value of deltas
    percent_deltas = []  # percentual values of deltas, used for normalizing the errors as 5% at peak is supposed to
    # weight as much as 5% at bottom
    minutes = []  # contains minutes for which deltas were calculated for

    # print("computing delta between measurements and poa simulation")
    # print(xa_day)
    # print(poa)

    # TODO this loop here is likely to be the main cause for angle estimation being slow
    # Replace with vectorized operations?
    for i in range(len(xa_minutes)):
        xa_minute = xa_minutes[i]  # this is poa index
        xa_power = xa_powers[i]
        poa_power = poa_powers[xa_minute]

        delta = xa_power - poa_power

        # poa power may be 0, avoiding zero divisions here
        if poa_power > 1:
            percent_delta = (delta / poa_power) * 100
        else:
            percent_delta = None
        deltas.append(delta)
        percent_deltas.append(percent_delta)
        minutes.append(xa_minute)

    return deltas, percent_deltas, minutes
