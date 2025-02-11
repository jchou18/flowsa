# USDA_ERS_FIWS.py (flowsa)
# !/usr/bin/env python3
# coding=utf-8
"""
USDA Economic Research Service (ERS) Farm Income and Wealth Statistics (FIWS)
https://www.ers.usda.gov/data-products/farm-income-and-wealth-statistics/

Downloads the February 5, 2020 update
"""

import zipfile
import io
import pandas as pd
from flowsa.common import US_FIPS, get_all_state_FIPS_2, us_state_abbrev


def fiws_call(**kwargs):
    """
    Convert response for calling url to pandas dataframe, begin parsing df into FBA format
    :param kwargs: potential arguments include:
                   url: string, url
                   response_load: df, response from url call
                   args: dictionary, arguments specified when running
                   flowbyactivity.py ('year' and 'source')
    :return: pandas dataframe of original source data
    """
    # load arguments necessary for function
    response_load = kwargs['r']

    # extract data from zip file (only one csv)
    with zipfile.ZipFile(io.BytesIO(response_load.content), "r") as f:
        # read in file names
        for name in f.namelist():
            data = f.open(name)
            df = pd.read_csv(data, encoding="ISO-8859-1")
        return df


def fiws_parse(**kwargs):
    """
    Combine, parse, and format the provided dataframes
    :param kwargs: potential arguments include:
                   dataframe_list: list of dataframes to concat and format
                   args: dictionary, used to run flowbyactivity.py ('year' and 'source')
    :return: df, parsed and partially formatted to flowbyactivity specifications
    """
    # load arguments necessary for function
    dataframe_list = kwargs['dataframe_list']
    args = kwargs['args']

    # concat dataframes
    df = pd.concat(dataframe_list, sort=False)
    # select data for chosen year, cast year as string to match argument
    df['Year'] = df['Year'].astype(str)
    df = df[df['Year'] == args['year']].reset_index(drop=True)
    # add state fips codes, reading in datasets from common.py
    fips = get_all_state_FIPS_2().reset_index(drop=True)
    # ensure capitalization of state names
    fips['State'] = fips['State'].apply(lambda x: x.title())
    fips['StateAbbrev'] = fips['State'].map(us_state_abbrev)
    # pad zeroes
    fips['FIPS_2'] = fips['FIPS_2'].apply(lambda x: x.ljust(3 + len(x), '0'))
    df = pd.merge(df, fips, how='left', left_on='State', right_on='StateAbbrev')
    # set us location code
    df.loc[df['State_x'] == 'US', 'FIPS_2'] = US_FIPS
    # drop "All" in variabledescription2
    df.loc[df['VariableDescriptionPart2'] == 'All', 'VariableDescriptionPart2'] = 'drop'
    # combine variable descriptions to create Activity name and remove ", drop"
    df['ActivityProducedBy'] = df['VariableDescriptionPart1'] + \
                               ', ' + df['VariableDescriptionPart2']
    df['ActivityProducedBy'] = df['ActivityProducedBy'].str.replace(", drop", "", regex=True)
    # trim whitespace
    df['ActivityProducedBy'] = df['ActivityProducedBy'].str.strip()
    # drop columns
    df = df.drop(columns=['artificialKey', 'PublicationDate', 'Source', 'ChainType_GDP_Deflator',
                          'VariableDescriptionPart1', 'VariableDescriptionPart2',
                          'State_x', 'State_y', 'StateAbbrev', 'unit_desc'])
    # rename columns
    df = df.rename(columns={"VariableDescriptionTotal": "Description",
                            "Amount": "FlowAmount",
                            "FIPS_2": "Location"})
    # assign flowname, based on comma placement
    df['FlowName'] = df['Description'].str.split(',').str[0]
    # add location system based on year of data
    df['Year'] = df['Year'].astype(int)
    df.loc[df['Year'] >= 2019, 'LocationSystem'] = 'FIPS_2019'
    df.loc[df['Year'].between(2015, 2018), 'LocationSystem'] = 'FIPS_2015'
    df.loc[df['Year'].between(2013, 2014), 'LocationSystem'] = 'FIPS_2013'
    df.loc[df['Year'].between(2010, 2012), 'LocationSystem'] = 'FIPS_2010'
    # drop unnecessary rows
    df = df[df['FlowName'].str.contains("Cash receipts")]
    # the unit is $1000 USD, so multiply FlowAmount by 1000 and set unit as 'USD'
    df['FlowAmount'] = df['FlowAmount'].astype(float)
    df['FlowAmount'] = df['FlowAmount'] * 1000
    # hard code data
    df['Class'] = 'Money'
    df['SourceName'] = 'USDA_ERS_FIWS'
    df['Unit'] = 'USD'
    # Add DQ scores
    df['DataReliability'] = 5  # tmp
    df['DataCollection'] = 5  # tmp
    # sort df
    df = df.sort_values(['Location', 'FlowName'])
    # reset index
    df.reset_index(drop=True, inplace=True)

    return df
