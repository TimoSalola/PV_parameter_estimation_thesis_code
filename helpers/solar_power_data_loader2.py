import pandas


path_helsinki = "fmi-helsinki-2021.csv"
path_kuopio = "fmi-kuopio-2021.csv"
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