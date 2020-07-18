from util.pod import getPodProgressMeaning, getPodInitDict
from util.pod import getPodInitRestartDict
import pandas as pd

# This file has higher level pod-specific functions


# iterate through all msgDict to update the pod state
# some messages are not parsed (they show up as 0x##)
def getInitState(frame):
    """
    Purpose: Evaluate pod initialition process

    Input:
        frame: DataFrame initialization messages

    Output:
       podInitFrame       dataframe with init pod state

    """
    # initialize values for pod states that we will update
    list_of_states = []
    timeCumSec = 0
    # increment initIdx upon success matching msgType and pod_progress
    # initIdx is the index into the expectMT and expectPP for initializaton
    initIdx = 0
    actualPP = 0
    ppMeaning = getPodProgressMeaning(actualPP)
    podInitDict = getPodInitDict()
    # if need to restart sequence, then need updated podInitDict
    # currently, there is only one restartType
    restartType = 0

    colNames = ('logIdx', 'timeStamp', 'deltaSec', 'timeCumSec',
                'seqNum', 'expectAction', 'expectMT', 'expectPP',
                'statusBool', 'actualMT', 'actualPP',
                'ppMeaning', 'msgDict', 'address')

    # iterate through the DataFrame
    for index, row in frame.iterrows():
        # reset each time
        timeStamp = row['time']
        deltaSec = row['deltaSec']
        timeCumSec += deltaSec
        statusBool = False
        initIdx = min(initIdx, len(podInitDict)-1)
        expectAction = podInitDict[initIdx][0]
        expectMT = podInitDict[initIdx][1]
        ppRange = podInitDict[initIdx][2]
        msgDict = row['msgDict']
        # prevent excel from treating 1e as exponent
        seqNum = msgDict['seqNum']
        address = row['address']

        actualMT = msgDict['msgType']

        if 'pod_progress' in msgDict:
            actualPP = msgDict['pod_progress']
            ppMeaning = getPodProgressMeaning(actualPP)

        # check if message matches expected sequence
        if actualMT == expectMT and \
            ((actualPP >= ppRange[0]) or
             (actualPP <= ppRange[-1])):
            statusBool = True
            initIdx = initIdx + 1
        elif actualMT == '0x07' and initIdx >= 2:
            # restarting the pairing from the beginning
            initIdx = 1
            podInitDict = getPodInitRestartDict(restartType)
        elif expectMT == '0x1d':
            # did not get '0x1d' response from pod, back up one
            initIdx = max(0, initIdx-1)
        elif actualPP > ppRange[-1]:
            # pod moved on and message was not captured
            initIdx = 0
            while actualPP > ppRange[-1]:
                expectAction = podInitDict[initIdx][0]
                expectMT = podInitDict[initIdx][1]
                ppRange = podInitDict[initIdx][2]
                initIdx = initIdx+1

        list_of_states.append((index, timeStamp, deltaSec, timeCumSec,
                               seqNum, expectAction, expectMT, ppRange,
                               statusBool, actualMT, actualPP, ppMeaning,
                               msgDict, address))

    podInitFrame = pd.DataFrame(list_of_states, columns=colNames)
    return podInitFrame


# iterate through all msgDict to extract gain and rssi from 0x0115 responses
def getPod0x0115Response(frame):
    """
    Purpose: Return gain and rssi from pod 0x0115 response(s)

    Input:
        frame: DataFrame initialization messages

    Output:
       pod0x115Response       dataframe gain and rssi

    """
    # initialize values for pod states that we will update
    list_of_states = []
    timeCumSec = 0
    num07 = 0
    num03 = 0
    num08 = 0
    num0115 = 0

    colNames = ('timeStamp', 'timeCumSec',
                'recvGain', 'rssiValue', 'piVersion', 'pod_progress',
                'lot', 'tid', 'address', 'podAddr', 'msgDict')

    # iterate through the DataFrame
    for index, row in frame.iterrows():
        # reset each time
        timeStamp = row['time']
        deltaSec = row['deltaSec']
        timeCumSec += deltaSec
        msgDict = row['msgDict']
        address = row['address']

        if msgDict['msgType'] == '0x07':
            num07 += 1

        elif msgDict['msgType'] == '0x03':
            num03 += 1

        elif msgDict['msgType'] == '0x08':
            num08 += 1

        elif msgDict['msgType'] == '0x0115':
            num0115 += 1
            list_of_states.append((timeStamp, timeCumSec, msgDict['recvGain'],
                                   msgDict['rssiValue'], msgDict['piVersion'],
                                   msgDict['pod_progress'], msgDict['lot'],
                                   msgDict['tid'], address, msgDict['podAddr'],
                                   msgDict))

    pod0x0115Response = pd.DataFrame(list_of_states, columns=colNames)
    pod0x0115Response['num07'] = num07
    pod0x0115Response['num03'] = num03
    pod0x0115Response['num08'] = num08
    pod0x0115Response['num0115'] = num0115
    return pod0x0115Response
