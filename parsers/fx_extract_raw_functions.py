"""
fx_extract_raw_functions.py

break off from the massive messageLogs_functions.py function

"""

# import time
import re
import pandas as pd
# import os
import markdown
from bs4 import BeautifulSoup, NavigableString, Tag
from util.misc import combineByte
from util.misc import printDict, printList
from parsers.messagePatternParsing import processMsg
from parsers.messageLogs_functions import fapsx_message_dict
# add for FAPSX files
import os
import subprocess
import numpy as np
import json
import tempfile


def extract_raw_pod(raw_content):
    logDF = pd.DataFrame({})
    noisy = 0
    if noisy:
        print(">>>   call to extract_raw_pod")
        print("first 256 characters : ", raw_content[:256])
        print("last  256 characters : ", raw_content[-256:])

    # split by newline:
    lines_raw = raw_content.splitlines()
    numLines = len(lines_raw)

    if numLines == 0:
        print("numLines = ", numLines, " in extract_raw_pod")
        return logDF
    elif noisy:
        print("numLines = ", numLines, " in extract_raw_pod")

    if noisy:
        print('first line\n', lines_raw[0])
        print('last line\n', lines_raw[-1])

    # update 9/3/2022 to handle the new Pod connect
    #  disconnect and Unacknowledged message log output
    pod_patt_f = "DEV: Device message: f"
    pod_patt_1 = "DEV: Device message: 1"
    pod_connect_patt = "DEV: Device message: Pod"
    pod_unack_patt = "DEV: Device message: Unacknowledged"
    pod_messages = [x for x in lines_raw
                    if ((x.find(pod_patt_f) > -1) or
                    (x.find(pod_patt_1) > -1)) and
                    (x.find(pod_connect_patt) == -1) and
                    (x.find(pod_unack_patt) == -1)]
    if len(pod_messages) == 0:
        return logDF
    if noisy:
        print('first pod line\n', pod_messages[0][0:19], ' ',
              pod_messages[0][166:])
        print('last pod line\n', pod_messages[-1][0:19], ' ',
              pod_messages[-1][166:])
        num_lines = len(pod_messages)
        print('Found ', num_lines)
    messages = [fapsx_message_dict(m) for m in pod_messages]

    noisy = 0
    if noisy:
        print('first messages line\n', messages[0])
        print('last messages line\n', messages[-1])
        print('number of messages is ', len(messages))
    logDF = pd.DataFrame(messages)
    logDF['time'] = pd.to_datetime(logDF['time'])
    logDF['deltaSec'] = (
        logDF['time'] -
        logDF['time'].shift()).dt.seconds.fillna(0).astype(float)

    return logDF


def extract_raw_determBasal(raw_content):

    determBasalDF = pd.DataFrame({})
    date_patt = raw_content[:8]
    # number of lines after json string starts to search for TB/SMB success
    max_lines = 400

    noisy = 0
    if noisy:
        print(">>>   call to extract_raw_determBasal")
        print("first 256 characters : ", raw_content[:256])
        print("last  256 characters : ", raw_content[-256:])
        print("date_patt is ", date_patt)

    # split by newline:
    lines_raw = raw_content.splitlines()

    # now extract the determine basal message
    # use the time pattern from messages to id end of json strings
    determBasal_patt = " 68 - DEV:"
    pump_events = "239 - DEV: New pump events:"
    pe_num = 4  # number of lines to search for Bolus or TempBasal

    idx = 0
    numLines = len(lines_raw)

    if numLines == 0:
        print("numLines = ", numLines, " in extract_raw_determBasal")
        return determBasalDF
    elif noisy:
        print("numLines = ", numLines, " in extract_raw_determBasal")

    """
     items in json, choose the ones we want:
        "temp": "absolute",
        "bg": 79,
        "tick": "+0",
        "eventualBG": 111,
        "insulinReq": -0.25,
        "reservoir": 75.6,
        "deliverAt": "2021-06-28T04:02:55.250Z",
        "sensitivityRatio": 1,
        "predBGs": { numbers here for one or more predictions}
        "COB": 18,
        "IOB": 0.69,
        "reason": "COB: 18, Dev: 16, BGI: -3, ISF: 56, CR: 13.15,
                   Target: 82, minPredBG 68, minGuardBG 62, IOBpredBG 54,
                   COBpredBG 111, UAMpredBG 59; Eventual BG 111 >= 82,
                   insulinReq -0.25; setting 60m low temp of 0U/h. ",
        "rate": tbr,
        "duration": 60
        or
        "units": 0.075,
        "duration": 30,
        "rate": tbr
        or
        nothing - if Skip neutral temps is not selected
                    and scheduled basal is suggested
    """

    idx = 0
    numLines = len(lines_raw)
    line_array = []
    timestamp_array = []
    json_length_array = []
    bg_array = []
    sens_array = []
    cob_array = []
    iob_array = []
    rate_array = []
    bolus_array = []
    tb_success_array = []
    smb_success_array = []
    while idx < numLines-1:
        thisLine = lines_raw[idx]
        if determBasal_patt in thisLine:
            line_0 = idx
            # extract dateTime from beginning of line
            timestamp = thisLine[0:10] + ' ' + thisLine[11:19]
            # json string begins at the { at end of this line and ends before
            #   beginning of the next line which start with date_patt,
            #   white space is ignored outside of quotes
            jdx = idx
            json_message = "{"
            while (jdx < numLines-1) and (jdx < (line_0+max_lines-1)):
                jdx += 1
                if lines_raw[jdx][:8] == date_patt:
                    break
                json_message += lines_raw[jdx]

            try:
                json_dict = json.loads(json_message)
            except Exception as e:
                print("Failure parsing at line number", idx)
                print(e)
                # skip over broken part
                idx += 1
                continue

            # check configuration of json_dict
            if "bg" in json_dict:

                # print(idx, timestamp, cob, iob)
                line_array.append(idx)
                timestamp_array.append(timestamp)
                bg_array.append(json_dict['bg'])
                if "sensitivityRatio" in json_dict:
                    sens_array.append(json_dict['sensitivityRatio'])
                else:
                    sens_array.append(np.nan)
                cob_array.append(float(json_dict['COB']))
                iob_array.append(float(json_dict['IOB']))
                if "rate" in json_dict:
                    rate_array.append(json_dict['rate'])
                else:
                    rate_array.append(np.nan)
                if "units" in json_dict:
                    bolus_array.append(json_dict['units'])
                else:
                    bolus_array.append(np.nan)
                json_length_array.append(jdx - idx)
                # continue searching for enact success iff rate or units found
                tb_success_array.append(np.nan)
                smb_success_array.append(np.nan)
                if "rate" in json_dict:
                    # assume failure, search for success
                    tb_success_array[-1] = 0
                if "units" in json_dict:
                    # assume failure, search for success
                    smb_success_array[-1] = 0
                if "rate" in json_dict or "units" in json_dict:
                    # search for pump_events: "239 - DEV: New pump events:"
                    while (jdx < numLines-2) and (jdx < (line_0+max_lines-2)):
                        jdx += 1
                        # if the next json string happens before New pump event
                        # break out of loop
                        if determBasal_patt in lines_raw[jdx]:
                            idx = jdx
                            break
                        if lines_raw[jdx].find(pump_events) > -1:
                            mdx = jdx
                            while mdx-jdx < pe_num:
                                # Medtronic Format:
                                if lines_raw[mdx][:11] == "Bolus units":
                                    smb_success_array[-1] = 1
                                    # print("SMB mdx, lines_raw: ", mdx, ", ",
                                    #      lines_raw[mdx])
                                # Omnipod Format:
                                if lines_raw[mdx][:6] == "Bolus:":
                                    smb_success_array[-1] = 1
                                    # print("SMB mdx, lines_raw: ", mdx, ", ",
                                    #      lines_raw[mdx])
                                if lines_raw[mdx][:9] == "TempBasal":
                                    tb_success_array[-1] = 1
                                    # print(" TB mdx, lines_raw: ", mdx, ", ",
                                    #      lines_raw[mdx])
                                mdx += 1
                            break
            else:
                # print("json_dict missing bg, skipping")
                printDict(json_dict)
            idx = jdx
        else:
            idx = idx+1
            thisLine = lines_raw[idx]

    # finished the entire lines_raw list, create the data frame
    d = {'date_time': timestamp_array, 'line#': line_array,
         'BG': bg_array, 'COB': cob_array, 'IOB': iob_array,
         'Bolus': bolus_array, 'Basal': rate_array,
         'SensRatio': sens_array, 'num_json_lines': json_length_array,
         'TB_Success': tb_success_array, 'SMB_Success': smb_success_array}
    determBasalDF = pd.DataFrame(d)
    # split the time into a new column, use for plots 0 to 24 hour
    time_array = pd.to_datetime(determBasalDF['date_time']).dt.time
    determBasalDF['time'] = time_array

    return determBasalDF


def extract_raw_determTdd(raw_content):

    determTddDF_old = pd.DataFrame({})
    date_patt = raw_content[:8]
    # number of lines after json string starts to search for TDD success
    max_lines = 400
    # phrase for iaps version - this if followed by json format
    tdd_pattern_old = "340 - DEV: Determinated: "

    noisy = 0
    if noisy:
        print(">>>   call to extract_raw_determTdd")
        print("first 256 characters : ", raw_content[:256])
        print("last  256 characters : ", raw_content[-256:])
        print("date_patt is ", date_patt)

    # split by newline:
    lines_raw = raw_content.splitlines()

    # now extract the TDD old style message
    # use the time pattern from messages to id end of json strings
    pe_num = 10  # number of lines to search for TDD

    idx = 0
    numLines = len(lines_raw)

    if numLines == 0:
        print("numLines = ", numLines, " in extract_raw_determTdd")
        return determBasalDF
    elif noisy:
        print("numLines = ", numLines, " in extract_raw_determTdd")

    # Old Style information
    """
     items in json, old version, choose the ones we want:
        340 - DEV: Determinated: {
            "temp": "absolute",
            "bg": 109,
            "tick": -1,
            "eventualBG": 116,
            "insulinReq": -0.04,
            "reservoir": 3735928559,
            "deliverAt": "2024-12-24T08:02:27.573Z",
            "sensitivityRatio": 1,
            "CR": 8,
            "TDD": 4.7,
            "insulin": {
                "TDD": 4.7,
                "bolus": 0.55,
                "temp_basal": 2.55,
                "scheduled_basal": 1.6
            },
    """

    idx = 0
    numLines = len(lines_raw)
    line_array_old = []
    timestamp_array_old = []
    json_length_array = []
    tdd_array_old = []
    bolus_array_old = []
    tb_array_old = []
    sb_array_old = []

    # go through one time for old style TDD information
    while idx < numLines-1:
        thisLine = lines_raw[idx]
        if tdd_pattern_old in thisLine:
            line_0 = idx
            # extract dateTime from beginning of line
            timestamp = thisLine[0:10] + ' ' + thisLine[11:19]
            # json string begins at the { at end of this line and ends before
            #   beginning of the next line which start with date_patt,
            #   white space is ignored outside of quotes
            jdx = idx
            json_message = "{"
            while (jdx < numLines-1) and (jdx < (line_0+max_lines-1)):
                jdx += 1
                if lines_raw[jdx][:8] == date_patt:
                    break
                json_message += lines_raw[jdx]

            try:
                json_dict = json.loads(json_message)
            except Exception as e:
                print("Failure parsing at line number", idx)
                print(e)
                # skip over broken part
                idx += 1
                continue

            # check configuration of json_dict
            if "TDD" in json_dict:
                line_array_old.append(idx)
                timestamp_array_old.append(timestamp)
                json_length_array.append(jdx - idx)
                tdd_array_old.append(json_dict['TDD'])
                insulinDict=json_dict['insulin']
                bolus_array_old.append(insulinDict['bolus'])
                tb_array_old.append(insulinDict['temp_basal'])
                sb_array_old.append(insulinDict['scheduled_basal'])

            else:
                if noisy:
                    print("json_dict missing TDD, skipping")
                    printDict(json_dict)
            idx = jdx
        else:
            idx = idx+1
            thisLine = lines_raw[idx]

    # finished the entire lines_raw list, create the data frame
    d = {'date_time': timestamp_array_old, 
         'line_in_log': line_array_old,
         'json_length': json_length_array,
         'TDD': tdd_array_old,
         'Bolus': bolus_array_old,
         'TempBasal': tb_array_old,
         'SchBasal': sb_array_old}
    determTddDF_old = pd.DataFrame(d)

    if noisy:
        print(determTddDF_old)

    return determTddDF_old


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
