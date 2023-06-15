# scratch_for_reading_and_plotting_json.py

# use the same project as OmniLoopMessageParser, but may need to break out later

# first read in a Nightscout json file and print out selected results

# copy imports from messageLogs_function.py

import re
import pandas as pd
# import os
from util.misc import printDict, printList
# add for FAPSX files
import os
import subprocess
import numpy as np
import json
import tempfile
import matplotlib.pyplot as plt


def read_devicestatus_file(filename):
    print("filename in read_json_file = ", filename)
    fp = open(filename, "r", encoding='UTF8')
    raw_content = fp.read()
    fp.close()
    # remove the beginning and ending []
    content = raw_content[1:-2]
    # break into separate json lines
    content = content.replace(',{"_id', '\n{"_id')
    return content
    

# modify extract_raw_determBasal
# to extract_raw_nightscout
# with URL/api/v1/devicestatus.json, the file is all one line
# so we don't use a date_patt
def extract_raw_nightscout(raw_content):

    nsDeviceDataDF = pd.DataFrame({})
 
    noisy = 0
    if noisy:
        print("\n>>>   call to extract_raw_nightscout")
        print("first 256 characters : ", raw_content[:256])
        print("\nlast  256 characters : ", raw_content[-256:])

    # split by newline:
    lines_raw = raw_content.splitlines()
    print("\nlines_raw has ", len(lines_raw), " lines")

    # parse the devicedata output
    jdx=0
    loop_time=[]
    iob_time=[]
    iob=[]
    glucose_time=[]
    glucose=[]
    for line in lines_raw:
        try:
            json_dict = json.loads(line)
            if (jdx < 2 & noisy):
                print('\n *** jdx = ', jdx)
                printDict(json_dict)
            loop_time.append(json_dict['loop']['timestamp'])
            iob_time.append(json_dict['loop']['iob']['timestamp'])
            iob.append(json_dict['loop']['iob']['iob'])
            glucose_time.append(json_dict['loop']['predicted']['startDate'])
            glucose.append(json_dict['loop']['predicted']['values'][0])
            if noisy:
                print("\n *** jdx = ", jdx)
                print(loop_time[jdx], glucose_time[jdx], iob_time[jdx], glucose[jdx], iob[jdx])
            jdx=jdx+1

        except Exception as e:
            print("Failure parsing json")
            print("*** exception:")
            print(e)
            print("*** line:")
            print(line)
            exit

    d = {'loop_time': loop_time, 'iob_time': iob_time, 
         'glucose_time': glucose_time,
        'iob': iob, 'glucose': glucose}
    nsDeviceDataDF = pd.DataFrame(d)
    # split the time into a new column, use for plots 0 to 24 hour
    time_array = pd.to_datetime(nsDeviceDataDF['loop_time']).dt.time
    nsDeviceDataDF['time'] = time_array

    return nsDeviceDataDF


def main():
    #filename = "/Users/marion/dev/Loop_FreeAPS_Dash_Development/01-AlgorithmExperiments/test_output_short.txt"
    filename = "/Users/marion/dev/Loop_FreeAPS_Dash_Development/01-AlgorithmExperiments/test_output.txt"
    content = read_devicestatus_file(filename)
    nsDeviceDataDF = extract_raw_nightscout(content)
    print(" *** nsDeviceDataDF:")
    print(nsDeviceDataDF)


if __name__ == "__main__":
    main()

