import numpy as np
import pandas as pd
from utils import *
from utils_pd import *
from analyzePodMessages import *

"""
analyzeAllPodsInDeviceLog
    This pre-parser selects pod messages from Device Communications
    Logic: Split podFrame by address=noPod
    Scenarios:
        address1 : group 1
        noPod + address2: group 2
        noPod + address3: group 3, etc
"""

def analyzeAllPodsInDeviceLog(thisFile, podFrame, podDict, fault_report, outFile):
    # Put in debug printout grouped by vFlag
    vFlag = 1;

    # break podFrame into chunks and process each chunk
    podAddress, breakPoints = findBreakPoints(podFrame)

    frameLength = len(podFrame)
    if vFlag:
        print('Unique Pod Addresses, out of : {:6d} lines'.format(frameLength))
        print(podAddress)
        print('Break Points are at rows:')
        print(breakPoints)

    idx = 0
    startRow = breakPoints[idx]
    for val in breakPoints:
        idx = idx+1
        if idx >= len(breakPoints):
            break
        stopRow = breakPoints[idx]-1
        thisFrame = podFrame.loc[startRow:stopRow][:]
        startRow = stopRow+1
        print(thisFrame.head(2))
        print(thisFrame.tail(2))

        df, podState, actionFrame, actionSummary = analyzePodMessages(thisFile,
            thisFrame, podDict, fault_report, outFile)

    return df, podState, actionFrame, actionSummary
