# extract_raw_determTdd.py

import pandas as pd
import numpy as np
import json
#
from util.misc import printDict


def extract_raw_determTdd(raw_content):

    determTddDF_old = pd.DataFrame({})
    date_patt = raw_content[:8]
    # number of lines after json string starts to search for TDD success
    max_lines = 400
    # phrase for iaps version - this if followed by json format
    tdd_pattern_old = "- DEV: Determinated: "

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
