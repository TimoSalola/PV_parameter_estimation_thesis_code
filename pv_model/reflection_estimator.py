"""
REFLECTION FUNCTIONS

Functions for estimating how much of the solar irradiance is absorbed by solar panels in opposed to being reflected away
Equation for radiation absorbed:
Radiation_absorbed = (1-dni_reflected)DNIPOA+(1-ghi_reflected)GHIPOA + (1-diffuse_reflected)DHIPOA
dni_reflected is alpha_BN in notes
ghi_reflected is alpha_dg in notes
diffuse_reflected is alpha_d in notes
"""

import math
import numpy
from pv_model import astronomical_calculations
from helpers import config

# panel reflectance constant, empirical value. Solar panels with better optical coatings would have a lower value where
# as uncoated panels would have a higher value. Dust on panels increases reflectance_constant.
# 0.159 is given as an average value for polycrystalline silicon module reflectance
reflectance_constant = 0.159

def components_to_corrected_poa(DNI_component, DHI_component, GHI_component, dt, tilt, azimuth, latitude, longitude):
    """
    Takes dni, dhi and ghi components of a solar panel projected irradiance and computes how much of the radiation is
    absorbed by the solar panels, in opposed to reflected away.
    :param DNI_component: poa transposed dni value(W)
    :param DHI_component: poa transposed dhi value(W)
    :param GHI_component: poa transposed ghi value(W)
    :param dt: time for estimation. For example, "2023-10-13 19:30:00+00:00"
    :return: absorbed radiation in W
    """

    # direct sunlight reflection variable, has to be computed multiple times.
    dni_reflected = __dni_reflected(dt, tilt, azimuth, latitude, longitude)

    # These values do not have to be recomputed every single time as they are installation-specific, and they do not
    # even take time as an input. This could be optimized if needed.
    dhi_reflected = __dhi_reflected(tilt)
    ghi_reflected = __ghi_reflected(tilt)

    # POA_reflection_corrected or radiation absorbed by the solar panel.
    POA_reflection_corrected = ((1 - dni_reflected) * DNI_component + (1 - dhi_reflected) * DHI_component +
                                (1 - ghi_reflected) * GHI_component)

    return POA_reflection_corrected


def add_reflection_corrected_poa_to_df(df, tilt, azimuth, latitude, longitude):
    """
    Adds reflection corrected POA value to dataframe with name "poa_ref_cor"
    :param df:
    :return:
    """

    #print("Adding reflection corrected POA to dataframe")

    # helper function, new fast version
    def helper_components_to_corrected_poa_fast(dni_poa, dhi_poa, ghi_poa, time, tilt, azimuth, latitude, longitude):
        return components_to_corrected_poa(dni_poa, dhi_poa, ghi_poa, time, tilt, azimuth, latitude, longitude)


    df["poa_ref_cor"] = helper_components_to_corrected_poa_fast(df["dni_poa"], df["dhi_poa"], df["ghi_poa"], df["time"],
                                                                tilt, azimuth, latitude, longitude)

    #print("Reflection corrected POA values added.")

    return df


def add_reflection_corrected_poa_components_to_df(df, tilt, azimuth, latitude, longitude):
    def helper_add_dni_ref(dni_poa, time):
        #  (1-alpha_BN)*BTN
        dni_refl = __dni_reflected(time, tilt, azimuth, latitude, longitude)
        dni_refl_inverse = 1 - dni_refl
        dni_ref_fabs = numpy.fabs(dni_refl_inverse)
        dni_absorbed = dni_poa * dni_ref_fabs
        return dni_absorbed

    def helper_add_dhi_ref(dhi):
        # (1-alpha_d)*DT
        return math.fabs(1 - __dhi_reflected(tilt)) * dhi

    def helper_add_ghi_ref(ghi):
        # (1-alpha_dg)*DTg
        return math.fabs(1 - __ghi_reflected(tilt)) * ghi

    """
    BTN = dni_poa
    DTg = ghi_poa
    DT = dhi_poa
    """

    # fast versions:
    df["dni_rc"] = helper_add_dni_ref(df["dni_poa"], df["time"])
    df["ghi_rc"] = helper_add_ghi_ref(df["ghi_poa"])
    df["dhi_rc"] = helper_add_dhi_ref(df["dhi_poa"])

    return df


def __dni_reflected(dt, tilt, azimuth, latitude, longitude):
    """
    Computes a constant in range [0,1] which represents how much of the direct irradiance is reflected from panel
    surfaces.
    :param dt: datetime
    :return: reflected radiation in range [0,1]

    dni_reflected denoted as alpha_BN in Williams work.

    F_B_(alpha) in "Calculation of the PV modules angular losses under field conditions by means of an analytical model"
    """

    a_r = reflectance_constant  # empirical constant for polycrystalline silicon module reflectance

    AOI = astronomical_calculations.get_solar_angle_of_incidence(dt, tilt, azimuth, latitude, longitude)

    """
    # upper section of the fraction equation
    upper_fraction = math.e ** (-math.cos(numpy.radians(AOI)) / a_r) - math.e ** (-1.0 / a_r)
    # lower section of the fraction equation
    lower_fraction = 1.0 - math.e ** (-1.0 / a_r)

    # fraction or alpha_BN or dni_reflected
    dni_reflected = upper_fraction / lower_fraction
    """

    dni_reflected = (math.e ** (-numpy.cos(numpy.radians(AOI)) / a_r) - math.e ** (-1.0 / a_r)) / (
                1.0 - math.e ** (-1.0 / a_r))

    return dni_reflected


def __ghi_reflected(tilt):
    """
    Computes a constant in range [0,1] which represents how much of ground reflected irradiation is reflected away from
    solar panel surfaces. Note that this is constant for an installation.
    :return: [0,1] float, 0 no light reflected, 1 no light absorbed by panels.

    ghi reflected is denoted as alpha_d in Williams work

    F_A(beta) in "Calculation of the PV modules angular losses under field conditions by means of an analytical model"

    """

    # constants, these are from
    c1 = 4.0 / (3.0 * math.pi)

    c2 = -0.074
    a_r = reflectance_constant
    panel_tilt = numpy.radians(tilt)  # theta_T
    pi = math.pi

    # equation parts, part 1 is used 2 times
    part1 = math.sin(panel_tilt) + (panel_tilt - math.sin(panel_tilt)) / (1.0 - math.cos(panel_tilt))

    part2 = c1 * part1 + c2 * (part1 ** 2.0)
    part3 = (-1.0 / a_r) * part2

    ghi_reflected = math.e ** (part3)

    return ghi_reflected


def __dhi_reflected(tilt):
    """
    Computes a constant in range [0,1] which represents how much of atmospheric diffuse light is reflected away from
    solar panel surfaces. Constant for an installation. Almost a 1 to 1 copy of __ghi_reflected except
    "pi -" addition to part1 and "1-cos" to "1+cos" replacement in part1 as well.
    :return: [0,1] float, 0 no light reflected, 1 no light absorbed by panels.

    # denoted as alpha_dg in williams work

    F_D(beta) in "Calculation of the PV modules angular losses under field conditions by means of an analytical model"
    """
    # constants

    c1 = 4.0 / (math.pi * 3.0)
    c2 = -0.074
    a_r = reflectance_constant
    panel_tilt = numpy.radians(tilt)  # theta_T
    pi = math.pi

    # equation parts, part 1 is used 2 times
    part1 = math.sin(panel_tilt) + (pi - panel_tilt - math.sin(panel_tilt)) / (1.0 + math.cos(panel_tilt))

    part2 = c1 * part1 + c2 * (part1 ** 2.0)
    part3 = (-1.0 / a_r) * part2

    dhi_reflected = math.e ** part3

    return dhi_reflected
