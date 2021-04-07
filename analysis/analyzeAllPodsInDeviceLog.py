from util.pd import findBreakPoints
from analysis.analyzePodMessages import analyzePodMessages

"""
analyzeAllPodsInDeviceLog
    This pre-parser selects pod messages from Device Communications
    Logic: Split podFrame by logAddress=noPod, address=ffffffff
    Scenarios:
        address1 : group 1
        noPod/ffffffff + address2: group 2
        noPod/ffffffff + address3: group 3, etc
"""


def analyzeAllPodsInDeviceLog(fileDict, loopReadDict, outFlag, vFlag):
    """
        Purpose: break logDF into chunks for each pod in Report
                and process each chunk using analyzedPodMessages

        Input:
            fileDict - pass through to next function
            loopReadDict use these keys:
                logDF complete set of hex pod messages read from report
                podMgrDict parsed from ## OmnipodPumpManager
            outFlag used to route output (if needed)
            vFlag pass through selection for verbosity
    """
    logDF = loopReadDict['logDF']
    podMgrDict = loopReadDict['podMgrDict']

    podAddresses, breakPoints = findBreakPoints(logDF)

    numChunks = len(breakPoints)-1

    idx = 0
    startRow = breakPoints[idx]
    for val in breakPoints:
        if idx > numChunks-1:
            continue
        # overwrite the pod address with value within the breakPoints
        if 'address' in podMgrDict:
            podMgrDict['address'] = podAddresses[idx]
        idx = idx + 1
        stopRow = breakPoints[idx] - 1
        podFrame = logDF.loc[startRow:stopRow][:]
        podFrame[startRow, 'deltaSec'] = 0

        startRow = stopRow + 1

        print('  ----------------------------------------\n')
        print(f'  Report on Omnipod from {fileDict["personFile"]}')
        print(f'     Block {idx} of {numChunks}\n')

        analyzePodMessages(fileDict, podFrame, podMgrDict, outFlag, vFlag, idx)

    return
