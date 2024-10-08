import matplotlib
import pandas
import pandas as pd

from helpers import splitters2, config, multiplier_matcher, cloud_free_day_finder, solar_power_data_loader2
from estimators import angler
from pv_model import pvlib_poa
from estimators import geoguesser_longitude
from matplotlib.patches import Patch



def compare_cloudfree_to_cloudy_day():
    """
    This plots 2 days from the dataset, a cloudfree day and a hand chosen cloudy day
    """

    data = solar_power_data_loader2.load_helsinki_csv()
    year_n = 2019

    data_year = splitters2.split_df_year(data, year_n)

    cloud_free_days = cloud_free_day_finder.find_smooth_days_df(data_year, 156, 157, 0.5)

    cloudy_day_number = 153

    single_cloudy_day = splitters2.split_df_day_range(data_year, cloudy_day_number, cloudy_day_number)

    single_cloudy_day  = single_cloudy_day[single_cloudy_day['output'] > 0]

    single_cloudfree_day = cloud_free_days[0]

    plot1_label = "Day: " + str(cloudy_day_number)
    plot2_label = "Day: " + str(single_cloudfree_day["day"].values[0])

    # Create a figure and two subplots sharing the same y-axis
    fig, (ax1, ax2) = matplotlib.pyplot.subplots(1, 2, sharey=True, figsize=(10, 5))

    # Plot data on the first subplot
    ax1.scatter(single_cloudy_day["minute"], single_cloudy_day["output"],  color=config.ORANGE, s=1)
    ax1.set_title(plot1_label)
    ax1.set_xlabel('Minute')
    ax1.set_ylabel('Power(W)')

    # Plot data on the second subplot
    ax2.scatter(single_cloudfree_day["minute"], single_cloudfree_day["output"], color=config.ORANGE, s=1)
    ax2.set_title(plot2_label)
    ax2.set_xlabel('Minute')

    # Adjust the layout to prevent overlap
    matplotlib.pyplot.tight_layout()

    pos1 = ax1.get_position()  # Get the original position of ax1
    pos2 = ax2.get_position()  # Get the original position of ax2

    ax1.set_position([pos1.x0, pos1.y0, pos1.width * 1.05, pos1.height])  # Adjust ax1 position
    ax2.set_position([pos1.x0 + pos1.width * 1.05, pos2.y0, pos2.width * 1.0, pos2.height])  # Adjust ax2 position

    # Display the plot
    matplotlib.pyplot.show()

compare_cloudfree_to_cloudy_day()


def plot_poa_for_different_latitudes():

    year_n = 2024
    lon = config.longitude_helsinki

    colors = ['red', 'orange', 'yellow', 'green', "blue" ,'purple']
    labels = []
    plot_index = 0

    for lat in range(20, 80, 10):
        firsts = []
        lasts = []
        days = []
        minutes_all = []
        days_double = []
        for day_n in range(1, 365,1):
            first, last = pvlib_poa.get_first_and_last_nonzero_minute(lat, lon, year_n, day_n)

            if first is not None and last is not None:
                firsts.append(first)
                lasts.append(last)
                days.append(day_n)
                minutes_all.append(first)
                minutes_all.append(last)
                days_double.append(day_n)
                days_double.append(day_n)

        labels.append(str(lat) + " degrees latitude")
        matplotlib.pyplot.scatter(days_double, minutes_all, s=1, c=colors[plot_index])
        plot_index +=1

    color_patches = [Patch(facecolor=color, edgecolor='black', label=label) for color, label in zip(colors, labels)]
    matplotlib.pyplot.legend(handles=color_patches, loc='center')
    #matplotlib.pyplot.title("First and last minutes at different latitudes")
    matplotlib.pyplot.ylabel("Minute")
    matplotlib.pyplot.xlabel("Day")
    matplotlib.pyplot.show()


#plot_poa_for_different_latitudes()



def compare_poa_to_measurements_multi_day():
    data = solar_power_data_loader2.load_helsinki_csv()
    year_n = 2019

    data_year = splitters2.split_df_year(data, year_n)

    poa_first_mins = []
    poa_last_mins = []
    mea_first_mins = []
    mea_last_mins = []
    days = []

    for day_n in range(150, 200):
        data_day = splitters2.split_df_day_range(data_year, day_n, day_n)
        poa = pvlib_poa.get_irradiance(year_n, day_n, config.latitude_helsinki, config.longitude_helsinki, 15, 135)

        poa = poa[poa['POA'] != 0.0]
        data_day = data_day[data_day['output'] != 0.0]
        poa = poa[poa['POA'] != 0.0]
        data_day = data_day[data_day['output'] != 0.0]

        poa_fmin, poa_lmin = geoguesser_longitude.__df_get_first_last_minutes_poa(poa)
        mea_fmin, mea_lmin = geoguesser_longitude.__df_get_first_last_minutes(data_day)
        poa_first_mins.append(poa_fmin)
        poa_last_mins.append(poa_lmin)
        mea_first_mins.append(mea_fmin)
        mea_last_mins.append(mea_lmin)
        days.append(day_n)

    # creating statistics df from results
    statistics_df = pd.DataFrame(
        {
            "day": days,
            'poa_first_min': poa_first_mins,
            'poa_last_min': poa_last_mins,
            'mea_first_min': mea_first_mins,
            'mea_last_min': mea_last_mins,
        }
    )

    statistics_df["poa_solar_noon"] = (statistics_df["poa_first_min"] + statistics_df["poa_last_min"])/2
    statistics_df["mea_solar_noon"] = (statistics_df["mea_first_min"] + statistics_df["mea_last_min"]) / 2

    poa_solar_noon_avg = statistics_df["poa_solar_noon"].mean()
    mea_solar_noon_avg = statistics_df["mea_solar_noon"].mean()

    print("Printing statistics")
    print("Average poa solar noon: " + str(poa_solar_noon_avg) + " mea solar noon: " + str(mea_solar_noon_avg))

    est_longitude = geoguesser_longitude.longitude_from_solar_date_solar_noon(year_n, day_n, mea_solar_noon_avg)

    print("Estimated longitude: " + str(est_longitude))



    # POA PLOTS
    matplotlib.pyplot.scatter(days, poa_first_mins, c=config.PURPLE)
    matplotlib.pyplot.scatter(days, poa_last_mins, c=config.PURPLE)

    matplotlib.pyplot.scatter(days, mea_first_mins, c=config.ORANGE)
    matplotlib.pyplot.scatter(days, mea_last_mins, c=config.ORANGE)

    matplotlib.pyplot.xlabel("Day")
    matplotlib.pyplot.ylabel("Minute")

    matplotlib.pyplot.show()

#compare_poa_to_measurements_multi_day()


def compare_poa_to_measurements_single_day():
    """
    Compares the POA simulation to a single day of measurements.
    """

    data = solar_power_data_loader2.load_helsinki_csv()

    year_n = 2019
    day_n = 220

    data_year = splitters2.split_df_year(data, year_n)
    data_day = splitters2.split_df_day_range(data_year, day_n, day_n)

    poa = pvlib_poa.get_irradiance(year_n, day_n, config.latitude_helsinki, config.longitude_helsinki, 15,135)

    poa = poa[poa['POA'] != 0.0]
    data_day = data_day[data_day['output'] != 0.0]


    poa_fmin, poa_lmin = geoguesser_longitude.__df_get_first_last_minutes_poa(poa)
    mea_fmin, mea_lmin = geoguesser_longitude.__df_get_first_last_minutes(data_day)

    poa_solar_noon = (poa_fmin+poa_lmin)/2.0
    mea_solar_noon = (mea_lmin+mea_fmin)/2.0

    # POA PLOTS
    matplotlib.pyplot.plot(poa["minute"], poa["POA"], c=config.PURPLE, label="Simulated")
    matplotlib.pyplot.scatter([poa_fmin, poa_lmin], [0, 0], c=config.PURPLE)
    matplotlib.pyplot.scatter(poa_solar_noon, 0, c=config.PURPLE)

    # measurement plots
    matplotlib.pyplot.scatter([mea_fmin, mea_lmin], [0,0], c=config.ORANGE)
    matplotlib.pyplot.plot(data_day["minute"], data_day["output"], c=config.ORANGE, label="Measured")
    matplotlib.pyplot.scatter(mea_solar_noon, 0, c=config.ORANGE)

    print("Poa solar noon: " +str(poa_solar_noon))
    print("Measurements solar noon: " +str(mea_solar_noon))

    matplotlib.pyplot.show()

#compare_poa_to_measurements_single_day()
def compare_poa_to_improved_sim(year, clearday):
    year_n = year
    tilt = config.tilt_helsinki
    azimuth = config.azimuth_helsinki
    latitude = config.latitude_helsinki
    longitude = config.longitude_helsinki

    # loading measurement data and selecting clear day
    data = solar_power_data_loader2.load_helsinki_csv()
    year_data = splitters2.split_df_year(data, year_n)
    clear_days = cloud_free_day_finder.find_smooth_days_df(year_data, 70, 250, 1)

    if clearday > len(clear_days) - 1:
        return None, None

    day = clear_days[clearday]
    # 208 and 104 for day 0
    # 207 and 111 for day 1
    # 156 and 138 for day 2
    # 220 and 103 for day 3
    # 190 and 101 for day 4

    # clear day xa
    #day = day.dropna(dim="minute")

    # day number for clear day
    day_n = day["day"].values[0]

    # minutes and powers from installation
    powers_installation = day["output"]
    minutes_installation = day["minute"]

    # placeholder rated power
    rated_power = 1

    # regular poa simulation for installation
    poa_installation = pvlib_poa.get_irradiance(year_n, day_n, latitude, longitude, tilt, azimuth)
    minutes_simulated_installation = poa_installation.minute.values
    powers_simulated_installation = poa_installation.POA.values * rated_power

    # complex physically accurate simulation for installation
    poa_accurate = pvlib_poa.pvlib_complex(year_n, day_n, latitude, longitude, tilt, azimuth, rated_power=rated_power)

    # poa accurate value processing
    poa_accurate_minutes = poa_accurate["time"].dt.hour * 60 + poa_accurate["time"].dt.minute
    poa_accurate_power = poa_accurate["output"].values
    poa_accurate_minutes = poa_accurate_minutes[:-1]
    poa_accurate_power = poa_accurate_power[:-1]

    a_poa_multiplier = multiplier_matcher.match_x1_to_x2(poa_accurate_power, powers_installation)
    poa_multiplier = multiplier_matcher.match_x1_to_x2(powers_simulated_installation, powers_installation)

    print("Multipliers for multiplier matching")
    print(a_poa_multiplier)
    print(poa_multiplier)

    # creating dicts and dataframes from multiplier matched power curves
    poa_accurate_power = poa_accurate_power * a_poa_multiplier
    powers_simulated_installation = powers_simulated_installation * poa_multiplier

    dict_poa_a = {'minute': poa_accurate_minutes, 'power_complex': poa_accurate_power}
    df_poa_a = pandas.DataFrame(dict_poa_a)

    dict_poa = {'minute': minutes_simulated_installation, 'power_simulated': powers_simulated_installation}
    df_poa = pandas.DataFrame(dict_poa)

    dict_measurements = {'minute': minutes_installation, 'power_measured': powers_installation}
    df_measurements = pandas.DataFrame(dict_measurements)

    df_curves = pandas.merge(df_measurements, df_poa_a, on="minute", how="outer")
    df_curves = pandas.merge(df_curves, df_poa, on="minute", how="outer")
    df_curves = df_curves[df_curves['minute'] > 50].iloc[:, :]
    df_curves = df_curves[df_curves['minute'] < 1200].iloc[:, :]
    #df_curves = df_curves.dropna()

    df_curves = df_curves.fillna(0)

    df_curves["simulated_error"] = df_curves["power_simulated"] - df_curves["power_measured"]
    df_curves["complex_error"] = df_curves["power_complex"] - df_curves["power_measured"]

    df_curves["simulated_error"] = abs(df_curves["simulated_error"])
    df_curves["complex_error"] = abs(df_curves["complex_error"])

    simulated_error_sum = sum(df_curves["simulated_error"])
    complex_error_sum = sum(df_curves["complex_error"])

    poa_error = simulated_error_sum / 1440
    complex_error = complex_error_sum / 1440
    print(poa_error)
    print(complex_error)

    # print(df_curves)

    # uncomment for plotting
    matplotlib.rcParams.update({'font.size': 16})
    # plotting curves
    matplotlib.pyplot.plot(df_curves["minute"], df_curves["power_simulated"], c=config.PURPLE)
    matplotlib.pyplot.plot(df_curves["minute"], df_curves["power_complex"], c=config.ORANGE)
    matplotlib.pyplot.plot(df_curves["minute"], df_curves["power_measured"], c="black")

    # plotting other features
    matplotlib.pyplot.xlabel("Minute")
    matplotlib.pyplot.ylabel("Power")
    matplotlib.pyplot.title("Day " + str(day_n))
    matplotlib.pyplot.show()

    return poa_error, complex_error

#compare_poa_to_improved_sim(2019, 2)




#solve_panel_anles_single_day_iterative()

def test_new_point_generation():

    x= 0.2
    y =0.2


    for _ in range(5):
        print("xy:" + str(round(x, 2))+ " - " + str(round(y, 2)))
        tilt, azimuth = angler.unit_circle_point_to_tilt_azimuth(x, y)
        print("tilt:" + str(round(tilt, 2)) + " - " + str(round(azimuth, 2)))

        y += 0.1


#test_new_point_generation()

def test_model_fitting():
    year_n = 2019

    data = solar_power_data_loader2.load_helsinki_csv()
    data = splitters2.split_df_year(data, year_n)
    data = splitters2.split_df_day_range(data, 120, 200)

    clear_days = cloud_free_day_finder.find_smooth_days_df(data, 120, 200, 1.0)

    # single clear day
    clear_day = clear_days[0]
    day_n = clear_day["day"].values[0]
    print("selected day number: " + str(day_n))

    angler.test_single_pair_of_angles_improved(clear_day, config.latitude, config.longitude, 90, 135)


#test_model_fitting()



def compare_simulation_multiday():
    #There were 22 days in the comparison.
    #Average error for POA was 243.81718421332442
    #Average error for complex model was 144.5552824230795
    #[447.3674107999009, 262.65370522807797, 249.9538079581001, 234.0073662825604, 222.8880313761473, 282.0503794245285, 243.3132427944721, 260.821991581006, 272.6448474858243, 270.41467635818145, 207.94168966868548, 207.19207422347486, 156.74758761286392, 220.6325687563472, 190.2666849485733, 227.42592286318907, 193.13221021410723, 290.4059081572246, 200.95609872247186, 268.48544504064546, 214.65309458805675, 240.02330860869827]
    #[438.0275214458236, 121.82893245483794, 124.21679523155477, 162.6865679611049, 123.38503731051054, 146.15542455591077, 257.9707062518125, 123.44095589051176, 227.97166893694714, 169.39203427888995, 104.08058969410932, 110.77902751183491, 138.1474339242247, 102.57660070273533, 101.2619445957287, 119.43707931489395, 111.10297060966876, 154.22800918875896, 91.76985068770932, 69.90117207170347, 98.05086319826644, 83.80502749021004]

    #There were 42 days in the comparison.
    #Average error for POA was 486.69244019151716
    #Average error for complex model was 320.059851406965
    #[512.5148540243098, 492.07588404560795, 523.8768505055458, 497.36191784498993, 475.6265197917338, 468.5223167648421, 436.0969991250037, 451.96036228934776, 443.99408709296944, 587.2335910322982, 495.3795865551867, 488.84535518031635, 515.7620232747649, 478.1848434267206, 508.1011981648827, 478.67599113865515, 482.1390019694032, 431.3554925561996, 479.61520193830404, 464.5057988283408, 418.77331773803576, 428.9527983371596, 456.88685252437307, 333.9263799208392, 477.91276043976757, 423.00493039864887, 1562.9758669138653, 365.1315200303449, 383.36326220186106, 399.7315675083835, 355.91582412519847, 451.79853971373797, 484.6861040672027, 306.1217315810861, 619.1131484827503, 594.4663488736946, 499.4174583871716, 559.7816242759945, 459.36106918514594, 469.55058630835725, 343.2199055419859, 335.1630159386986]
    #[314.73811863302274, 307.6058824362536, 320.51340340328863, 292.3199509227711, 250.61356252179615, 277.80205076769136, 255.96272354073864, 272.06776065789285, 295.43662156438296, 423.10815468728146, 338.3035827018957, 364.3794579471111, 335.73326670827623, 285.2005708241078, 303.42722298909666, 283.7527839639252, 309.64274333360197, 263.11149641348413, 284.5001871832037, 295.27630046868825, 255.01938670476432, 256.6561317138862, 290.89202689961513, 233.2459077097805, 349.38487939382077, 281.72108918740463, 1524.5475111998808, 215.72506577989773, 228.57719061492497, 254.39625312354607, 242.87000305083072, 232.09816499693176, 329.5470457838128, 188.91745791578563, 468.8524344065826, 428.08433923930465, 297.2653469903228, 352.15985806818355, 256.92832542426856, 267.0636847427492, 192.92778013573385, 222.13803434198925]
    poa_errors = []
    complex_errors = []

    for year in range(2017, 2021):
        for day in range(0, 20):
            p_error, c_error = compare_poa_to_improved_sim(year=year, clearday=day)
            if p_error is not None:
                poa_errors.append(p_error)
                complex_errors.append(c_error)

    print("There were " + str(len(poa_errors)) + " days in the comparison.")
    print("Average error for POA was " + str(sum(poa_errors) / len(poa_errors)))
    print("Average error for complex model was " + str(sum(complex_errors) / len(complex_errors)))

    print(poa_errors)
    print(complex_errors)

#compare_poa_to_improved_sim(2018, 3)

#compare_simulation_multiday()
