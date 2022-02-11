from parsers.messageLogs_functions import generate_table
from util.misc import printDict
from util.report import writePodInitCmdCountToOutputFile, printInitFrame
from util.report import printPodInfo, printPodDict, printLogInfoSummary
from util.report import printActionSummary
from util.report import writeDescriptivePodStateToOutputFile
from util.report import printUncategorizedMessages
from util.report import writeDashStats
from util.pod import getLogInfoFromState
from analysis.podStateAnalysis import getPodState
from analysis.podInitAnalysis import getPodInitCmdCount
from analysis.checkAction import checkAction, processActionFrame

"""
analyzePodMessages
    This code analyzes a single Pod with messages in podFrame
"""


def analyzePodMessages(fileDict, podFrame, podDict, outFlag,
                       vFlag, chunkNum):
    """
    preprocess podFrame to be from a single pod
    vFlag
     : 0: output analysis to terminal window
     : 1: deprecated
     : 2: like 0, + printPodInitFrame if exceeds nominal steps
     : 3: output podInitCmdCount to outFlag, skip balance and return
     : 4: like 2, + verboseOutput (init, podState, full df) to csv
     : 5: same as 4 plus add extra for Dash
    """
    REPORT_INIT_ONLY = 3
    VERBOSE_OUT_FILE = 4
    nomNumInitSteps = 18  # nominal number steps to initialize pod
    dashStatsFlag = 0

    if vFlag == 5:
        dashStatsFile = outFlag + '/' + 'dash_stats.csv'
        dashStatsFlag = 1
        vFlag = 4  # rest of code uses this for verbose reporting

    # This is time (sec) radio on Pod stays awake once comm is initiated
    # Eros only:
    radio_on_time = 30
    # For Dash, this is 3 minutes but app reconnects every time pod BT drops.
    # right now - not tracking this for Dash

    # add more stuff and return as a DataFrame
    df = generate_table(podFrame, radio_on_time)

    # Process df to generate the podState associated with every message
    #   Updates to states occur with pod message (mostly 1d) status
    #     (the state for extended_bolus_active is NOT included (always False))
    #   Includes values for requested bolus and TB
    # Note that .iloc for df and podState are identical
    # Indexing within podState requires .loc
    podState, faultProcessedMsg = getPodState(df)

    # generate a number of useful facts from podState
    # a few values are added / modified later as analysis continues
    logInfoDict = getLogInfoFromState(podState)

    # checkAction returns actionFrame with indices and times for every action
    #     completed actions and incomplete requests are separate columns
    #     see also function getActionDict
    #   actionFrame  dataframe of processed analysis from podState (by action)
    #   initIdx      indices in podState to extract pod initilization
    actionFrame, initIdx, frameBalance = checkAction(podState)

    numInitSteps = len(initIdx)
    if numInitSteps > 0:
        podInitFrame = podState.loc[initIdx]
        [podInitCmdCount, podInitState] = getPodInitCmdCount(podInitFrame)
    else:
        # this means no podInitFrame in report
        podInitState = -1
        podInitCmdCount = {}

    if vFlag == REPORT_INIT_ONLY:
        if podInitState >= 0:
            print('  output info from podInitCmdCount to ', outFlag)
            writePodInitCmdCountToOutputFile(outFlag, fileDict['personFile'],
                                             podInitCmdCount)
            # typically used for survey including older reports,
            #   use > 22 instead of nomNumSteps
            if numInitSteps > 0 and numInitSteps > 22:
                printInitFrame(podInitFrame)
        return

    # continue if vFlag is not 3 (aka REPORT_INIT_ONLY)
    if podInitState >= 0:
        printPodInfo(podInitCmdCount, nomNumInitSteps)
    else:
        printPodDict(podDict)

    if podInitState >= 0:
        if vFlag == VERBOSE_OUT_FILE or \
           vFlag == 2 and numInitSteps > nomNumInitSteps:
            printInitFrame(podInitFrame)

    if vFlag == VERBOSE_OUT_FILE:
        thisOutFile = outFlag + '/' + 'podState_' + fileDict['person'] \
                      + '_' + fileDict['date'] + '_' + str(chunkNum) + \
                      '.csv'
        commentString = str(chunkNum)
        writeDescriptivePodStateToOutputFile(thisOutFile, commentString,
                                             podState)

    # special handling if an 0x02 messages aka fault was received
    checkInsulin = 0
    if len(faultProcessedMsg):
        # print(faultProcessedMsg)
        if 'logged_fault' in faultProcessedMsg:
            hasFault = True
            thisFault = faultProcessedMsg['logged_fault']
            checkInsulin = faultProcessedMsg['insulinDelivered']
        else:
            thisFault = faultProcessedMsg['fault_type']
        # update logInfoDict with insulinDelivered and sourceString if needed
        if checkInsulin >= logInfoDict['insulinDelivered']:
            logInfoDict['insulinDelivered'] = checkInsulin
            logInfoDict['sourceString'] = 'from 0x02 msg'
    else:
        hasFault = False
        thisFault = 'Nominal'
        faultProcessedMsg = {}

    # process the action frame
    # returns a dictionary plus total completed message count)
    if len(actionFrame) == 0:
        print('\nPod did not initialize')
        return

    actionSummary, totalCompletedMessages = processActionFrame(actionFrame,
                                                               podState)
    percentCompleted = 100*totalCompletedMessages/logInfoDict['numMsgs']

    # add this to logInfoDict
    logInfoDict['totalCompletedMessages'] = totalCompletedMessages
    logInfoDict['percentCompleted'] = percentCompleted

    if True:
        printLogInfoSummary(logInfoDict)
        if hasFault:
            faultString = f'    An 0x0202 message of {thisFault} reported'
            if thisFault == '0x1c':
                print(f'     {faultString}:   80 hour pod time limit')
                hasFault = 0
            elif thisFault == '0x18':
                print(f'     {faultString}:   Pod out of insulin')
                hasFault = 0
            elif thisFault == '0x00':
                print(f'     {faultString}:   Read Pod Status')
                hasFault = 0
            elif thisFault == '0x34':
                print(f'     {faultString}:   Fault wipes out pod registers')
            else:
                print(f'     {faultString}:   Fault details found below')

        numACK = len(podState[podState.msgType == 'ACK'])
        if numACK > 0:
            print(f'    ***  Detected {numACK} ACK(s) during life of pod')

        printActionSummary(actionSummary)

        # turn these back on - still useful, action list no longer complete
        if 1:
            # report for uncategorized commands
            if len(frameBalance) > 0:
                printUncategorizedMessages(frameBalance, podState)

    if hasFault:
        print('\nFault Details')
        printDict(faultProcessedMsg)

    if dashStatsFlag == 1:
        writeDashStats(dashStatsFile, podState, fileDict, logInfoDict,
                       numInitSteps, faultProcessedMsg)

    return
