from util.pod import getUnitsFromPulses
import numpy as np
import pandas as pd


# This file has higher level pod-specific functions

# iterate through all messages and apply parsers to update the pod state
# some messages are not parsed (they show up as 0x##)
def getPodState(frame):
    """
    Purpose: Evaluate state changes while the pod_progress is in range

    Input:
        frame: DataFrame with all messages

    Output:
       podStateFrame       dataframe with pod state extracted from messages
       ackMessageList    indices of any blank messages (ACK)
       faultProcessedMsg   dictionary for the fault message
       podInfo             dictionary for pod

    """
    # initialize values for pod states that we will update
    timeCumSec = 0
    podOnTime = 0
    pod_progress = 0
    faultProcessedMsg = {}
    insulinDelivered = getUnitsFromPulses(0)
    reqTB = getUnitsFromPulses(0)
    reqBolus = getUnitsFromPulses(0)
    # extBo = False # extended bolus is always false, don't put into dataframe
    # to make this print out nicely, use '' for FALSE, 'y' for TRUE
    # NOPE - have to have logic for checkAction to be valid
    Bolus = False
    TB = False
    schBa = False
    ackMessageList = []
    radio_on_time = 30  # radio is on for 30 seconds every time pod wakes up
    radioOnCumSec = radio_on_time

    podInfo = {}

    list_of_states = []

    colNamesMsg = ('logIdx', 'timeStamp', 'deltaSec', 'timeCumSec',
                   'radioOnCumSec', 'podOnTime', 'seqNum', 'pod_progress',
                   'type', 'msgType', 'msgMeaning', 'insulinDelivered',
                   'reqTB', 'reqBolus', 'Bolus', 'TB', 'SchBasal', 'address',
                   'msgDict')

    colNamesDev = ('logIdx', 'timeStamp', 'deltaSec', 'timeCumSec',
                   'radioOnCumSec', 'podOnTime', 'seqNum', 'pod_progress',
                   'type', 'msgType', 'msgMeaning', 'insulinDelivered',
                   'reqTB', 'reqBolus', 'autoBolus', 'Bolus', 'TB', 'SchBasal',
                   'logAddr', 'address', 'msgDict')

    # iterate through the DataFrame
    for index, row in frame.iterrows():
        # reset each time
        timeStamp = row['time']
        deltaSec = row['deltaSec']
        timeCumSec += deltaSec
        msgDict = row['msgDict']
        seqNum = msgDict['seqNum']
        msgMeaning = msgDict['msgMeaning']
        autoBolus = False
        if msgDict['msgType'] == 'ACK':
            ackMessageList.append(index)

        msgType = msgDict['msgType']
        if msgType == '0x0202':
            faultProcessedMsg = msgDict

        timeAsleep = row['timeAsleep']
        if np.isnan(timeAsleep):
            radioOnCumSec += deltaSec
        else:
            radioOnCumSec += deltaSec - timeAsleep

        # fill in pod state based on msgType
        if msgType == '0x1a16':
            reqTB = msgDict['temp_basal_rate_u_per_hr']

        elif msgType == '0x1a17':
            reqBolus = msgDict['prompt_bolus_u']
            autoBolus = msgDict['autoBolus']

        elif msgType == '0x1d':
            pod_progress = msgDict['pod_progress']
            insulinDelivered = msgDict['insulinDelivered']
            Bolus = msgDict['immediate_bolus_active']
            TB = msgDict['temp_basal_active']
            schBa = msgDict['basal_active']
            podInfo['podOnTime'] = msgDict['podOnTime']
            podOnTime = msgDict['podOnTime']

        elif msgType == '0x0115':
            pod_progress = msgDict['pod_progress']
            podInfo['piVersion'] = msgDict['piVersion']
            podInfo['lot'] = str(msgDict['lot'])
            podInfo['tid'] = str(msgDict['tid'])
            podInfo['address'] = msgDict['podAddr']
            podInfo['recvGain'] = msgDict['recvGain']
            podInfo['rssiValue'] = msgDict['rssiValue']

        elif msgType == '0x011b':
            pod_progress = msgDict['pod_progress']
            podInfo['piVersion'] = msgDict['piVersion']
            podInfo['lot'] = str(msgDict['lot'])
            podInfo['tid'] = str(msgDict['tid'])
            podInfo['address'] = msgDict['podAddr']

        if row.get('logAddr'):
            colNames = colNamesDev
            list_of_states.append((index, timeStamp, deltaSec, timeCumSec,
                                  radioOnCumSec, podOnTime, seqNum,
                                  pod_progress, row['type'], msgType,
                                  msgMeaning, insulinDelivered, reqTB,
                                  reqBolus, autoBolus, Bolus, TB, schBa,
                                  row['logAddr'], row['address'], msgDict))
        else:
            colNames = colNamesMsg
            list_of_states.append((index, timeStamp, deltaSec, timeCumSec,
                                  radioOnCumSec, podOnTime, seqNum,
                                  pod_progress, row['type'], msgType,
                                  msgMeaning, insulinDelivered, reqTB,
                                  reqBolus, Bolus, TB, schBa,
                                  row['address'], msgDict))

    podStateFrame = pd.DataFrame(list_of_states, columns=colNames)
    return podStateFrame, ackMessageList, faultProcessedMsg, podInfo
