# Census_CBP.py (flowsa)
# !/usr/bin/env python3
# coding=utf-8
"""
Pulls County Business Patterns data in NAICS from the Census Bureau
Writes out to various FlowBySector class files for these data items
EMP = Number of employees, Class = Employment
PAYANN = Annual payroll ($1,000), Class = Money
ESTAB = Number of establishments, Class = Other
This script is designed to run with a configuration parameter
--year = 'year' e.g. 2015
"""
import json
import pandas as pd
import numpy as np
from flowsa.common import get_all_state_FIPS_2, get_county_FIPS
from flowsa.flowbyfunctions import assign_fips_location_system


def Census_CBP_URL_helper(**kwargs):
    """
    This helper function uses the "build_url" input from flowbyactivity.py, which
    is a base url for data imports that requires parts of the url text string
    to be replaced with info specific to the data year.
    This function does not parse the data, only modifies the urls from which data is obtained.
    :param kwargs: potential arguments include:
                   build_url: string, base url
                   config: dictionary, items in FBA method yaml
                   args: dictionary, arguments specified when running flowbyactivity.py
                   flowbyactivity.py ('year' and 'source')
    :return: list, urls to call, concat, parse, format into Flow-By-Activity format
    """

    # load the arguments necessary for function
    build_url = kwargs['build_url']
    args = kwargs['args']

    urls_census = []
    # This section gets the census data by county instead of by state.
    # This is only for years 2010 and 2011. This is done because the State
    # query that gets all counties returns too many results and errors out.
    if args["year"] in ['2010', '2011']:
        if args["year"] == '2011':
            fips_year = '2010'
        else:
            fips_year = '2010'
        county_fips_df = get_county_FIPS(fips_year)
        county_fips = county_fips_df.FIPS
        for d in county_fips:
            url = build_url
            state_digit = str(d[0]) + str(d[1])
            county_digit = str(d[2]) + str(d[3]) + str(d[4])
            url = url.replace("__NAICS__", "NAICS2007")
            url = url.replace("__stateFIPS__", state_digit)
            url = url.replace("__countyFIPS__", county_digit)

            if args["year"] == "2010":
                # These are the counties where data is not available.
                # s signifies state code and y indicates year.
                s_02_y_10 = ["105", "195", "198", "230", "275"]
                s_15_y_10 = ["005"]
                s_48_y_10 = ["269"]

                # There are specific counties in various states for the year
                # 2010 that do not have data. For these counties a URL is not
                # generated as if there is no data then an error occurs.
                if state_digit == "02" and county_digit in s_02_y_10 or \
                        state_digit == "15" and county_digit in s_15_y_10 or \
                        state_digit == "48" and county_digit in s_48_y_10:
                    pass
                else:
                    urls_census.append(url)
            else:
                # These are the counties where data is not available.
                # s signifies state code and y indicates year.
                s_02_y_11 = ["105", "195", "198", "230", "275"]
                s_15_y_11 = ["005"]
                s_48_y_11 = ["269", "301"]

                # There are specific counties in various states for the year 2011
                # that do not have data. For these counties a URL is not generated
                # as if there is no data then an error occurs.
                if state_digit == "02" and county_digit in s_02_y_11 or \
                        state_digit == "15" and county_digit in s_15_y_11 or \
                        state_digit == "48" and county_digit in s_48_y_11:
                    pass
                else:
                    urls_census.append(url)
    else:
        FIPS_2 = get_all_state_FIPS_2()['FIPS_2']
        for c in FIPS_2:
            url = build_url
            url = url.replace("__stateFIPS__", c)
            # specified NAICS code year depends on year of data
            if args["year"] in ['2017']:
                url = url.replace("__NAICS__", "NAICS2017")
                url = url.replace("__countyFIPS__", "*")
            if args["year"] in ['2012', '2013', '2014', '2015', '2016']:
                url = url.replace("__NAICS__", "NAICS2012")
                url = url.replace("__countyFIPS__", "*")
            urls_census.append(url)

    return urls_census


def census_cbp_call(**kwargs):
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

    cbp_json = json.loads(response_load.text)
    # convert response to dataframe
    df_census = pd.DataFrame(data=cbp_json[1:len(cbp_json)], columns=cbp_json[0])
    return df_census


def census_cbp_parse(**kwargs):
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
    # Add year
    df['Year'] = args["year"]
    # convert county='999' to line for full state
    df.loc[df['county'] == '999', 'county'] = '000'
    # Make FIPS as a combo of state and county codes
    df['Location'] = df['state'] + df['county']
    # now drop them
    df = df.drop(columns=['state', 'county'])
    # rename NAICS column and add NAICS year as description
    if 'NAICS2007' in df.columns:
        df = df.rename(columns={"NAICS2007": "ActivityProducedBy"})
        df['Description'] = 'NAICS2007'
    if 'NAICS2012' in df.columns:
        df = df.rename(columns={"NAICS2012": "ActivityProducedBy"})
        df['Description'] = 'NAICS2012'
    if 'NAICS2017' in df.columns:
        df = df.rename(columns={"NAICS2017": "ActivityProducedBy"})
        df['Description'] = 'NAICS2017'
    # drop all sectors record
    df = df[df['ActivityProducedBy'] != "00"]
    # rename columns
    df = df.rename(columns={'ESTAB': 'Number of establishments',
                            'EMP': 'Number of employees',
                            'PAYANN': 'Annual payroll'})
    # use "melt" fxn to convert colummns into rows
    df = df.melt(id_vars=["Location", "ActivityProducedBy", "Year", "Description"],
                 var_name="FlowName",
                 value_name="FlowAmount")
    # specify unit based on flowname
    df['Unit'] = np.where(df["FlowName"] == 'Annual payroll', "USD", "p")
    # specify class
    df.loc[df['FlowName'] == 'Number of employees', 'Class'] = 'Employment'
    df.loc[df['FlowName'] == 'Number of establishments', 'Class'] = 'Other'
    df.loc[df['FlowName'] == 'Annual payroll', 'Class'] = 'Money'
    # add location system based on year of data
    df = assign_fips_location_system(df, args['year'])
    # hard code data
    df['SourceName'] = 'Census_CBP'
    # Add tmp DQ scores
    df['DataReliability'] = 5
    df['DataCollection'] = 5
    df['Compartment'] = None
    return df
