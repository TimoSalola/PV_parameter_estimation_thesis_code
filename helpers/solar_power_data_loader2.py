import matplotlib
import pandas


path_helsinki = "fmi-helsinki-2021.csv"
path_kuopio = "fmi-kuopio-2021.csv"

# these variables are used to store which days were read from csv, which were accepted and which were discarded
# can be read with solar_power_data_loader.all_days_in_dataset_df etc, useful for plotting and "data quality" tests
all_days_in_dataset_df = None
discarded_days_df = None
accepted_days_df = None

def load_helsinki_csv():
    return load_csv(path_helsinki)

def load_kuopio_csv():
    return load_csv(path_kuopio)

def load_csv(path):
    df = pandas.read_csv(path, sep=";", skiprows=15, parse_dates=["prod_time"])
    df = df[['prod_time','pv_inv_out']]
    df.columns = ["time", "output"]
    df = df.dropna()
    df = __minute_format(df)
    df['time'] = pandas.to_datetime(df.time).dt.tz_localize("UTC")
    #df = df.dropna()

    return df

def __minute_format(df):
    df2 = pandas.DataFrame.copy(df, deep=True)

    df2["minute"] = df2["time"].dt.hour * 60 + df2["time"].dt.minute

    df2["year"] = df2["time"].dt.year
    df2["day"] = df2["time"].dt.strftime("%j").astype(int)

    df2 = pandas.DataFrame(df2, columns=["time", "year", "day", "minute", "output"])
    return df2


def print_last_loaded_data_visual():
    """
    Creates a plot which shows the days within last loaded dataset, days which were discarded and days which were
    accepted
    """

    matplotlib.rcParams.update({'font.size': 13})
    matplotlib.pyplot.rcParams.update({
        "text.usetex": True
    })

    print(
        "Read " + str(len(all_days_in_dataset_df)) + " from datafile. Out of these " + str(len(accepted_days_df)) + "("
        + "%.2f" % round(100 * len(accepted_days_df) / len(all_days_in_dataset_df), 2) + "%) passed set filters.")

    # plotting eventplot good days part
    for year_n in accepted_days_df["year"].unique():
        good_year_y = accepted_days_df.where(accepted_days_df["year"] == year_n)
        good_year_y = good_year_y.dropna()
        matplotlib.pyplot.eventplot(good_year_y["day"].values, lineoffsets=year_n, color=config.ORANGE)

    # plotting eventplot discarded days part
    for year_n in discarded_days_df["year"].unique():
        bad_days_y = discarded_days_df.where(discarded_days_df["year"] == year_n)
        bad_days_y = bad_days_y.dropna()
        matplotlib.pyplot.eventplot(bad_days_y["day"].values, lineoffsets=year_n, color="dimgrey")

    matplotlib.pyplot.xlabel("Day")
    matplotlib.pyplot.ylabel("Year")
    matplotlib.pyplot.title("Data quality")
    # matplotlib.pyplot.legend(["Accepted days", "Discarded days"])

    orange_patch = matplotlib.patches.Patch(color=config.ORANGE, label='Accepted days')
    grey_patch = matplotlib.patches.Patch(color="grey", label='Discarded days')
    white_patch = matplotlib.patches.Patch(color="white", label='Missing from dataset')
    matplotlib.pyplot.legend(handles=[orange_patch, grey_patch, white_patch])

    # max_year = max(all_days["year"].values)
    # min_year = min(all_days["year"].values)

    matplotlib.pyplot.ylim(min(all_days_in_dataset_df.year.values) - 0.5, max(all_days_in_dataset_df.year.values) + 0.5)
    matplotlib.pyplot.xlim(0, 365)
    matplotlib.pyplot.show()