# extract_raw_pod.py

import pandas as pd
import numpy as np
#

def get_timestamp_from_line(thisLine, recordType):
    if recordType == "deviceLog":
        timestamp = thisLine[2:22]
    else:
        timestamp = thisLine[2:22]

    return timestamp

def get_pod_address_from_line(thisLine, recordType):
    if recordType == "deviceLog":
        pod_address = thisLine[41:49]
    else:
        pod_address = "N/A"

    return pod_address

def extract_pod_connect_time(raw_content, recordType):
    # raw_content: lines from the log file
    # log_type: "loop" or "fx"
    connectDF = pd.DataFrame({})
    noisy = 1

    # split by newline:
    lines_raw = raw_content.splitlines()
    numLines = len(lines_raw)

    if numLines == 0:
        print("numLines = ", numLines, " in extract_pod_connect_time")
        return logDF
    elif noisy:
        print("numLines = ", numLines, " in extract_pod_connect_time")
        print('first line\n', lines_raw[0])
        print('last few lines\n', lines_raw[-5:-1])

    # create a data frame with pod connect, disconnect
    #  and, if available, debug @@@ comments
    pod_patt_connect = "connection Pod connected"
    pod_patt_disconnect = "connection Pod disconnected"
    pod_patt_connect_fx = "Device message: Pod connected"
    pod_patt_disconnect_fx = "Device message: Pod disconnected"

    # configure blank arrays to use for filling in the dataframe
    idx = -1
    numLines = len(lines_raw)
    timestamp_array = []
    pod_address_array = []
    # options are 1 = connect, 0 = disconnect, 2 = debug
    pod_connect_array = []
    # options are 0 if not a debug row, otherwise 1 = runSession, 2 = sendMessage,
    #  3 = isConnected (state nil), 4 = isConnected (C.CBPeripheralState)
    # pod_debug_array = []
    pod_address_array = []

    # go through a line at a time searching for patterns and fill out arrays
    # not efficient but it works
    while idx < numLines-1:
        idx = idx+1
        thisLine = lines_raw[idx]
        extract_from_this_line = 0
        if (pod_patt_connect in thisLine) | (pod_patt_connect_fx in thisLine):
            extract_from_this_line = 1
            pod_connect_array.append(1)
        elif (pod_patt_disconnect in thisLine) | (pod_patt_disconnect_fx in thisLine):
            extract_from_this_line = 1
            pod_connect_array.append(0)

        if extract_from_this_line == 1:
            timestamp = get_timestamp_from_line(thisLine, recordType)
            timestamp_array.append(timestamp)
            pod_address = get_pod_address_from_line(thisLine, recordType)
            pod_address_array.append(pod_address)

    # finished the entire lines_raw list, create the data frame
    d = {'time': timestamp_array, 'pod_address': pod_address_array,
         'pod_connect': pod_connect_array }
    connectDF = pd.DataFrame(d)

    # git deltaTime between every message
    connectDF['time'] = pd.to_datetime(connectDF['time'])
    # calculate all the delta times
    connectDF['deltaTime'] = (connectDF['time'] -
                         connectDF['time'].shift()
                         ).dt.seconds.fillna(0).astype(float)

    if noisy:
        print(connectDF)

    return connectDF


## do not use the pod_debug_array, but save the code
#    # finished the entire lines_raw list, create the data frame
#    d = {'time': timestamp_array, 'pod_address': pod_address_array,
#         'pod_connect': pod_connect_array,
#         'pod_debug': pod_debug_array }
