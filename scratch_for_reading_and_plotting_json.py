# scratch_for_reading_and_plotting_json.py

# use the same project as OmniLoopMessageParser, but may need to break out later

# first read in a Nightscout json file and print out selected results

# copy imports from messageLogs_function.py

import re
import pandas as pd
# import os
import markdown
from bs4 import BeautifulSoup, NavigableString, Tag
from util.misc import combineByte
from util.misc import printDict, printList
from parsers.messagePatternParsing import processMsg
# add for FAPSX files
import os
import subprocess
import numpy as np
import json
import tempfile

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
 
    noisy = 1
    if noisy:
        print("\n>>>   call to extract_raw_nightscout")
        print("first 256 characters : ", raw_content[:256])
        print("\nlast  256 characters : ", raw_content[-256:])

    # split by newline:
    lines_raw = raw_content.splitlines()
    print("\nlines_raw has ", len(lines_raw), " lines")

    # parse the devicedata output
    ''' - figure out direct to dataframe later
    jdx=0
    for line in lines_raw:
        try:
            nsDeviceDataDF=pd.read_json(line)
            print("pd.read_json parse index ", jdx)
            print(nsDeviceDataDF)
            jdx=jdx+1

        except Exception as e:
            print("Failure parsing json")
            print("*** exception:")
            print(e)
            print("*** line:")
            print(line)
            exit
    '''

    jdx=0
    iob_time=[]
    iob=[]
    glucose_time=[]
    glucose=[]
    for line in lines_raw:
        try:
            json_dict = json.loads(line)
            iob_time.append=json_dict['loop']['iob']['timestamp']
            iob.append=json_dict['loop']['iob']['iob']
            glucose_time.append=json_dict['loop']['predicted']['startDate']
            glucose.append=json_dict['loop']['predicted']['values'][0]
            print("jdx = ", jdx)
            print(iob_time, iob, glucose_time, glucose)
            jdx=jdx+1

        except Exception as e:
            print("Failure parsing json")
            print("*** exception:")
            print(e)
            print("*** line:")
            print(line)
            exit

    return json_dict


def main():
    filename = "/Users/marion/dev/Loop_FreeAPS_Dash_Development/01-AlgorithmExperiments/test_output_short.txt"
    content = read_devicestatus_file(filename)
    json_dict = extract_raw_nightscout(content)
    print(" *** json dict:")
    printDict(json_dict)


if __name__ == "__main__":
    main()

