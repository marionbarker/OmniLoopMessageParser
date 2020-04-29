from utils import *
from utils_pd import *
from utils_pod import *
from messagePatternParsing import *

## This file has higher level pod-specific functions

# iterate through all messages and apply parsers to update the pod state
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

    colNames = ('logIdx', 'timeStamp', 'deltaSec', 'timeCumSec', \
                'seqNum', 'expectAction', 'expectMT', 'expectPP', \
                'statusBool', 'actualMT', 'actualPP', \
                'ppMeaning', 'msgDict', 'address' )

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
        seqNum = row['seqNum']
        address = row['address']

        actualMT = msgDict['msgType']

        if 'pod_progress' in msgDict:
            actualPP = msgDict['pod_progress']
            ppMeaning = getPodProgressMeaning(actualPP)

        # check if message matches expected sequence
        if actualMT == expectMT and \
            ((actualPP >= ppRange[0]) or \
            (actualPP <= ppRange[-1]) ):
            statusBool = True
            initIdx = initIdx + 1
        elif actualMT == '0x07' and initIdx >= 2:
            # restarting the pairing from the beginning
            initIdx = 1
            podInitDict = getPodInitRestartDict(restartType)
        elif expectMT == '0x1d':
            # did not get '0x1d' response from pod, back up one
            initIdx = max(0,initIdx-1)
        elif actualPP > ppRange[-1]:
            # pod moved on and message was not captured
            initIdx = 0
            while actualPP > ppRange[-1]:
                expectAction = podInitDict[initIdx][0]
                expectMT = podInitDict[initIdx][1]
                ppRange = podInitDict[initIdx][2]
                initIdx = initIdx+1

        list_of_states.append((index, timeStamp, deltaSec, timeCumSec, \
                seqNum, expectAction, expectMT, ppRange, \
                statusBool, actualMT, actualPP, ppMeaning, msgDict, address))

    podInitFrame = pd.DataFrame(list_of_states, columns=colNames)
    return podInitFrame
