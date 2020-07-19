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


# iterate through all msgDict in initialization to count commands
# the frame passed in just has rows from initIdx
def getPodInitCmdCount(frame):
    """
    Purpose: count commands in initialization attempt
             Return gain and rssi from pod 0x0115 if available

    Input:
        frame: DataFrame initialization messages

    Output:
       podInitCmdCount       message counts and other information

    """
    # initialize values for podInitCmdCount
    podInitCmdCount = {
        'timeStamp': frame.iloc[0]['time'],
        'deltaSec': frame.iloc[0]['deltaSec'],
        'gain': 0,
        'rssi': 0,
        'podAddr': 'n/a',
        'piVersion': 0,
        'lot': 0,
        'tid': 0,
        'PP115': 0,
        'lastPP': 0,
        'numInitSteps': len(frame),
        'cnt07': 0,
        'cnt03': 0,
        'cnt08': 0,
        'cnt19': 0,
        'cnt1a17': 0,
        'cnt1a13': 0,
        'cnt0e': 0,
        'cntACK': 0,
        'cnt0115': 0,
        'cnt011b': 0,
        'cnt1d': 0}

    # keep track of number of each type of message expected during pod init
    # (ack is not desired, but does happen)
    # for certain messages, update other dictionary values

    # iterate through the initialization DataFrame
    for index, row in frame.iterrows():
        # reset each time
        timeStamp = row['time']
        deltaSec = row['deltaSec']
        msgDict = row['msgDict']

        # now modify what happens based on msgType
        if msgDict['msgType'] == '0x07':
            podInitCmdCount['cnt07'] += 1

        elif msgDict['msgType'] == '0x0115':
            podInitCmdCount['cnt0115'] += 1
            podInitCmdCount['timeStamp'] = timeStamp
            podInitCmdCount['deltaSec'] = deltaSec
            podInitCmdCount['PP115'] = msgDict['pod_progress']
            podInitCmdCount['gain'] = msgDict['recvGain']
            podInitCmdCount['rssi'] = msgDict['rssiValue']
            podInitCmdCount['piVersion'] = msgDict['piVersion']
            podInitCmdCount['lot'] = msgDict['lot']
            podInitCmdCount['tid'] = msgDict['tid']
            podInitCmdCount['podAddr'] = msgDict['podAddr']

        elif msgDict['msgType'] == '0x03':
            podInitCmdCount['cnt03'] += 1
            podInitCmdCount['podAddr'] = msgDict['podAddr']

        elif msgDict['msgType'] == '0x011b':
            podInitCmdCount['cnt011b'] += 1
            podInitCmdCount['piVersion'] = msgDict['piVersion']
            podInitCmdCount['lot'] = msgDict['lot']
            podInitCmdCount['tid'] = msgDict['tid']
            podInitCmdCount['podAddr'] = msgDict['podAddr']

        elif msgDict['msgType'] == 'ACK':
            podInitCmdCount['cntACK'] += 1

        elif msgDict['msgType'] == '0x08':
            podInitCmdCount['cntACK'] += 1

        elif msgDict['msgType'] == '0x1d':
            podInitCmdCount['cnt1d'] += 1
            podInitCmdCount['lastPP'] = msgDict['pod_progress']

        elif msgDict['msgType'] == '0x19':
            podInitCmdCount['cnt19'] += 1

        elif msgDict['msgType'] == '0x1a17':
            podInitCmdCount['cnt1a17'] += 1

        elif msgDict['msgType'] == '0x1a13':
            podInitCmdCount['cnt1a13'] += 1

        elif msgDict['msgType'] == '0x0e':
            podInitCmdCount['cnt0e'] += 1

    return podInitCmdCount
