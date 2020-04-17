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
    # increment initIdx upon success matching msg_type and pod_progress
    # initIdx is the index into the expectMT and expectPP for initializaton
    initIdx = 0
    actualPP = -1
    podInitDict = getPodInitDict()
    statusOK = 1
    statusNotOK = 0
    ppMeaning = getPodProgressMeaning(actualPP)

    colNames = ('df_idx', 'timeStamp', 'time_delta', 'timeCumSec', \
                'seq_num', 'expectAction', 'expectMT', 'expectPP', \
                'status', 'actualMT', 'actualPP', \
                'ppMeaning', 'msg_body' )

    # iterate through the DataFrame
    for index, row in frame.iterrows():
        # reset each time
        timeStamp = row['time']
        time_delta = row['time_delta']
        timeCumSec += time_delta
        status = statusNotOK
        expectAction = podInitDict[initIdx][0]
        expectMT = podInitDict[initIdx][1]
        ppRange = podInitDict[initIdx][2]
        msg = row['msg_body']
        seq_num = row['seq_num']
        pmsg = processMsg(msg)

        actualMT = pmsg['msg_type']
        if 'pod_progress' in pmsg:
            actualPP = pmsg['pod_progress']
            ppMeaning = getPodProgressMeaning(actualPP)

        # check if message matches expected sequence
        if actualMT == expectMT and \
            ((actualPP >= ppRange[0]) or \
            (actualPP <= ppRange[-1]) ):
            status = statusOK
            initIdx = initIdx + 1
        elif expectMT == '1d':
            initIdx = max(0,initIdx-1)
        elif actualMT == '0x7':
            # restarting the pairing from the beginning
            initIdx = 1
        elif actualPP > ppRange[-1]:
            # pod moved on and message was not captured
            initIdx = 0
            while actualPP > ppRange[-1]:
                expectAction = podInitDict[initIdx][0]
                expectMT = podInitDict[initIdx][1]
                ppRange = podInitDict[initIdx][2]
                initIdx = initIdx+1

        list_of_states.append((index, timeStamp, time_delta, timeCumSec, \
                seq_num, expectAction, expectMT, ppRange, \
                status, actualMT, actualPP, ppMeaning, msg))

    podInitFrame = pd.DataFrame(list_of_states, columns=colNames)
    return podInitFrame
