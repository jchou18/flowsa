# write_Crosswalk_UDSA_CoA_Cropland.py (scripts)
# !/usr/bin/env python3
# coding=utf-8
# ingwersen.wesley@epa.gov

"""
Create a crosswalk linking the downloaded USDA_CoA_Cropland to NAICS_12.
Created by selecting unique Activity Names and
manually assigning to NAICS

NAICS8 are unofficial and are not used again after initial aggregation to NAICS6. NAICS8 are based
on NAICS definitions from the Census.

7/8 digit NAICS align with USDA ERS IWMS

"""
import pandas as pd
from flowsa.common import datapath
from scripts.common_scripts import unique_activity_names, order_crosswalk


def assign_naics(df):
    """
    Function to assign NAICS codes to each dataframe activity
    :param df: df, a FlowByActivity subset that contains unique activity names
    :return: df with assigned Sector columns
    """

    # assign sector source name
    df['SectorSourceName'] = 'NAICS_2012_Code'

    # Coal Integrated Gasification Combined Cycle
    df.loc[df['Activity'] == 'CGCC', 'Sector'] = '221112'

    # Conventional Steam Coal
    df.loc[df['Activity'] == 'CSC', 'Sector'] = '221112'

    # Municipal Solid Waste
    df.loc[df['Activity'] == 'MSW', 'Sector'] = '221118'

    # Natural Gas Fired Combined Cycle
    df.loc[df['Activity'] == 'NGCC', 'Sector'] = '221112'

    # Natural Gas Steam Turbine
    df.loc[df['Activity'] == 'NGSC', 'Sector'] = '221112'

    # Nuclear
    df.loc[df['Activity'] == 'NU', 'Sector'] = '221113'

    # Other Gases
    df.loc[df['Activity'] == 'OG', 'Sector'] = '221118'

    # Other - specified in footnotes of source data
    df.loc[df['Activity'] == 'OT', 'Sector'] = '221118'

    # Other Waste Biomass
    df.loc[df['Activity'] == 'OWB', 'Sector'] = '221117'

    # Petroleum Coke
    df.loc[df['Activity'] == 'PC', 'Sector'] = '221112'

    # Petroleum Liquids
    df.loc[df['Activity'] == 'PL', 'Sector'] = '221112'

    # Solar Thermal with or without Energy Storage
    df.loc[df['Activity'] == 'ST', 'Sector'] = '221114'

    # Wood/Wood Waste Biomass
    df.loc[df['Activity'] == 'WB', 'Sector'] = '221117'




    return df


if __name__ == '__main__':
    # select years to pull unique activity names
    year = '2016'
    # datasource
    datasource = 'NETL_EIA_PlantWater'
    # df of unique ers activity names
    df = unique_activity_names(datasource, year)
    # add manual naics 2012 assignments
    df = assign_naics(df)
    # drop any rows where naics12 is 'nan'
    # (because level of detail not needed or to prevent double counting)
    df = df.dropna()
    # assign sector type
    df['SectorType'] = None
    # sort df
    df = order_crosswalk(df)
    # save as csv
    df.to_csv(datapath + "activitytosectormapping/" +
              "Crosswalk_" + datasource + "_toNAICS.csv", index=False)
