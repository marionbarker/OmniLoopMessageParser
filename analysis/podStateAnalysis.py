from util.pod import getUnitsFromPulses
from util.pod import getFaultMsg
import numpy as np
import pandas as pd


# Iterate through all messages and apply parsers to update the podState.
# If a state is not updated by a given message, the last value for that state
# is carried forward
def getPodState(frame):
    """
    Purpose: Evaluate state changes while the pod_progress is in range

    Input:
        frame: DataFrame with all messages

    Output:
       podStateFrame       dataframe with pod state extracted from messages
       faultProcessedMsg   dictionary for the fault message, if present

    """
    # initialize values for pod states that we will update
    timeCumSec = -frame.iloc[0]['deltaSec']
    podOnTime = 0
    pod_progress = 0
    faultProcessedMsg = {}
    insulinDelivered = getUnitsFromPulses(0)
    reqTB = getUnitsFromPulses(0)
    reqBolus = getUnitsFromPulses(0)
    # extBo = False # extended bolus is always false, don't put into dataframe
    Bolus = False
    TB = False
    schBa = False
    radio_on_time = 30  # radio is on for 30 seconds every time pod wakes up
    radioOnCumSec = radio_on_time

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

        msgType = msgDict['msgType']
        if msgType == '0x0202':
            faultProcessedMsg = getFaultMsg(msgDict)

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
            podOnTime = msgDict['podOnTime']

        elif msgType == '0x0115':
            pod_progress = msgDict['pod_progress']

        elif msgType == '0x011b':
            pod_progress = msgDict['pod_progress']

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
    return podStateFrame, faultProcessedMsg
