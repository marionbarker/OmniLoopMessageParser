from parsers.messageLogs_functions import generate_table, getPersonFromFilename
from util.misc import printDict
from util.report import writePodox0115ToOutputFile, printInitFrame
from util.report import printPodInfo, printPodDict, printLogInfoSummary
from util.report import writePodInitStateToOutputFile, printActionSummary
from util.report import writeDescriptivePodStateToOutputFile
from util.report import reportUncategorizedMessages
from util.pod import getLogInfoFromState, returnPodID
from analysis.podStateAnalysis import getPodState
from analysis.podInitAnalysis import getPod0x0115Response, getInitState
from analysis.checkAction import checkAction, processActionFrame

"""
analyzePodMessages
    This code analyzes a single Pod with available message dataframe
"""


def analyzePodMessages(thisFile, podFrame, podDict, faultInfoDict, outFile,
                       vFlag, chunkNum):
    """
    preprocess podFrame to be from a single pod
    new use of vFlag.
     : if 0: output analysis to terminal window
     : if 1: output pod session analysis to outFile (older and not working)
     : if 2: like 0, but report init steps to terminal if exceeds nominal
       expected
     : if 3: output init summary to outFile, init steps if too many, skip rest
       of pod analysis
     : if 4: report init steps to terminal and outFile_init.csv, report
       podState to outFile_podState.csv
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
    podState, ackMessageList, faultProcessedMsg, podInfo = getPodState(df)

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
        thisFrame = df.iloc[initIdx]
        pod0x0115Response = getPod0x0115Response(thisFrame)
        if vFlag == REPORT_INIT_ONLY:
            print('  output info from 0x0115 response to ', outFile)
            writePodox0115ToOutputFile(outFile, thisFile, pod0x0115Response)

    # if pod initialization exists, put that into podID, otherwise use podDict
    podID, hasPodInit = returnPodID(podDict, podInfo)

    # if pod initialization exists, get just the frames associated with it
    if numInitSteps > 0:
        podInfo['numInitSteps'] = numInitSteps
        thisFrame = df.iloc[initIdx]
        podInitFrame = getInitState(thisFrame)

    # Special handling for vFlag = 3 (aka REPORT_INIT_ONLY)
    if vFlag == REPORT_INIT_ONLY:
        # If number of initializations steps not nominal, print initFrame
        if numInitSteps > 0 and podInfo['numInitSteps'] != nomNumInitSteps:
            printInitFrame(podInitFrame)
        # output summary to outfile if provided
        # if hasPodInit and outFile:
        #    writePodInfoToOutputFile(outFile, lastDate, thisFile, podInfo)
        # return now, so set returned args not yet defined to []
        actionSummary = []
        return df, podState, actionFrame, actionSummary

    # continue if vFlag is not 3 (aka REPORT_INIT_ONLY)
    if hasPodInit:
        printPodInfo(podInfo, nomNumInitSteps)
    else:
        printPodDict(podDict)

    if vFlag == 2:
        if hasPodInit and podInfo['numInitSteps'] != nomNumInitSteps:
            printInitFrame(podInitFrame)

    if vFlag == VERBOSE_OUT_FILE and numInitSteps > 0:
        # print to terminal if not nominal
        if numInitSteps != nomNumInitSteps:
            printInitFrame(podInitFrame)
        # write to file
        thisOutFile = outFile + 'initSteps_' + thisPerson + '_' + thisDate \
            + '_' + str(chunkNum) + '.csv'
        commentString = str(chunkNum)
        writePodInitStateToOutputFile(thisOutFile, commentString, podInitFrame)

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
        actionSummary = 0
        return df, podState, actionFrame, actionSummary
    actionSummary, totalCompletedMessages = processActionFrame(actionFrame,
                                                               podState)
    percentCompleted = 100*totalCompletedMessages/logInfoDict['numMsgs']

    # add this to logInfoDict
    logInfoDict['totalCompletedMessages'] = totalCompletedMessages
    logInfoDict['percentCompleted'] = percentCompleted

    # print(f') doesn't work with {dict items}
    # fix this eventually, for not - rename them

    if outFile == 2:
        # print a few things then returns
        # The string literal "thisAntenna" is replacing an undefined variable
        print('{:s}, {:s}, {:s}, {:s}, {:s}, {:.2f}, {:s}, {:s}, {:s} '.format(
            thisPerson, "thisAntenna", thisFault, logInfoDict['first_msg'],
            logInfoDict['last_msg'], logInfoDict['msgLogHrs'],
            podID['lot'], podID['tid'], podID['piVersion']))
        actionSummary = []
        return df, podState, actionFrame, actionSummary

    if True:
        printLogInfoSummary(logInfoDict)
        if hasFault:
            if thisFault == '0x1C':
                print('    An 0x0202 message of ' +
                      '{:s} reported 80 hour time limit'.format(thisFault))
                hasFault = 0
            elif thisFault == '0x18':
                print('    An 0x0202 message of ' +
                      '{:s} reported  out of insulin'.format(thisFault))
                hasFault = 0
            elif thisFault == '0x34':
                print('    An 0x0202 message of ' +
                      '{:s} reported wipes out registers'.format(thisFault))
            else:
                print('    An 0x0202 message of ' +
                      '{:s} reported details later'.format(thisFault))

        if ackMessageList:
            print('    ***  Detected {:d} ACK(s) during life of pod'.format(
                  len(ackMessageList)))
            print('    ***  indices :', ackMessageList)

        printActionSummary(actionSummary, vFlag)

        # report for uncategorized commands
        if len(frameBalance) > 0:
            reportUncategorizedMessages(frameBalance, podState)

        # add this printout to look for message types other than 14 for 06 responses
        #  added message logging to record this around Dec 2, 2019
        # print('\n Search for non-type 14 in 06 messages\n',podState[podState.msgType=='06'])

    if hasFault:
        print('\nFault Details')
        printDict(faultProcessedMsg)

    return df, podState, actionFrame, actionSummary
