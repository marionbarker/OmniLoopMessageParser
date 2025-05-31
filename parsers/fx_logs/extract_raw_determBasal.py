# extract_raw_determBasal.py

import pandas as pd
import numpy as np
import json
#
from util.misc import printDict
# from util.misc import printList


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
