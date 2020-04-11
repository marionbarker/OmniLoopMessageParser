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

def analyzeAllPodsInDeviceLog(thisFile, podFrame, podDict, fault_report, outFile, vFlag):
    # break podFrame into chunks and process each chunk
    podAddress, breakPoints = findBreakPoints(podFrame)

    numChunks = len(breakPoints)-1

    idx = 0
    startRow = breakPoints[idx]
    for val in breakPoints:
        idx = idx+1
        if idx > numChunks:
            break
        stopRow = breakPoints[idx]-1
        thisFrame = podFrame.loc[startRow:stopRow][:]
        startRow = stopRow+1

        print('__________________________________________\n')
        print('  Report on Omnipod from {:s}'.format(thisFile))
        print('     Block {:d} of {:d}\n'.format(idx, numChunks))

        df, podState, actionFrame, actionSummary = analyzePodMessages(thisFile,
            thisFrame, podDict, fault_report, outFile, vFlag)

    return df, podState, actionFrame, actionSummary
