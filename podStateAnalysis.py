from utils import *
from messagePatternParsing import *

## This file has pod-specific functions

# This is from Eelke
def basal_analysis(df):
  # add analysis per Eelke (2/27 and 3/2/2019 )

  # Add time between TBs
  df['time_diff_tbs'] = time_difference(df.loc[df['command']=='1a16']['time'])

  # Add time column a normal basal was running before this TB
  df["normal_basal_running_seconds"] = df.loc[df['time_diff_tbs'] > 30 * 60]['time_diff_tbs'] - (30 * 60)
  df_basals = df[df["normal_basal_running_seconds"].notnull()]

  # Normal basals running
  df_basals["normal_basal_running_time"]= df_basals["normal_basal_running_seconds"].astype(int).apply(to_time)
  # Previous 2 values of first TB send after >30 minutes
  df2 = df.loc[(df.normal_basal_running_seconds < 30),["time","command","normal_basal_running_seconds", "raw_value"]]
  df2 = df2.append(df[df.normal_basal_running_seconds.shift(-3) < 30].loc[:,["time","command","normal_basal_running_seconds", "raw_value"]])
  df2 = df2.append(df[df.normal_basal_running_seconds.shift(-2) < 30].loc[:,["time","command","normal_basal_running_seconds", "raw_value"]])
  df2 = df2.append(df[df.normal_basal_running_seconds.shift(-1).notnull()].loc[:,["time","command","normal_basal_running_seconds", "raw_value"]])

  return df_basals, df2

# marion's code starts here
# iterate through all messages and apply parsers to update the pod state
# some messages are not parsed (they show up as 0x##)
def getPodState(frame):
    """
    Purpose: Evaluate state changes while the pod_progress is in range

    Input:
        frame: DataFrame with all messages

    Output:
       podStateFrame    dataframe with pod state extracted from messages
       emptyMessageList indices of any messages with blank commands

    """
    # initialize values for pod states that we will update
    timeCumSec = 0
    pod_progress = 0
    total_insulin = getUnitsFromPulses(0)
    lastTB = getUnitsFromPulses(0)
    lastBolus = getUnitsFromPulses(0)
    #extBo = False # since extended bolus is always false, don't put into dataframe
    Bolus = False
    TB    = False
    schBa = False
    emptyMessageList = []
    sendDict, recvDict = getMessageDict()
    list_of_recv = listFromDict(recvDict)
    radio_on_time = 30 # radio is on for 30 seconds every time pod wakes up
    radioOnCumTime = radio_on_time

    list_of_states = []

    colNames = ('df_idx', 'timeStamp', 'time_delta', 'timeCumSec', \
                'message_type', 'pod_progress', 'radioOnCumTime',\
                'total_insulin', 'lastTB', \
                'lastBolus', 'Bolus','TB','SchBasal', 'raw_value' )

    # iterate through the DataFrame, should already be sorted into send-recv pairs
    for index, row in frame.iterrows():
        # reset each time
        timeStamp = row['time']
        time_delta = row['time_delta']
        timeCumSec += time_delta
        msg = row['raw_value']
        if msg == '':
            #print('Empty command for {} at dataframe index of {:d}'.format(row['type'], index))
            pmsg = {}
            pmsg['message_type'] = 'unknown'
            emptyMessageList.append(index)
            continue
        else:
            pmsg = processMsg(msg)

        message_type = pmsg['message_type']

        timeAsleep = row['time_asleep']
        if np.isnan(timeAsleep):
            radioOnCumTime += time_delta
        else:
            radioOnCumTime += time_delta - timeAsleep

        # fill in pod state based on message_type
        if message_type == '1a16':
            lastTB = pmsg['temp_basal_rate_u_per_hr']

        elif message_type == '1a17':
            lastBolus = pmsg['prompt_bolus_u']

        elif message_type == '1d':
            pod_progress = pmsg['pod_progress']
            total_insulin = pmsg['total_insulin_delivered']
            Bolus = pmsg['immediate_bolus_active']
            TB    = pmsg['temp_basal_active']
            schBa = pmsg['basal_active']

        elif message_type == '1f':
            Bolus = Bolus and not pmsg['cancelBolus']
            TB    = TB and not pmsg['cancelTB']
            schBa = schBa and not pmsg['suspend']
            # rename the message_type per Joe's request
            message_type = '1f0{:d}'.format(pmsg['cancelByte'])

        list_of_states.append((index, timeStamp, time_delta, timeCumSec, \
                              message_type, pod_progress, radioOnCumTime, \
                              total_insulin, lastTB, \
                              lastBolus, Bolus, TB, schBa, msg))

    podStateFrame = pd.DataFrame(list_of_states, columns=colNames)
    return podStateFrame, emptyMessageList

def getMessageDict():
    # this is the list of messages that might be sent or recieved
    # sendDict { 'sendMsg' : ('expectedRecvMsg', 'sendName')}

    sendDict = { \
      '0x3'  : ('0x1', 'SetupPod'), \
      '0x7'  : ('0x1', 'AssignID'), \
      '0x8'  : ('1d', 'CnfgDelivFlags'), \
      '0e'   : ('1d', 'StatusRequest'), \
      '0x11' : ('1d', 'AcknwlAlerts'), \
      '0x19' : ('1d', 'CnfgAlerts'), \
      '0x1c' : ('1d', 'DeactivatePod'), \
      '0x1e' : ('1d', 'DiagnosePod'), \
      '1a13' : ('1d', 'Basal'), \
      '1a16' : ('1d', 'TB'), \
      '1a17' : ('1d', 'Bolus'),
      '1f'   : ('1d', 'CancelDelivery'),
      '1f01' : ('1d', 'CancelBasal'),
      '1f02' : ('1d', 'CancelTB'),
      '1f04' : ('1d', 'CancelBolus'),
      '1f07' : ('1d', 'CancelAll')
       }

    recvDict = { \
      '0x1'  : 'VersionResponse', \
      '1d'   : 'StatusResponse', \
      '06'   : 'NonceResync', \
      '02'   : 'Fault'}

    return sendDict, recvDict

def getCompleteDict():
    sendDict, recvDict = getMessageDict()
    completeDict = {}
    sendDictNames = {}
    for keys, values in sendDict.items():
        completeDict[keys] = values[1]
        sendDictNames[keys] = values[1]
    for keys, values in recvDict.items():
        completeDict[keys] = values
    return completeDict, sendDictNames, recvDict

def getPodSuccessfulActions(podStateFrame):
    """
    WARNING - podStateFrame must start with 0 index or iterrows index is out of sycn
              probably a better way to get the next row
    Purpose: Evaluate each request from the dictionary

    Input:
        podStateFrame: output from getPodState code applied to all messages (df)

    Output:
        podRequestSuccess  dataframe with successful responses to requests
        podOtherMessages   all other messages
    """
    list_of_success = []  # success for items in list_of_requests
    list_of_other   = []  # all other or unpaired messages
    nextIndex = -1
    sendDict, recvDict = getMessageDict()
    list_of_recv = listFromDict(recvDict)

    successColumnNames = ('start_df_idx', 'start_podState_idx', 'end_podState_idx', \
      'startTimeStamp', 'start_timeCumSec', 'startMessage', 'endMessage', \
      'end_pod_progress', 'responseTime', 'radioOnCumTime', 'total_insulin', \
      'lastTB', 'lastBolus', 'Bolus','TB','SchBasal' )
    otherColumnNames = ('start_df_idx', 'start_podState_idx', 'startTimeStamp', 'startMessage' )

    # iterate looking for requests and successful responses
    for index, row in podStateFrame.iterrows():
        if index <= nextIndex or index >= len(podStateFrame)-1:
            continue
        # set up params we need for either case
        start_df_idx   = row['df_idx']
        startTimeStamp = row['timeStamp']
        startMessage   = row['message_type']
        start_timeCumSec = row['timeCumSec']
        # if a recieve is detected without a send, it goes here
        if startMessage in list_of_recv:
            nextIndex = index
            list_of_other.append((start_df_idx, index, startTimeStamp, startMessage))
        # was in list_of_requests, look for successful return message
        # look for desired response, then once it's determined which this is, append to appropriate list
        else:
            # use the sendDict to determine expected response
            # reset the response message (avoid getting out sync)
            respMessage = []
            for keys, values in sendDict.items():
              if startMessage == keys:
                respMessage = values[0]
                break

            # increment to read next message
            nextIndex = index + 1
            # initialize for failure, then change if next message is correct
            didSucceed = False
            newRow = podStateFrame.iloc[nextIndex] ## << bad code, works iff podStateFrame starts with 0 index and indices are sequential

            # was the next message the expected response
            if  newRow['message_type'] == respMessage:
                didSucceed = True

            if didSucceed:
                list_of_success.append((start_df_idx, index, nextIndex, startTimeStamp, \
                  start_timeCumSec, startMessage, respMessage, row['pod_progress'], \
                  newRow['time_delta'], newRow['radioOnCumTime'], newRow['total_insulin'], \
                  newRow['lastTB'], newRow['lastBolus'], \
                  newRow['Bolus'], newRow['TB'], newRow['SchBasal']))
            else:
                list_of_other.append((start_df_idx, index, startTimeStamp, startMessage))
                nextIndex = index # decrement so we don't skip the next message

    podRequestSuccess = pd.DataFrame(list_of_success, columns=successColumnNames)
    podOtherMessages = pd.DataFrame(list_of_other, columns=otherColumnNames)

    return podRequestSuccess, podOtherMessages


def doThePrintSuccess(frame):
    if len(frame) == 0:
        return
    print('    Successful Request with Appropriate Pod Response:')
    completeDict, sendDictNames, recvDict = getCompleteDict()
    print('      Request(code)           : #Requests, mean, [ min, max ], response time (sec) ')
    for keys,values in completeDict.items():
        thisSel   = frame[frame.startMessage==keys]
        numberSel = len(thisSel)
        if numberSel == 1:
            print('      {:14s} ({:4s})   : {:5d}, {:5.1f}'.format(values, \
                keys, numberSel, thisSel['responseTime'].mean()))
        elif numberSel > 1:
            print('      {:14s} ({:4s})   : {:5d}, {:5.1f}, [ {:5.1f}, {:5.1f} ]'.format(values, \
                keys, numberSel, thisSel['responseTime'].mean(), \
                thisSel['responseTime'].min(), thisSel['responseTime'].max() ))
    return


def doThePrintOther(frame):
    if len(frame) == 0:
        return
    completeDict, sendDictNames, recvDict = getCompleteDict()
    print('    Send without expected Receive:')
    print('      Message(code)  : #Messages')
    for keys,values in sendDictNames.items():
        thisSel   = frame[frame.startMessage==keys]
        numberSel = len(thisSel)
        if numberSel:
            print('      {:14s} ({:4s})   : {:5d}'.format(values, keys, numberSel))
    print('    Off-nominal Receive Messages:')
    print('      Message(code)  : #Messages')
    for keys,values in recvDict.items():
        thisSel   = frame[frame.startMessage==keys]
        numberSel = len(thisSel)
        if numberSel:
            print('      {:14s} ({:4s})   : {:5d}'.format(values, keys, numberSel))
    return
