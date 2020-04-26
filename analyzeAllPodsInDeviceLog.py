import numpy as np
import pandas as pd
from utils import *
from utils_pd import *
from analyzePodMessages import *

"""
analyzeAllPodsInDeviceLog
    This pre-parser selects pod messages from Device Communications
    Logic: Split podFrame by logAddress=noPod, address=ffffffff
    Scenarios:
        address1 : group 1
        noPod/ffffffff + address2: group 2
        noPod/ffffffff + address3: group 3, etc
"""

def analyzeAllPodsInDeviceLog(thisFile, podFrame, podDict, fault_report, outFile, vFlag):
    # break podFrame into chunks and process each chunk
    #  unique address list, breakPoints in podFrame
    podAddresses, breakPoints = findBreakPoints(podFrame)

    numChunks = len(breakPoints)-1

    idx = 0
    startRow = breakPoints[idx]
    for val in breakPoints:
        if idx > numChunks-1:
            continue
        # overwrite the pod address with value within the breakPoints
        if 'address' in podDict:
            podDict['address'] = podAddresses[idx]
        idx = idx+1
        stopRow = breakPoints[idx]-1
        thisFrame = podFrame.loc[startRow:stopRow][:]
        startRow = stopRow+1

        print('__________________________________________\n')
        print('  Report on Omnipod from {:s}'.format(thisFile))
        print('     Block {:d} of {:d}'.format(idx, numChunks))

        df, podState, actionFrame, actionSummary = analyzePodMessages(thisFile,
            thisFrame, podDict, fault_report, outFile, vFlag, idx)

        if vFlag == 4:
            thisOutFile = 'm:/SharedFiles/LoopReportPythonAnalysis' + '/' \
                + 'verboseOutput' + '/' + 'full_df_out_' + str(idx) + '.csv'
            print('  Sending this chunk of df details to \n    ',thisOutFile)
            df.to_csv(thisOutFile)

    return df, podState, actionFrame, actionSummary
