from utils import *
from podUtils import *
from messagePatternParsing import *

## This file has higher level pod-specific functions

# iterate through all messages and apply parsers to update the pod state
# some messages are not parsed (they show up as 0x##)
def getPodState(frame):
    """
    Purpose: Evaluate state changes while the pod_progress is in range

    Input:
        frame: DataFrame with all messages

    Output:
       podStateFrame       dataframe with pod state extracted from messages
       emptyMessageList    indices of any messages with blank commands
       faultProcessedMsg   dictionary for the fault message

    """
    # initialize values for pod states that we will update
    timeCumSec = 0
    pod_progress = 0
    faultProcessedMsg = {}
    insulinDelivered = getUnitsFromPulses(0)
    reqTB = getUnitsFromPulses(0)
    reqBolus = getUnitsFromPulses(0)
    #extBo = False # since extended bolus is always false, don't put into dataframe
    Bolus = False
    TB    = False
    schBa = False
    emptyMessageList = []
    sendDict, recvDict = getMessageDict()
    list_of_recv = listFromDict(recvDict)
    radio_on_time = 30 # radio is on for 30 seconds every time pod wakes up
    radioOnCumSec = radio_on_time

    list_of_states = []

    colNames = ('df_idx', 'timeStamp', 'time_delta', 'timeCumSec', \
                'message_type', 'pod_progress', 'radioOnCumSec',\
                'insulinDelivered', 'reqTB', \
                'reqBolus', 'Bolus','TB','SchBasal', 'raw_value' )

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
            #continue
        else:
            pmsg = processMsg(msg)

        message_type = pmsg['message_type']
        if message_type == '02':
            faultProcessedMsg = pmsg

        timeAsleep = row['time_asleep']
        if np.isnan(timeAsleep):
            radioOnCumSec += time_delta
        else:
            radioOnCumSec += time_delta - timeAsleep

        # fill in pod state based on message_type
        if message_type == '1a16':
            reqTB = pmsg['temp_basal_rate_u_per_hr']

        elif message_type == '1a17':
            reqBolus = pmsg['prompt_bolus_u']

        elif message_type == '1d':
            pod_progress = pmsg['pod_progress']
            insulinDelivered = pmsg['insulinDelivered_delivered']
            Bolus = pmsg['immediate_bolus_active']
            TB    = pmsg['temp_basal_active']
            schBa = pmsg['basal_active']

        elif message_type == '1f':
            #Bolus = Bolus and not pmsg['cancelBolus']
            #TB    = TB and not pmsg['cancelTB']
            #schBa = schBa and not pmsg['suspend']
            # rename the message_type per Joe's request
            message_type = '1f0{:d}'.format(pmsg['cancelByte'])

        list_of_states.append((index, timeStamp, time_delta, timeCumSec, \
                              message_type, pod_progress, radioOnCumSec, \
                              insulinDelivered, reqTB, \
                              reqBolus, Bolus, TB, schBa, msg))

    podStateFrame = pd.DataFrame(list_of_states, columns=colNames)
    return podStateFrame, emptyMessageList, faultProcessedMsg

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
        # if a recieve is detected without a send, it goes here
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
