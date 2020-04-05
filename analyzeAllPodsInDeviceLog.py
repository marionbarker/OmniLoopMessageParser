import numpy as np
import pandas as pd
from utils import *
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

    # find the unique pod addresses
    podAddress = list(podFrame['address'].unique())
    frameLength = len(podFrame)
    if vFlag:
        print('Unique Pod Addresses, out of : {:6d} lines'.format(frameLength))
        print(podAddress)
    """
        If only one address is found,
            then startRow and stopRow will have only one value
        If noPod is found after first row,
            append that to startRow List
            pre-pend the previous row to stopRow List
    """
    firstRow = []
    startRow = 0 # initial value
    stopRow = frameLength # initial value
    for x in podAddress:
        mask = podFrame['address'] == x
        idx = next(iter(mask.index[mask]), 0)
        firstRow.append(idx)

    if len(firstRow) == 1:
        startRow = 0;
        stopRow = frameLength;
    else:
        # by definition, if there is more than one address, one must be noPod
        foundIt = 0;
        for x in firstRow:
            if podFrame['address'][x] == "noPod":
                startRow = x
                foundIt = 1
                print('Found noPod')
                print('startRow =', startRow)
            elif foundIt == 1:
                foundIt = foundIt+1
                print('incrementing')
            elif foundIt == 2:
                stopRow = x
                foundIt = 0
                print('stopRow =', stopRow)
                print('WARNING - more than on pod start in this file')

        # if noPod not found, this is an error
        if startRow == -1:
            print('ERROR - more than one address, did not find noPod')

    # use the selected start and stop rows to limit messages to single pod
    print('start and stopRows =', startRow, stopRow)

    podFrame = podFrame.iloc[startRow:stopRow][:]

    df, podState, actionFrame, actionSummary = analyzePodMessages(thisFile,
        podFrame, podDict, fault_report, outFile)

    return df, podState, actionFrame, actionSummary
