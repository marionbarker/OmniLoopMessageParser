from parsers.messageLogs_functions import generate_table, getPersonFromFilename
from util.misc import printDict
from util.report import writePodInitCmdCountToOutputFile, printInitFrame
from util.report import printPodInfo, printPodDict, printLogInfoSummary
from util.report import printActionSummary
from util.report import writeDescriptivePodStateToOutputFile
from util.report import reportUncategorizedMessages
from util.pod import getLogInfoFromState, returnPodID
from analysis.podStateAnalysis import getPodState
from analysis.podInitAnalysis import getPodInitCmdCount
from analysis.checkAction import checkAction, processActionFrame

"""
analyzePodMessages
    This code analyzes a single Pod with available message dataframe
"""
# loopReadDict has keys:
#   fileType, logDF, podMgrDict, faultInfoDict, loopVersionDict


def analyzePodMessages(thisFile, podFrame, podDict, faultInfoDict, outFile,
                       vFlag, chunkNum):
    """
    preprocess podFrame to be from a single pod
    new use of vFlag.
     : if 0: output analysis to terminal window
     : if 1: deprecated
     : if 2: like 0, plus printPodInitFrame if exceeds nominal steps
     : if 3: output podInitCmdCount to outFile, skip balance and return
     : if 4: like 2, plus verboseOutput init.csv, pod.csv, logDfCmb.csv
    """
    REPORT_INIT_ONLY = 3
    VERBOSE_OUT_FILE = 4
    nomNumInitSteps = 18  # nominal number steps to initialize pod

    # This is time (sec) radio on Pod stays awake once comm is initiated
    radio_on_time = 30

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

    # get some strings used for later reporting
    thisPerson, thisDate = getPersonFromFilename(thisFile,
                                                 logInfoDict['last_msg'])

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
        if vFlag == REPORT_INIT_ONLY:
            print('  output info from podInitCmdCount to ', outFile)
            writePodInitCmdCountToOutputFile(outFile, thisFile,
                                             podInitCmdCount)
    else:
        # this means no podInitFrame in report
        podInitState = -1
        podInitCmdCount = {}

    # returns whatever we have from report file, various sources
    podID = returnPodID(podDict, podInitCmdCount)

    # Special handling for vFlag = 3 (aka REPORT_INIT_ONLY)
    if vFlag == REPORT_INIT_ONLY:
        # If number of initializations steps not nominal, print initFrame
        if numInitSteps > 0 and numInitSteps != nomNumInitSteps:
            printInitFrame(podInitFrame)
        # output summary to outfile if provided
        # if hasPodInit and outFile:
        #    writePodInfoToOutputFile(outFile, lastDate, thisFile, podInfo)
        # return now
        return

    # continue if vFlag is not 3 (aka REPORT_INIT_ONLY)
    if podInitState >= 0:
        printPodInfo(podInitCmdCount, nomNumInitSteps)
    else:
        printPodDict(podDict)

    if vFlag == 2:
        if podInitState >= 0 and \
           podInitCmdCount['numInitSteps'] != nomNumInitSteps:
            printInitFrame(podInitFrame)

    if vFlag == VERBOSE_OUT_FILE and numInitSteps > 0:
        # print to terminal if not nominal
        if numInitSteps != nomNumInitSteps:
            printInitFrame(podInitFrame)
        printInitFrame(podInitFrame)
        # write to file
        # thisOutFile = outFile + 'initSteps_' + thisPerson + '_' + thisDate \
        #     + '_' + str(chunkNum) + '.csv'
        # commentString = str(chunkNum)
        # writeDescriptivePodStateToOutputFile(thisOutFile, commentString,
        #                                      podState[initIdx])

    if vFlag == VERBOSE_OUT_FILE:
        thisOutFile = outFile + 'podState_' + thisPerson + '_' + thisDate + \
            '_' + str(chunkNum) + '.csv'
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
    elif faultInfoDict == {}:
        hasFault = False
        thisFault = 'Nominal'
    else:
        hasFault = True
        thisFault = 'PodInfoFaultEvent'

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

    if outFile == 2:
        # print a few things then returns
        # The string literal "thisAntenna" is replacing an undefined variable
        print(f'{thisPerson}, "thisAntenna", {thisFault}, ' +
              f'{logInfoDict["first_msg"]}, {logInfoDict["last_msg"]}, ' +
              f'{logInfoDict["msgLogHrs"]}, {podID["lot"]}, {podID["tid"]}, ' +
              f' {podID["piVersion"]} ')
        return

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
            elif thisFault == '0x34':
                print(f'     {faultString}:   Fault wipes out pod registers')
            else:
                print(f'     {faultString}:   Fault details found below')

        numACK = len(podState[podState.msgType == 'ACK'])
        if numACK > 0:
            print(f'    ***  Detected {numACK} ACK(s) during life of pod')

        printActionSummary(actionSummary, vFlag)

        # report for uncategorized commands
        if len(frameBalance) > 0:
            reportUncategorizedMessages(frameBalance, podState)

    if hasFault:
        print('\nFault Details')
        printDict(faultProcessedMsg)

    return
