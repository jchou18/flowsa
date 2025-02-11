# USGS_MYB_SodaAsh.py (flowsa)
# !/usr/bin/env python3
# coding=utf-8

"""
SourceName: USGS_MYB_SodaAsh
https://www.usgs.gov/centers/nmic/soda-ash-statistics-and-information

Minerals Yearbook, xls file, tab "T4"
REPORTED CONSUMPTION OF SODA ASH IN THE UNITED STATES, BY END USE, BY QUARTER1

Interested in annual data, not quarterly
Years = 2010+
https://s3-us-west-2.amazonaws.com/prd-wret/assets/palladium/production/mineral-pubs/soda-ash/myb1-2010-sodaa.pdf
"""

import io
import math
from string import digits
import pandas as pd
from flowsa.flowbyfunctions import assign_fips_location_system


def description(value, code):
    """
    Create string for column based on row description
    :param value: str, description column for a row
    :param code: str, NAICS code
    :return: str, to use as column value
    """
    glass_list = ["Container", "Flat", "Fiber", "Other", "Total"]
    other_list = ["Total domestic consumption4"]
    export_list = ["Canada"]
    return_val = ""
    if value in glass_list:
        return_val = "Glass " + value
        if math.isnan(code):
            return_val = value
        if value == "Total":
            return_val = "Glass " + value
    elif value in other_list:
        return_val = "Other " + value
    elif value in export_list:
        return_val = "Exports " + value
    else:
        return_val = value
    remove_digits = str.maketrans('', '', digits)
    return_val = return_val.translate(remove_digits)
    return return_val


def soda_url_helper(**kwargs):
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
    config = kwargs['config']
    args = kwargs['args']

    # URL Format, replace __year__ and __format__, either xls or xlsx.
    url = build_url
    year = str(args["year"])
    url = url.replace("__url_text__", config["url_texts"][year])
    url = url.replace("__year__", year)
    url = url.replace("__format__", config["formats"][year])
    return [url]


def soda_call(**kwargs):
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

    df_raw_data = pd.read_excel(io.BytesIO(response_load.content),
                                sheet_name='T4')
    if kwargs['args']['year'] == '2017':
        df_data = pd.DataFrame(df_raw_data.loc[7:25]).reindex()
        df_data = df_data.iloc[:, [0, 2, 22]]
    else:
        df_data = pd.DataFrame(df_raw_data.loc[7:25]).reindex()
        df_data = df_data.iloc[:, [0, 2, 14]]
    df_data = df_data.reset_index(drop=True)
    df_data.columns = ["NAICS code", "End use", "Total"]
    return df_data


def soda_parse(**kwargs):
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

    total_glass = 0
    data = {}
    dataframe = pd.DataFrame()
    for df in dataframe_list:

        data["Class"] = "Chemicals"
        data['FlowType'] = "Elementary Type"
        data["Location"] = "00000"
        data["Compartment"] = " "
        data["SourceName"] = "USGS_MYB_SodaAsh"
        data["Year"] = str(args["year"])
        data["Unit"] = "Thousand metric tons"
        data['FlowName'] = "Soda Ash"
        data["Context"] = "air"
        data['DataReliability'] = 5  # tmp
        data['DataCollection'] = 5  # tmp

        for index, row in df.iterrows():
            data["Description"] = ""
            data['ActivityConsumedBy'] = description(df.iloc[index]["End use"],
                                                     df.iloc[index]["NAICS code"])

            if df.iloc[index]["End use"].strip() == "Glass:":
                total_glass = int(df.iloc[index]["NAICS code"])
            elif data['ActivityConsumedBy'] == "Glass Total":
                data["Description"] = total_glass

            if not math.isnan(df.iloc[index]["Total"]):
                data["FlowAmount"] = int(df.iloc[index]["Total"])
                data["ActivityProducedBy"] = None
                if not math.isnan(df.iloc[index]["NAICS code"]):
                    des_str = str(df.iloc[index]["NAICS code"])
                    data["Description"] = des_str
            if df.iloc[index]["End use"].strip() != "Glass:":
                dataframe = dataframe.append(data, ignore_index=True)
                dataframe = assign_fips_location_system(dataframe, str(args["year"]))
    return dataframe
