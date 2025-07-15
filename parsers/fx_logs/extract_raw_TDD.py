# extract_raw_TDD.py

import pandas as pd
import numpy as np


def extract_raw_TDD(raw_content):
    # use for versions of Trio that calculate rolling TDD using swift
    # format changed part-way through development

    determTddDF_tcd = pd.DataFrame({})
    date_patt = raw_content[:8]
    # number of lines after json string starts to search for TDD success
    max_lines = 400

    noisy = 0
    if noisy:
        print(">>>   call to extract_raw_determTdd")
        print("first 256 characters : ", raw_content[:256])
        print("last  256 characters : ", raw_content[-256:])
        print("date_patt is ", date_patt)

    # split by newline:
    lines_raw = raw_content.splitlines()

    # new tcd output here - first pattern
    """
     items in log, tcd version - does not use json:
        84 - DEV: TDD Summary:
        - Total: 4.9 U
        - Bolus: 0.55 U (11.2 %)
        - Temp Basal: 2.75 U (56.1 %)
        - Scheduled Basal: 1.6 U (32.7 %)
        - WeightedAverage: 0 U
        - Hours of Data: 10.336439974175558
    """

    # new tcd output here - second pattern
    """
     items in log, tcd version - does not use json:
    111 - DEV: TDD Summary:
    +-------------------+-----------+-----------+
    | Type				| Amount U	| Percent %	|
    +-------------------+-----------+-----------+
    | Total				| 26.85		| 			|
    | Bolus				| 14.15		| 52.70		|
    | Temp Basal		| 12.70		| 47.30		|
    | Scheduled Basal	| 0.00		| 0.00		|
    | Weighted Average	| 0.00		| 			|
    +-------------------+-----------+-----------+
    - Hours of Data: 23.89372
    - Earliest Event: Type: tempBasal, Timestamp: 2025-01-04T04:02:53Z
    - Latest Event: Type: tempBasal, Timestamp: 2025-01-05T03:56:30Z
    """

    idx = 0
    numLines = len(lines_raw)
    line_array_tcd = []
    timestamp_array_tcd = []
    tdd_array_tcd = []
    bolus_array_tcd = []
    tb_array_tcd = []
    sb_array_tcd = []
    wt_ave_tcd = []
    hr_data_tcd = []
    earliest_date = []
    latest_date = []
    earliest_type = []
    latest_type = []
    tdd_pattern_tcd_A = "84 - DEV: TDD Summary:"
    tdd_pattern_tcd_B = " - DEV: TDD Summary:"
    na_string = "NA"
    split0 = ": "
    split1 = " U"
    split2 = "| "

    # go through one time for old style TDD information
    # old hack but it was working so leave it unchanged
    # tried dnzxy regex example, but wasn't sure how to get it to work
    # hack the new table the same way - fix this all later
    while idx < numLines-1:
        thisLine = lines_raw[idx]
        if tdd_pattern_tcd_A in thisLine:
            # extract dateTime from beginning of line
            timestamp = thisLine[0:10] + ' ' + thisLine[11:19]
            # the next line contains the "- Total: value U" for the TDD
            thisString = lines_raw[idx+1]
            tmp = thisString.split(split0,2)
            value = tmp[1].split(split1,2)
            tdd_array_tcd.append(value[0])
            #
            thisString = lines_raw[idx+2]
            tmp = thisString.split(split0,2)
            value = tmp[1].split(split1,2)
            bolus_array_tcd.append(value[0])
            #
            thisString = lines_raw[idx+3]
            tmp = thisString.split(split0,2)
            value = tmp[1].split(split1,2)
            tb_array_tcd.append(value[0])
            #
            thisString = lines_raw[idx+4]
            tmp = thisString.split(split0,2)
            value = tmp[1].split(split1,2)
            sb_array_tcd.append(value[0])
            #
            thisString = lines_raw[idx+5]
            tmp = thisString.split(split0,2)
            value = tmp[1].split(split1,2)
            wt_ave_tcd.append(value[0])
            #
            thisString = lines_raw[idx+6]
            value = thisString.split(split0,2)
            hr_data_tcd.append(value[1])
            #
            line_array_tcd.append(idx)
            timestamp_array_tcd.append(timestamp)
            earliest_date.append(na_string)
            latest_date.append(na_string)
            earliest_type.append(na_string)
            latest_type.append(na_string)
            idx = idx + 6
        elif tdd_pattern_tcd_B in thisLine:
            # extract dateTime from beginning of line
            timestamp = thisLine[0:10] + ' ' + thisLine[11:19]
            # next 3 lines are table header
            tdd_string = lines_raw[idx+4]
            bolus_string = lines_raw[idx+5]
            tb_string = lines_raw[idx+6]
            sb_string = lines_raw[idx+7]
            wt_string = lines_raw[idx+8]
            hr_string = lines_raw[idx+10]
            event0 = lines_raw[idx+11]
            event1 = lines_raw[idx+12]
            line_array_tcd.append(idx)
            timestamp_array_tcd.append(timestamp)
            value = tdd_string.split(split2,3)
            # remove the two \t after value
            tdd_array_tcd.append(value[2][:-2])
            value = bolus_string.split(split2,3)
            bolus_array_tcd.append(value[2][:-2])
            value = tb_string.split(split2,3)
            tb_array_tcd.append(value[2][:-2])
            value = sb_string.split(split2,3)
            sb_array_tcd.append(value[2][:-2])
            value = wt_string.split(split2,3)
            wt_ave_tcd.append(value[2][:-2])
            value = hr_string.split(split0,2)
            hr_data_tcd.append(value[1])
            if event0 == "- Earliest Event: No events available":
                earliest_date.append(na_string)
                earliest_type.append(na_string)
                latest_date.append(na_string)
                latest_type.append(na_string)
            else:
                value = event0.split(",",2)
                type = value[0].split(split0,3)
                earliest_date.append(value[1][-20:-1])
                earliest_type.append(type[2])
                value = event1.split(",",2)
                type = value[0].split(split0,3)
                latest_date.append(value[1][-20:-1])
                latest_type.append(type[2])
            idx = idx + 15
        else:
            idx = idx+1
            thisLine = lines_raw[idx]

    # finished the entire lines_raw list, create the data frame
    d = {'date_time': timestamp_array_tcd, 'line_in_log': line_array_tcd,
         'Total': tdd_array_tcd, 'Bolus': bolus_array_tcd,
         'TempBasal': tb_array_tcd, 'SchBasal': sb_array_tcd,
         'WtAverage': wt_ave_tcd, 'HrsOfData': hr_data_tcd,
         'earliest_UTC': earliest_date, 'earliest_type': earliest_type, 
         'latest_UTC': latest_date, 'latest_type': latest_type }
    determTddDF_tcd = pd.DataFrame(d)

    if noisy:
        print(determTddDF_tcd)

    return determTddDF_tcd
