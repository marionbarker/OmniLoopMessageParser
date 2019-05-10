from utils import *
from podUtils import *

# only used by this deprecated function

def getMessageDict():
    # this is the list of messages that might be sent or received
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


## This file has functions used by analyzeMessageLogsNew but not needed
#  for analyzeMessageLogsRev3

def getPodSuccessfulActions(frame):
    """
    Purpose: Evaluate each request from the dictionary

    Input:
        frame: output from getPodState code

    Output:
        podRequestSuccess  dataframe with successful responses to requests
        podOtherMessages   all other messages
    """
    list_of_success = []  # success for items in list_of_requests
    list_of_other   = []  # all other or unpaired messages
    nextIndex = -1
    sendDict, recvDict = getMessageDict()
    list_of_recv = listFromDict(recvDict)

    successColumnNames = ('list_of_df_idx',  \
      'startTimeStamp', 'startCumSec', 'startMessage', 'endMessage', \
      'endPodProgress', 'responseTime', 'radioOnCumSec', 'insulinDelivered', \
      'reqTB', 'reqBolus', 'Bolus','TB','SchBasal' )
    otherColumnNames = ('df_idx', 'start_podState_idx', 'startTimeStamp', 'startMessage' )

    # for the iterrows index and nextIndex to work requires index reset
    frame = frame.reset_index()

    # iterate looking for requests and successful responses
    for index, row in frame.iterrows():
        if index <= nextIndex or index >= len(frame)-1:
            continue
        # set up params we need for either case
        startTimeStamp = row['timeStamp']
        startMessage   = row['message_type']
        startCumSec = row['timeCumSec']
        # if a receive is detected without a send, it goes here
        if startMessage in list_of_recv:
            nextIndex = index
            list_of_other.append((row['df_idx'], index, startTimeStamp, startMessage))
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
            newRow = frame.iloc[nextIndex]

            # was the next message the expected response
            if  newRow['message_type'] == respMessage:
                didSucceed = True

            if didSucceed:
                list_of_df_idx = [row['df_idx'], newRow['df_idx']]
                list_of_success.append((list_of_df_idx, startTimeStamp, \
                  startCumSec, startMessage, respMessage, row['pod_progress'], \
                  newRow['time_delta'], newRow['radioOnCumSec'], newRow['insulinDelivered'], \
                  newRow['reqTB'], newRow['reqBolus'], \
                  newRow['Bolus'], newRow['TB'], newRow['SchBasal']))
            else:
                list_of_other.append((row['df_idx'], index, startTimeStamp, startMessage))
                nextIndex = index # decrement so we don't skip the next message

    podRequestSuccess = pd.DataFrame(list_of_success, columns=successColumnNames)
    podOtherMessages = pd.DataFrame(list_of_other, columns=otherColumnNames)

    return podRequestSuccess, podOtherMessages

def doThePrintSuccess(frame):
    if len(frame) == 0:
        return
    print('    Successful Request Messages with Appropriate Pod Response:')
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
    print('    Send Messages without expected Receive:')
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
