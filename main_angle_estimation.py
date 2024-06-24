import math
import matplotlib
import numpy
from helpers import splitters2, config, multiplier_matcher, cloud_free_day_finder, solar_power_data_loader2
from estimators import angler
from pv_model import pvlib_poa


def solve_panel_angles_exhaustively():
    """
    This function shows how to use multiple days from multiple years to estimate pv system angles.
    """

    # choosing site and setting parameters
    site = "Kuopio"

    first_day = 120
    last_day = 250
    lattice_point_count = 10000

    # loading data and setting system parameters
    if site == "Kuopio":
        data = solar_power_data_loader2.load_kuopio_csv()
        config.latitude = config.latitude_kuopio
        config.longitude = config.longitude_kuopio
        config.tilt = config.tilt_kuopio
        config.azimuth = config.azimuth_kuopio
    elif site == "Helsinki":
        data = solar_power_data_loader2.load_helsinki_csv()
        config.latitude = config.latitude_helsinki
        config.longitude = config.longitude_helsinki
        config.tilt = config.tilt_helsinki
        config.azimuth = config.azimuth_helsinki

    # estimating installation angles for year range
    for year_n in range(2017, 2022):
        data_y = splitters2.split_df_year(data, year_n)
        data_y = splitters2.split_df_day_range(data_y, first_day, last_day)
        angler.angle_clear_days_from_df_with_n_point_fibo(data_y, config.latitude, config.longitude, 1, lattice_point_count)


#solve_panel_angles_exhaustively()

def exhaustive_search_single_day():
    ########################################################################
    ### Sample showing how to solve panel angles using exhaustive search ###
    ########################################################################

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

    # data processing
    data = splitters2.split_df_year(data, year_n)
    data = splitters2.split_df_day_range(data, first_day, last_day)

    #########################################
    ### Selecting clear day from dataset ###
    #########################################
    clear_days = cloud_free_day_finder.find_smooth_days_df(data, first_day, last_day, 0.4)

    # if the threshold was too tight, there might not be any cloud-free days in the dataset
    if len(clear_days) == 0:
        print("No clear days with chosen dataset and threshold. Quitting.")
        return

    # choosing a single day
    clear_day = clear_days[2]
    day_n = clear_day["day"].values[0]
    print("selected day number: " + str(day_n))

    ############################
    ### Solving panel angles ###
    ############################
    # solving best fit by exhaustive search
    tilt, azimuth, fit = angler.evaluate_1_day_against_n_fibo_points(clear_day, latitude, longitude, lattice_point_count)

    #####################################
    ### Printing and plotting results ###
    #####################################
    # printing best fit
    print("Best fit at tilt: " + str(round(tilt, 3)) + " azimuth: " + str(round(azimuth, 3)) + " delta: " + str(
        round(fit, 1)))

    # plotting best fit with test method
    angler.test_single_pair_of_angles_improved(clear_day, latitude, longitude, tilt, azimuth, plot=True)


#exhaustive_search_single_day()

def solve_panel_angles_multi_day_iterative():
    ###############################################################################
    ### Sample showing how to solve panel angles using multiple cloud free days ###
    ###############################################################################

    ###########################################
    ### Setting parameters and loading data ###
    ###########################################
    year_n = 2020

    # initial search distance for iterative search:
    search_distance = 0.3

    iterative_search_rounds = 30
    # initial search angle for iterative seach:
    center_tilt = 60
    center_azimuth = 270
    first_day = 120
    last_day = 250

    site = "Kuopio"

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


    data = splitters2.split_df_year(data, year_n)
    data = splitters2.split_df_day_range(data, first_day, last_day)

    #########################################
    ### Selecting clear days from dataset ###
    #########################################

    clear_days = cloud_free_day_finder.find_smooth_days_df(data, first_day, last_day, 1.5)

    ##########################
    ### Creating base plot ###
    ##########################
    f = matplotlib.pyplot.figure(figsize=(13, 8))
    global polar_ax
    polar_ax = matplotlib.pyplot.subplot(111, projection='polar')
    # setting zero at clock 12 and rotation as clockwise
    polar_ax.set_theta_zero_location("N")
    polar_ax.set_theta_direction(-1)
    polar_ax.set_xlim([0.0, 2 * math.pi])  # angle limit from 0 to 2pi
    polar_ax.set_ylim([0.0, 90.0])  # distance limit to 0 to 90 degrees

    ###############################################
    ### Iterative search loop for multiple days ###
    ###############################################

    # per day results
    found_tilts = []
    found_azimuths = []
    found_fitnesses = []

    # looping each day
    for clear_day in clear_days:
        day_n = clear_day["day"].values[0]
        print("selected day is year:" + str(year_n) + " day: " + str(day_n))

        center_fit = angler.test_single_pair_of_angles_improved(clear_day, config.latitude, config.longitude,
                                                                center_tilt,
                                                                center_azimuth)
        # initial distance:
        distance = search_distance

        # how many cross pattern searches to use per day
        for i in range(iterative_search_rounds):
            center_x, center_y = angler.tilt_azimuth_to_unit_circle_point(center_tilt, center_azimuth)

            tilts, azimuths = angler.points_around_center_x_y_in_tilt_azimuth(center_x, center_y, distance)
            #polar_ax.scatter(numpy.radians(azimuths), tilts, marker="o", color="grey", alpha=0.5, s=300 * distance)

            new_tilt, new_azimuth, new_fit = angler.get_best_from_tilt_azimuth_list(clear_day, latitude, longitude,
                                                                                    tilts,
                                                                                    azimuths)

            if new_fit < center_fit:
                center_tilt = new_tilt
                center_azimuth = new_azimuth
                center_fit = new_fit
            else:
                # polar_ax.scatter(numpy.radians(center_azimuth), center_tilt, marker="o", facecolors='none', edgecolors='blue', s=600*distance, alpha=1)
                distance = distance / 2

        found_tilts.append(center_tilt)
        found_azimuths.append(center_azimuth)
        found_fitnesses.append(center_fit)
        print("Last best" + str(round(center_tilt, 4)) + " " + str(round(center_azimuth, 4)))
        print("CAD: " + str(
            round(angler.angular_distance_between_points(center_tilt, center_azimuth, config.tilt, config.azimuth), 4)))
        # polar_ax.scatter(numpy.radians(center_azimuth), center_tilt, marker="o", color=config.PURPLE,s=50)

        print("Last distance: " + str(distance))

    ########################
    ### Plotting results ###
    ########################
    polar_ax.scatter(numpy.radians(found_azimuths), found_tilts, marker="o", color=config.PURPLE, s=50,
                     label="Discovered best fits")
    polar_ax.scatter(numpy.radians(known_azimuth), known_tilt, marker="o", color=config.ORANGE, s=50,
                     label="Known angles")

    #####################
    ### Printing data ###
    #####################
    print("Cluster parameters:")
    average_tilt = sum(found_tilts) / len(found_tilts)
    average_azimuth = sum(found_azimuths) / len(found_azimuths)
    print("Average tilt: " + str(round(average_tilt, 3)) + " azimuth: " + str(round(average_azimuth, 3)))
    print("Fitness: " + str(round(sum(found_fitnesses) / len(found_fitnesses), 4)))
    print("Cluster CAD: " + str(
        round(angler.angular_distance_between_points(known_tilt, known_azimuth, average_tilt, average_azimuth), 3)
    ))
    # showing plot
    matplotlib.pyplot.legend()
    matplotlib.pyplot.show()


def solve_panel_angles_single_day_iterative():
    year_n = 2019

    ###########################################
    ### loading data and setting parameters ###
    ###########################################
    site = "Kuopio"

    # day interval for iterative search:
    first_day = 120
    last_day = 250

    # starting angles for iterative search:
    center_tilt = 60
    center_azimuth = 270

    # Iterative search round count:
    iterative_search_rounds = 30

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


    data = splitters2.split_df_year(data, year_n)
    data = splitters2.split_df_day_range(data, first_day, last_day)

    clear_days = cloud_free_day_finder.find_smooth_days_df(data, first_day, last_day, 1.0)

    # single clear day
    clear_day = clear_days[0]
    day_n = clear_day["day"].values[0]
    print("selected day is year:" + str(year_n) + " day: " + str(day_n))

    ##########################
    ### creating base plot ###
    ##########################

    f = matplotlib.pyplot.figure(figsize=(13, 8))
    global polar_ax
    polar_ax = matplotlib.pyplot.subplot(111, projection='polar')
    # setting zero at clock 12 and rotation as clockwise
    polar_ax.set_theta_zero_location("N")
    polar_ax.set_theta_direction(-1)
    polar_ax.set_xlim([0.0, 2 * math.pi])  # angle limit from 0 to 2pi
    polar_ax.set_ylim([0.0, 90.0])  # distance limit to 0 to 90 degrees

    ###############################
    ### plotting starting point ###
    ###############################


    center_fit = angler.test_single_pair_of_angles_improved(clear_day, config.latitude, config.longitude, center_tilt,
                                                            center_azimuth)
    polar_ax.text(numpy.radians(center_azimuth), center_tilt, "Start")

    #############################
    ### Iterative search loop ###
    #############################
    distance = 0.3  # this is the search distance
    polar_ax.scatter(numpy.radians(center_azimuth), center_tilt, marker="o", facecolors='none', edgecolors='blue',
                     s=500 * distance)

    for i in range(iterative_search_rounds):
        center_x, center_y = angler.tilt_azimuth_to_unit_circle_point(center_tilt, center_azimuth)

        tilts, azimuths = angler.points_around_center_x_y_in_tilt_azimuth(center_x, center_y, distance)
        polar_ax.scatter(numpy.radians(azimuths), tilts, marker="o", color="grey", alpha=0.5, s=300 * distance)

        new_tilt, new_azimuth, new_fit = angler.get_best_from_tilt_azimuth_list(clear_day, latitude, longitude, tilts,
                                                                                azimuths)

        if new_fit < center_fit:
            # new best fit found from 4 surrounding points
            center_tilt = new_tilt
            center_azimuth = new_azimuth
            center_fit = new_fit
            #print("found new best" + str(round(center_tilt, 4)) + " " + str(round(center_azimuth,4)))
            polar_ax.scatter(numpy.radians(center_azimuth), center_tilt, marker="o", color="black", s=500 * distance,
                             alpha=0.5)
            polar_ax.text(numpy.radians(center_azimuth), center_tilt, str(i + 1))
        else:
            # no new best found, decreasing distance
            #polar_ax.scatter(numpy.radians(center_azimuth), center_tilt, marker="o", facecolors='none', edgecolors='blue', s=600*distance, alpha=1)
            print("no new found, decreasing distance")
            distance = distance / 2

    ###################################################################
    ### Iterative search is over, printing results and showing plot ###
    ###################################################################
    print("Last best" + str(round(center_tilt, 4)) + " " + str(round(center_azimuth, 4)))
    print("CAD: " + str(
        round(angler.angular_distance_between_points(center_tilt, center_azimuth, config.tilt, config.azimuth), 4)))
    polar_ax.scatter(numpy.radians(center_azimuth), center_tilt, marker="o", facecolors='none', edgecolors='red',
                     s=500 * distance)

    print("Last distance: " + str(distance))

    # showing plot
    matplotlib.pyplot.show()


def plot_two_results_and_cloudfree():
    #####################################################################
    ### Solving panel angles with 2 methods, iterative and exhaustive ###
    ### Plotting results next to simulation with known angles         ###
    #####################################################################

    ###########################################
    ### Setting parameters and loading data ###
    ###########################################
    year_n = 2019
    site = "Kuopio"

    # day range used:
    first_day = 120
    last_day = 250

    # exhaustive search point count:
    exhaustive_point_count = 100

    # iterative search initial distance:
    iterative_search_distance = 0.3

    if site == "Helsinki":
        latitude = config.latitude_helsinki
        longitude = config.longitude_helsinki
        tilt = config.tilt_helsinki
        azimuth = config.azimuth_helsinki
        data = solar_power_data_loader2.load_helsinki_csv()

    if site == "Kuopio":
        # panel parameters
        latitude = config.latitude_kuopio
        longitude = config.longitude_kuopio
        tilt = config.tilt_kuopio
        azimuth = config.azimuth_kuopio
        data = solar_power_data_loader2.load_kuopio_csv()

    data = splitters2.split_df_year(data, year_n)
    data = splitters2.split_df_day_range(data, first_day, last_day)

    ############################################
    ### Selecting one clear day from dataset ###
    ############################################
    clear_days = cloud_free_day_finder.find_smooth_days_df(data, first_day, last_day, 1.0)

    # single clear day
    clear_day = clear_days[4]
    day_n = clear_day["day"].values[0]
    print("selected day number: " + str(day_n))

    #####################################################
    ### Solving with exhaustive and iterative methods ###
    #####################################################

    # exhaustive fit angles:
    e_tilt, e_azi, e_fit = angler.evaluate_1_day_against_n_fibo_points(clear_day, latitude, longitude, exhaustive_point_count)
    # iterative fit angles:
    i_tilt, i_azi, i_fit = angler.solve_panel_angles_single_day_iterative(clear_day, latitude, longitude, iterative_search_distance)

    ###################################################
    ### Generating plots for found and known angles ###
    ###################################################
    # power output simulations:
    sim_known = pvlib_poa.pvlib_complex(year_n, day_n, latitude, longitude, tilt,
                                        azimuth)
    sim_exhaustive = pvlib_poa.pvlib_complex(year_n, day_n, latitude, longitude, e_tilt,
                                             e_azi)
    sim_iterative = pvlib_poa.pvlib_complex(year_n, day_n, latitude, longitude, i_tilt,
                                            i_azi)

    # generating multipliers to match curves in plot
    known_sim_powers = sim_known["output"]
    sim_exhaustive_powers = sim_exhaustive["output"]
    sim_iterative_powers = sim_iterative["output"]
    clear_day_powers = clear_day["output"]

    sim1_multiplier = multiplier_matcher.match_x1_to_x2(known_sim_powers, clear_day_powers)
    sim2_multiplier = multiplier_matcher.match_x1_to_x2(sim_exhaustive_powers, clear_day_powers)
    sim3_multiplier = multiplier_matcher.match_x1_to_x2(sim_iterative_powers, clear_day_powers)

    #################################################################################
    ### Plotting measurements and 3 simulations. Exhaustive, iterative and known. ###
    #################################################################################
    # plotting measured power
    matplotlib.pyplot.plot(clear_day["time"], clear_day["output"], label="Measured power")

    # plotting curves with multipliers
    matplotlib.pyplot.plot(sim_known["time"], sim_known["output"] * sim1_multiplier, color="black",
                           label="Known angles")
    matplotlib.pyplot.plot(sim_exhaustive["time"], sim_exhaustive["output"] * sim2_multiplier, color=config.PURPLE,
                           label="Exhaustive search")
    matplotlib.pyplot.plot(sim_iterative["time"], sim_iterative["output"] * sim3_multiplier, color=config.ORANGE,
                           label="Iterative search")

    # removing xlabels and showing plot
    matplotlib.pyplot.gca().set_xticklabels([])
    matplotlib.pyplot.legend()
    matplotlib.pyplot.show()

plot_two_results_and_cloudfree()
