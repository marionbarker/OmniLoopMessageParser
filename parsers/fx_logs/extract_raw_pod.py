# extract_raw_pod.py

import pandas as pd
import numpy as np
#
from parsers.fx_logs.fapsx_message_dict import fapsx_message_dict


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