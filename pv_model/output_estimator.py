import math


def add_output_to_df(df, rated_power):
    if "poa_ref_cor" not in df.columns:
        print("column poa_ref_cor not found in dataframe, output can not be simulated")
    if "module_temp" not in df.columns:
        print("module temperature variable \"module_temp\" not found in dataframe")

    """
    Helper function, returns calculated output or zero if module temp or poa ref cor are nan
    """

    def helper_add_output(dfn):
        estimated_output = __estimate_output(dfn["poa_ref_cor"], dfn["module_temp"], rated_power)
        if math.isnan(estimated_output):
            return 0
        else:
            return estimated_output

    # applying helper function to dataset and storing result as a new column
    df["output"] = df.apply(helper_add_output, axis=1)

    return df


def __estimate_output(absorbed_radiation, panel_temp, rated_power):
    # huld et al 2010 constants
    k1 = -0.017162
    k2 = -0.040289
    k3 = -0.004681
    k4 = 0.000148
    k5 = 0.000169
    k6 = 0.000005

    # hud et al equation:

    # main equation:
    # output = rated_power*nrad*efficiency

    # Helpers:
    # nrad = absorbed_radiation/1000
    # Tdiff = module_temp-25C
    # efficiency = 1+ k1*ln(nrad)
    # + k2*ln(nrad)²
    # + Tdiff*(k3+k4*ln(nrad) + k5*ln(nrad)²)
    # + k6*Tdiff²

    nrad = absorbed_radiation / 1000.0
    # radiation can sometimes be zero or less than zero, possibly due to floating point errors
    # math.log raises math error on log(less_or_equal_to_zero) and this has to be avoided
    # if radiation is zero, panels do not generate energy, returns zero
    if nrad <= 0:
        return 0

    Tdiff = panel_temp - 25
    rated_power = rated_power * 1000.0

    base = 1
    part_k1 = k1 * math.log(nrad)
    part_k2 = k2 * (math.log(nrad) ** 2)
    part_k3k4k5 = Tdiff * (k3 + k4 * math.log(nrad) + k5 * (math.log(nrad) ** 2))
    part_k6 = k6 * (Tdiff ** 2)

    efficiency = base + part_k1 + part_k2 + part_k3k4k5 + part_k6
    efficiency = max(efficiency, 0)  # limits efficiency to be positive, if efficiency is negative, will always return 0

    output = rated_power * nrad * efficiency

    return output
