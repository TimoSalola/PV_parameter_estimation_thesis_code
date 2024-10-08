import math
import statistics
import matplotlib
import numpy
from matplotlib import pyplot as plt
import helpers.config
from helpers import solar_power_data_loader2
from helpers import splitters2
from estimators import geoguesser_longitude, geoguesser_latitude



def estimate_longitude_v2():  # works, used in thesis
    ###############################################################
    #   This function contains an example on how to estimate geographic longitudes
    #   The method relies on geoguesser_longitude.estimate_longitude_based_on_year(year_data)
    #   Which has hardcoded geolocation for simulated solar noon time. The hardcoded values should be adjusted
    #   if the algorithm is to be used for datasets describing solar pv generation outside of Finland
    ###############################################################

    data = solar_power_data_loader2.load_helsinki_csv()

    correct_longitude = helpers.config.longitude_helsinki


    statistics_dataframes = []

    # estimating every year
    for year_n in range(2017, 2022):
        print("estimating longitude for year " + str(year_n))
        year_data = splitters2.split_df_year(data, year_n)
        year_data = splitters2.split_df_day_range(year_data, 125, 250)
        estimated_longitude = geoguesser_longitude.estimate_longitude_based_on_year_df(year_data)
        statistics_dataframes.append(estimated_longitude)

        print("Longitude median: " + str(round(estimated_longitude["longitude"].median(),4)))
        print("Longitude mean: " + str(round(estimated_longitude["longitude"].mean(),4)))
        print("Median delta: " + str(round(correct_longitude-estimated_longitude["longitude"].median(),4)))
        print("Mean delta: " + str(round(correct_longitude-estimated_longitude["longitude"].mean(),4)))


    years = []  # years
    box_data = []

    for df in statistics_dataframes:
        year_n = df["year"].values[0]
        years.append(year_n)
        box_data.append(df["longitude"])

    # adjusting font size
    font = {'size': 16}
    matplotlib.rc('font', **font)

    # Create the plot
    plt.figure(figsize=(10, 6))

    # plotting box plot
    plt.boxplot(box_data, positions=years, vert=False, showfliers=False)

    # plotting correct longitude coordinate
    plt.plot([correct_longitude,correct_longitude],[2016.5, 2021.5],c="black")
    # Add labels and title
    plt.ylabel('Year')
    plt.xlabel('Longitude')
    plt.yticks(years)

    # Add grid lines
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)

    # Display the plot
    plt.show()

    """
    These are for day range 125 to 250
    KUOPIO RESULTS:
    estimating longitude for year 2017
    Longitude median: 27.25
    Longitude mean: 26.5837
    Median delta: 0.3849
    Mean delta: 1.0512
    estimating longitude for year 2018
    Longitude median: 27.25
    Longitude mean: 26.9018
    Median delta: 0.3849
    Mean delta: 0.7331
    estimating longitude for year 2019
    Longitude median: 27.0625
    Longitude mean: 27.4484
    Median delta: 0.5724
    Mean delta: 0.1865
    estimating longitude for year 2020
    Longitude median: 27.125
    Longitude mean: 27.7391
    Median delta: 0.5099
    Mean delta: -0.1042
    estimating longitude for year 2021
    Longitude median: 27.125
    Longitude mean: 26.6925
    Median delta: 0.5099
    Mean delta: 0.9424
    
    HELSINKI RESULTS:
    estimating longitude for year 2017
    Longitude median: 25.0
    Longitude mean: 24.8859
    Median delta: -0.0375
    Mean delta: 0.0766
    estimating longitude for year 2018
    Longitude median: 25.4375
    Longitude mean: 25.2937
    Median delta: -0.475
    Mean delta: -0.3312
    estimating longitude for year 2019
    Longitude median: 25.625
    Longitude mean: 25.6219
    Median delta: -0.6625
    Mean delta: -0.6594
    estimating longitude for year 2020
    Longitude median: 25.5625
    Longitude mean: 25.0942
    Median delta: -0.6
    Mean delta: -0.1317
    estimating longitude for year 2021
    Longitude median: 25.5
    Longitude mean: 25.7665
    Median delta: -0.5375
    Mean delta: -0.804
    """


#estimate_longitude_v2()


def estimate_longitude_single_day():
    data = solar_power_data_loader2.load_helsinki_csv()

    year_n = 2019
    day_n = 176

    data_year = splitters2.split_df_year(data, year_n)
    data_day = splitters2.split_df_day_range(data_year, day_n, day_n)
    geoguesser_longitude.estimate_longitude_single_day_df(data_day)

#estimate_longitude_single_day()


def estimate_latitude_single_year():
    """
    Example of how to estimate latitude of a PV system for a single year of PV data
    :return:
    """
    data = solar_power_data_loader2.load_helsinki_csv()

    year_n = 2019

    geoguesser_latitude.slopematch_estimate_latitude_single_year(data, year_n, 190, 280)



#estimate_latitude_single_year()


def estimate_latitude_multi_year():
    #####################################################################
    ### This function estimates latitude using multiple years of data ###
    #####################################################################

    # loading data
    data = solar_power_data_loader2.load_helsinki_csv()

    # estimating latitude, getting first minute and last minute estimates
    lat1, lat2, year_n = geoguesser_latitude.slopematch_estimate_latitude_multi_year(data, 180, 310)

    print("Latitudes from first minutes:")
    print(lat1)
    print("Latitudes from last minutes:")
    print(lat2)
    print("Years used:")
    print(year_n)


    all_latitudes = lat1 + lat2

    standard_dev = statistics.pstdev(all_latitudes)
    print("Latitudes standard deviation: " + str(standard_dev))
    print("latitudes mean: " + str(statistics.mean(all_latitudes)))



estimate_latitude_multi_year()

def plot_day_interval_heatmap():

    ###################################################################################################
    ### This function creates a heatmap which displays day range to standard deviation relationship ###
    ###################################################################################################

    # helsinki = 180-310 dev: 0.3788
    data = solar_power_data_loader2.load_helsinki_csv()

    # list of tested intervals
    first_days = []
    last_days = []
    standard_deviations = []

    # best result data
    best_standard_dev = math.inf
    best_first_day = None
    best_last_day = None


    for f in range(150, 240, 10):
        # f is first day
        for l in range(40, 180, 10):
            # l is interval len
            first_day = f
            last_day = f+l

            if last_day > 350:
                continue

            print("Testing interval: " + str(first_day) +"-" + str(last_day))

            # using try-catch here because some intervals cause errors
            try:
                lat1, lat2, year_n = geoguesser_latitude.slopematch_estimate_latitude_multi_year(data, first_day, last_day)
                all_latitudes = lat1 + lat2

                standard_dev = statistics.pstdev(all_latitudes)

                first_days.append(first_day)
                last_days.append(last_day)
                standard_deviations.append(standard_dev)

                if standard_dev < best_standard_dev:
                    best_standard_dev = standard_dev
                    best_first_day = first_day
                    best_last_day = last_day
                    print("New lowest standard deviation found")
                    print(str(best_first_day) +"-" + str(best_last_day) + " dev: " + str(round(best_standard_dev,4)))
            except:
                print("Got an error for some reason, skipping this interval")

    # Convert lists to numpy arrays
    firsts = numpy.array(first_days)
    lasts = numpy.array(last_days)
    values = numpy.array(standard_deviations)

    # Plot heatmap as scatter plot
    plt.scatter(firsts, lasts, c=values, cmap='viridis', s=100, marker='s')
    plt.scatter(best_first_day, best_last_day, marker="o", s=150, color="red")

    # Add color bar
    plt.colorbar(label='Standard dev.')

    # Set labels and title
    plt.xlabel('First day')
    plt.ylabel('Last day')

    # Show plot
    plt.show()


#plot_day_interval_heatmap()