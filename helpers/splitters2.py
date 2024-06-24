def split_df_year(df, year):
    df = df.where(df.year == year)
    df = df.dropna()

    # removing non int date variables, they seem to be caused by df.where
    df = __remove_nonint_dates(df)

    return df

def split_df_day_range(df, day_start, day_end):
    df = df.where(df.day >= day_start)
    df = df.where(df.day <= day_end)
    df = df.dropna()
    df = __remove_nonint_dates(df)
    return df

def __remove_nonint_dates(df):
    df.year = df.year.astype(int)
    df.day = df.day.astype(int)
    df.minute = df.minute.astype(int)
    return df

