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


def analyzeAllPodsInDeviceLog(fileDict, loopReadDict, outFile, vFlag):
    """
        Purpose: break logDF into chunks for each pod in Report
                and process each chunk using analyzedPodMessages

        Input:
            fileDict - pass through to next function
            loopReadDict has keys:
                fileType "deviceLog" uses this preparser
                logDF complete set of hex pod messages read from report
                podMgrDict parsed from ## OmnipodPumpManager
                faultInfoDict parsed from ## PodInfoFaultEvent
                loopVersionDict parsed from ## LoopVersion
            outFile output file location (if needed)
            vFlag pass through selection for verbosity
    """
    logDF = loopReadDict['logDF']
    podMgrDict = loopReadDict['podMgrDict']
    faultInfoDict = loopReadDict['faultInfoDict']

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
        idx = idx+1
        stopRow = breakPoints[idx]-1
        thisFrame = logDF.loc[startRow:stopRow][:]
        startRow = stopRow+1

        print('  ----------------------------------------\n')
        print('  Report on Omnipod from {:s}'.format(fileDict['personFile']))
        print('     Block {:d} of {:d}\n'.format(idx, numChunks))

        analyzePodMessages(fileDict, thisFrame, podMgrDict, faultInfoDict,
                           outFile, vFlag, idx)

    return
