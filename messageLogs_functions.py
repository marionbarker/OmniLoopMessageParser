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

# add these two packages for the sequence and statistics calculations
from collections import Counter
import numpy as np


# read the file from the file_path (replace Eelke's original load_file(file_url))

def read_file(filename):
    commands = []
    file = open(filename)
    # limit the number of characters to 5k lines
    maxChars = 100*3400
    xcode_log_text = file.read(maxChars)

    # print(xcode_log_text)
    regex = r"\* ([0-9-:\s]*)\s.*\s(send|receive)\s([a-z0-9]*)\n*"
    select_1a_commands = re.findall(regex, xcode_log_text, re.MULTILINE)
    for line in select_1a_commands:
        commands.append({"time": line[0], "type": line[1], "raw_value": line[2][12:]})
    return commands

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


# generate a list of sequences (command/response groupings) from the dataframes
def generate_sequence(frame):
    # returns a list of the indices to dataframes that are part of a single sequence
    # This list will hold our indices
    list_of_sequences = []
    # This list is a sequence, remember to clear it after appending to the big list
    sequence = []
    for index, row in frame.iterrows():
        if pd.isna(row['time_asleep']):
            sequence.append(index)
        else:
            list_of_sequences.append(sequence)
            del(sequence)
            sequence = []
            sequence.append(index)

    return list_of_sequences


# prepare of list of the number of individual commands in each sequence
# this returns tuples of [number of commands in a sequence, number of sequences with that length]
def count_cmds_per_sequence(list_of_sequences):
    sequence_counter = Counter()
    for sequence in list_of_sequences:
        sequence_counter[len(sequence)] += 1

    return list(sequence_counter.items())


# prepare an array of the time since pod started to the first command in each
# sequence and the number of commands in that sequence
def create_time_vs_sequenceLength(frame, list_of_sequences, radio_on_time):
    """
    Returns a list of tuples (time since first command, length of sequence).

    PARAMS:
        frame (pandas.DataFrame): The pandas dataframe of commands
        list_of_sequences (list): The list of sequences from generate_sequence()
        radio_on_time: time in sec that Pod radio stays on one awake

    RETURNS:
        time_vs_sequenceLength (list):
          list of tuples (
              time in hours since pod start,
              length of messages,
              cummulative time (hours) pod radio is awake
              )
    """
    # initialize some stuff
    time_vs_sequenceLength = []
    first_command = frame.iloc[0]['time']
    pod_radio_awake_time = 0.0

    for sequence in list_of_sequences:
        timeDelta_since_beginning = (frame.iloc[sequence[0]]['time']-first_command)
        time_since_beginning_hrs = timeDelta_since_beginning.total_seconds()/3600
        seqLength = len(sequence)
        timeInSequence = (frame.iloc[sequence[seqLength-1]]['time']-frame.iloc[sequence[0]]['time'])
        timeInSequence_sec = timeInSequence.total_seconds()
        thisTime =  (timeInSequence_sec + radio_on_time)/3600
        if seqLength >= 1:
            pod_radio_awake_time += thisTime

        time_vs_sequenceLength.append((time_since_beginning_hrs, seqLength, pod_radio_awake_time))

    return time_vs_sequenceLength

# prepare all single sequence commands
def create_singleton_times(time_vs_sequenceLength):
    time_for_singleton = []
    for item in time_vs_sequenceLength:
        if item[1] == 1:
            time_for_singleton.append(item[0])

    return time_for_singleton

# parse the information in the filename
def parse_info_from_filename(filename):
    val = '^.*/'
    thisPerson = re.findall(val, filename)
    if not thisPerson:
        thisPerson = 'Unknown'
    else:
        thisPerson = thisPerson[0] [0:-1]

    finishValues = {'0x14', '0x34', '0x40', 'Nominal'}
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
        thisFinish = ['Unknown']

    if not thisAntenna:
        thisAntenna = ['433MHz']

    return (thisPerson, thisFinish[0], thisAntenna[0])

# parse the number of commands per sequence into ordered array
def get_cmds_per_seq_histogram(cmds_per_sequence):
    # first find out the maximum number of commands in a sequence
    maxNum = 0;
    for idx in cmds_per_sequence:
        if idx[0] > maxNum:
            maxNum = idx[0]

    # initialize to zero
    cmds_per_seq_histogram=[0 for nn in range (maxNum)]

    for idx in cmds_per_sequence:
        nn = idx[0]-1
        cmds_per_seq_histogram[nn] = idx[1]

    return cmds_per_seq_histogram