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

from utils import *

# read the file from the file_path (replace Eelke's original load_file(file_url))

def read_file(filename):
    commands = []
    file = open(filename)
    # limit the number of characters to read
    # this seems to be required from some files, ad-hoc maxChars to work
    #maxChars = 100*2900 # needed this for someone - but not enough for Theresa on 3/12/2019
    # so restore the 3400 I had earlier - see if Eelke can help with this one
    maxChars = 100*3400
    maxChars = 100*4000 # for theresa 3/15 report 
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
# separating out the send only sequences (assumes pod is out of range)
#  3/2/2019 - protect against the corner case of initial failure to pairs
#             followed by success, e.g., 'Marion/Loop Report 2019-02-06 18_38_18-08_00_Pod27_Nominal.md'
def generate_sequence(frame):
    """
    Purpose: Return two lists of lists of indices into the DataFrame

    Input:
        frame: DataFrame just created by generate_table

    Output:
       list_of_sequences : list of lists for send-receive pairs where all
                    s/r pairs within the radio-on time are in one sequence
       list_of_send_only : list of lists of send without a response
                          where adjacent sends are grouped together

    """
    # These two will hold the smaller lists (sequence and send_only)
    list_of_sequences = []
    list_of_send_only = []
    list_of_empty = []

    # These two hold indices as long as criteria are true and then are reset
    sequence = []
    send_only = []

    # iterate through the DataFrame
    for index, row in frame.iterrows():
        # first remove any messages with an empty string
        if row['raw_value'] == '':
            list_of_empty.append(index)
            continue

        # check if this is a send and if the next message also a send
        nextIdx = min(index+1,len(frame)-1)
        secondIdx = min(index+2,len(frame)-1)
        if row['type'] == 'send' and frame.iloc[nextIdx]['type'] == 'send':
            send_only.append(index)
            if frame.iloc[secondIdx]['type'] == 'receive':
                list_of_send_only.append(send_only)
                send_only = []
            # this case is when frame ends with 2 or more send
            elif secondIdx == nextIdx:
                list_of_send_only.append(send_only)
                if sequence != list_of_sequences[-1]:
                    list_of_sequences.append(sequence)
            continue
        # this is part of a send-recieve pair, if time_asleep is nan,
        #   radio is still on, so add to current sequence
        if pd.isna(row['time_asleep']):
            sequence.append(index)
        # radio is off, therefore append sequence to list_of_sequences,
        # and start a new sequence - ensure sequence is NOT empty
        else:
            if sequence:
              list_of_sequences.append(sequence)
            del(sequence)
            sequence = []
            sequence.append(index)
        # capture the final pair if ending in send/receive
        if nextIdx == secondIdx and sequence != list_of_sequences[-1]:
            list_of_sequences.append(sequence)

    return list_of_sequences, list_of_send_only, list_of_empty

# prepare of list of the number of individual commands in each sequence
# this returns tuples of [number of commands in a sequence, number of sequences with that length]
def count_cmds_per_sequence(list_of_sequences):
    sequence_counter = Counter()
    for sequence in list_of_sequences:
        sequence_counter[len(sequence)] += 1

    return list(sequence_counter.items())

# Prepare an array of the time since pod started to the first command in each
# sequence and the number of commands in that sequence. This function has been
# expanded in scope but not renamed.
def create_time_vs_sequenceLength(frame, list_of_sequences, radio_on_time):
    """
    Returns a list of tuples
      (time since first message, cummulative radio on time,
       length of sequence, average response time for this sequence)

    PARAMS:
        frame (pandas.DataFrame): The pandas dataframe of messages
        list_of_sequences (list): The list of sequences from generate_sequence()
        radio_on_time: time in sec that Pod radio stays on once awake

    RETURNS:
        time_vs_sequenceLength (list):
          list of tuples (
              cummulative time (hours) since pod start,
              cummulative time (hours) pod radio is awake
              number of send-recv messages in this sequence,
              average reponse time (recv-send) in this sequence
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
        pod_radio_awake_time += thisTime

        idx = 1
        responseTime = 0
        while idx < seqLength:
            responseTime += frame.iloc[sequence[idx]]['time_delta']
            idx += 2
        responseTime = 2*responseTime/seqLength

        time_vs_sequenceLength.append((time_since_beginning_hrs, pod_radio_awake_time, seqLength, responseTime))

    return time_vs_sequenceLength

# parse the information in the filename
def parse_info_from_filename(filename):
    val = '^.*/'
    thisPerson = re.findall(val, filename)
    if not thisPerson:
        thisPerson = 'Unknown'
    else:
        thisPerson = thisPerson[0] [0:-1]

    finishValues = {'0x12', '0x14', '0x31', '0x34', '0x40', '0x42', '0x80', 'Nominal'}
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
    totalMsg = 0;
    for idx in cmds_per_sequence:
        totalMsg += idx[0]*idx[1]
        if idx[0] > maxNum:
            maxNum = idx[0]

    # initialize to zero
    cmds_per_seq_histogram=[0 for nn in range (maxNum)]

    for idx in cmds_per_sequence:
        nn = idx[0]-1
        cmds_per_seq_histogram[nn] = idx[1]

    return cmds_per_seq_histogram, totalMsg
