# file contains all the functions required to analyze the MessageLogs portion of the Loop Reports .md files
# import requests # not found on local machine python
import time
#import matplotlib.pyplot as plt
#import matplotlib.dates as dates
#from matplotlib.dates import DateFormatter
#from pandas.plotting import register_matplotlib_converters
import re
import pandas as pd
import os

# add more information read for Loop Reports
def getPodDict (omnipodInfo):
    podDict = { \
      'piVersion' : '', \
      'pmVersion' : '', \
      'lot' : '', \
      'tid' : ''}
    idxStart = 0
    for keys in podDict.keys():
        strToSearch = '* ' + keys + ': '
        thisStart = omnipodInfo.find(strToSearch, idxStart)
        nextStart = thisStart + len(strToSearch)
        thisStop = omnipodInfo.find('\n', nextStart)
        values = omnipodInfo[nextStart:thisStop]
        podDict[keys]=values
        idxStart = thisStop

    return podDict


# read the file from the file_path (replace Eelke's original load_file(file_url))

def read_file(filename):
    commands = []
    # some of the files have 'charmap' codec can't decode byte 0x8d in position # XXX
    #  where locations changes but is always after MessageLogs section
    #  read a line at a time until reaching PodComms then quit
    file = open(filename)
    y=file.readline()
    while y != '## OmnipodPumpManager\n':
        y = file.readline()
    omnipodInfo = y
    while y != '### MessageLog\n':
        y = file.readline()
        omnipodInfo = omnipodInfo + y
    xcode_log_text = y
    while y != '## PodComms\n' and y != '':
        y=file.readline()
        xcode_log_text = xcode_log_text+y
    file.close()
    # end of section that replaces Eelke's original .read()
    regex = r"\* ([0-9-:\s]*)\s.*\s(send|receive)\s([a-z0-9]*)\n*"
    select_1a_commands = re.findall(regex, xcode_log_text, re.MULTILINE)
    for line in select_1a_commands:
        commands.append({"time": line[0], "type": line[1], "raw_value": line[2][12:]})
    podDict = getPodDict(omnipodInfo)
    return commands, podDict

def select_extra_command(raw_value):
    if raw_value[:2]=='1a':
        if raw_value[32:34] not in ['16','17']:
            return 13
        else:
            return raw_value[32:34]

def generate_table(commands, radio_on_time):
    df = pd.DataFrame(commands)
    df['time'] = pd.to_datetime(df['time'])
    df['command'] = df['raw_value'].str[:2].astype(str)+df['raw_value'].apply(select_extra_command).fillna('').astype(str)
    df['time_delta'] = (df['time']-df['time'].shift()).dt.seconds.fillna(0).astype(float)
    df['time_asleep'] = df['time_delta'].loc[df['time_delta'] > radio_on_time] - radio_on_time  # radio_on_time seconds the radio stays awake
    return df

# parse the information in the filename
def parse_info_from_filename(filename):
    val = '^.*/'
    thisPerson = re.findall(val, filename)
    if not thisPerson:
        thisPerson = 'Unknown'
    else:
        thisPerson = thisPerson[0] [0:-1]

    finishValues = {'0x12', '0x14', '0x31', '0x34', '0x3d', '0x40', '0x42', '0x80', 'Nominal', '0x18', '0x1c', 'Unknown','WIP'}
    antennaValues = {'origAnt', 'adHocAnt'}

    for val in finishValues:
        thisFinish = re.findall(val,filename)
        if thisFinish:
            break

    for val in antennaValues:
        thisAntenna = re.findall(val,filename)
        if thisAntenna:
            break

    if not thisFinish:
        thisFinish = ['Nominal']

    if not thisAntenna:
        thisAntenna = ['433MHz']

    return (thisPerson, thisFinish[0], thisAntenna[0])
