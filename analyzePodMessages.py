import pandas as pd
from messageLogs_functions import *
from utils import *
from utils_report import *
from podStateAnalysis import *
from podInitAnalysis import *
from messagePatternParsing import *
from checkAction import *

"""
analyzePodMessages
    This code analyzes a single Pod with available message dataframe
"""

def analyzePodMessages(thisFile, podFrame, podDict, fault_report, outFile, vFlag, chunkNum):
    # preprocess podFrame to be from a single pod
    # new use of vFlag.
    #  : if 0: output analysis to terminal window
    #  : if 1: output pod session analysis to outFile (older and not working)
    #  : if 2: like 0, but report init steps to terminal if exceeds nominal expected
    #  : if 3: output init summary to outFile, init steps if too many, skip rest of pod analysis
    #  : if 4: report init steps to terminal and outFile_init.csv, report podState to outFile_podState.csv
    REPORT_INIT_ONLY = 3
    VERBOSE_OUT_FILE = 4
    nomNumInitSteps = 18  # nominal number steps to initialize pod

    # This is time (sec) radio on Pod stays awake once comm is initiated
    radio_on_time   = 30

    # add more stuff and return as a DataFrame
    df = generate_table(podFrame, radio_on_time)

    # set up a few reportable values here from df, time is in UTC
    first_msg = df.iloc[0]['time']
    last_msg = df.iloc[-1]['time']
    send_receive_messages = df.groupby(['type']).size()
    number_of_messages = len(df)
    lastDate = last_msg.date()

    thisPerson, thisDate = getPersonFromFilename(thisFile, last_msg)

    # Process df to generate the podState associated with every message
    #   Updates to states occur with pod message (mostly 1d) status
    #     (the state for extended_bolus_active is NOT included (always False))
    #   Includes values for requested bolus and TB
    # Note that .iloc for df and podState are identical
    podState, ackMessageList, faultProcessedMsg, podInfo = getPodState(df)

    # checkAction returns actionFrame with indices and times for every action
    #     completed actions and incomplete requests are separate columns
    #     see also function getActionDict
    #   actionFrame  dataframe of processed analysis from podState (by action)
    #   initIdx      indices in podState to extract pod initilization
    actionFrame, initIdx = checkAction(podState)

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
        if numInitSteps > 0 and podInfo['numInitSteps']!=nomNumInitSteps:
            printInitFrame(podInitFrame)
        # output summary to outfile if provided
        #if hasPodInit and outFile:
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
        if hasPodInit and podInfo['numInitSteps']!=nomNumInitSteps:
            printInitFrame(podInitFrame)

    if vFlag == VERBOSE_OUT_FILE and numInitSteps > 0:
        # print to terminal
        printInitFrame(podInitFrame)
        # write to file
        thisOutFile = outFile +'initSteps_' + thisPerson + '_' + thisDate + '_' + str(chunkNum) + '.csv'
        commentString = str(chunkNum)
        writePodInitStateToOutputFile(thisOutFile, commentString, podInitFrame)

    if vFlag == VERBOSE_OUT_FILE:
        thisOutFile = outFile +'podState_' + thisPerson + '_' + thisDate + '_' + str(chunkNum) + '.csv'
        commentString = str(chunkNum)
        writePodStateToOutputFile(thisOutFile, commentString, podState)

    # From the podState, extract some values to use in reports
    msgLogHrs = podState.iloc[-1]['timeCumSec']/3600
    radioOnHrs = podState.iloc[-1]['radioOnCumSec']/3600
    numberOfAssignID = len(podState[podState.msgType=='0x07'])
    numberOfSetUpPod = len(podState[podState.msgType=='0x03'])
    numberOfNonceResync = len(podState[podState.msgType=='0x06'])
    insulinDelivered = podState.iloc[-1]['insulinDelivered']
    sourceString = 'from last 0x1d'

    # special handling if an 0x02 messages aka fault was received
    checkInsulin = 0
    if len(faultProcessedMsg):
        # print(faultProcessedMsg)
        hasFault = True
        if 'logged_fault' in faultProcessedMsg:
            thisFault = faultProcessedMsg['logged_fault']
            checkInsulin = faultProcessedMsg['insulinDelivered']
        else:
            thisFault = faultProcessedMsg['fault_type']
        rawFault = faultProcessedMsg['msg_body']
        if checkInsulin >= insulinDelivered:
            insulinDelivered = checkInsulin
            sourceString = 'from 0x02 msg'
    elif fault_report==[]:
        hasFault = False
        rawFault = 'n/a'
        thisFault = 'Nominal'
    else:
        hasFault = True
        rawFault = 'n/a'
        thisFault = 'PodInfoFaultEvent'

    # process the action frame (returns a dictionary plus total completed message count)
    if len(actionFrame) == 0:
        print('\nPod did not initialize')
        actionSummary = 0
        return df, podState, actionFrame, actionSummary
    actionSummary, totalCompletedMessages = processActionFrame(actionFrame, podState)
    percentCompleted = 100*totalCompletedMessages/number_of_messages

    # print(f') doesn't work with {dict items}
    # fix this eventually, for not - rename them
    lot = podID['lot']
    tid = podID['tid']
    piv = podID['piVersion']

    if outFile == 2:
        # print a few things then returns
        print(f'{thisPerson},{thisAntenna},{thisFault},{first_msg},{last_msg},{msgLogHrs},{lot},{tid},{piv}')
        actionSummary = []
        return df, podState, actionFrame, actionSummary

    if True:
        #
        # print out summary information to stdout window
        # need this True to get the actionSummary used to fill csv file
        print('\n            First message for pod :', first_msg)
        print('            Last  message for pod :', last_msg)
        print('  Total elapsed time in log (hrs) : {:6.1f}'.format(msgLogHrs))
        if podInfo.get('pod_active_minutes'):
            print(' Total elapsed time for pod (hrs) : {:6.1f}'.format(podInfo['pod_active_minutes']/60))
        print('                Radio on estimate : {:6.1f}, {:5.1f}%'.format(radioOnHrs, 100*radioOnHrs/msgLogHrs))
        print('   Number of messages (sent/recv) :{:5d} ({:4d} / {:4d})'.format(number_of_messages,
            send_receive_messages[1], send_receive_messages[0]))
        print('    Messages in completed actions :{:5d} : {:.1f}%'.format( \
            totalCompletedMessages, percentCompleted))
        print('          Number of nonce resyncs :{:5d}'.format(numberOfNonceResync))
        print('            Insulin delivered (u) : {:7.2f} ({:s})'.format(insulinDelivered, sourceString))
        if hasFault:
            thisFinish = thisFault
            thisFinish2 = 'Fault'
            if thisFault == '0x1C':
                print('    An 0x0202 message of {:s} reported - 80 hour time limit'.format(thisFault))
                thisFinish2 = 'Success'
            elif thisFault == '0x18':
                print('    An 0x0202 message of {:s} reported - out of insulin'.format(thisFault))
                thisFinish2 = 'Success'
            elif thisFault == '0x34':
                print('    An 0x0202 message of {:s} reported - this wipes out registers'.format(thisFault))
            else:
                print('    An 0x0202 message of {:s} reported - details later'.format(thisFault))
                #hasFault = 0

        if ackMessageList:
            print('    ***  Detected {:d} ACK(s) during life of the pod'.format(len(ackMessageList)))
            print('    ***  indices :', ackMessageList)


        printActionSummary(actionSummary, vFlag)

        # add this printout to look for message types other than 14 for 06 responses
        #  added message logging to record this around Dec 2, 2019
        # print('\n Search for non-type 14 in 06 messages\n',podState[podState.msgType=='06'])

    if hasFault:
        print('\nFault Details')
        printDict(faultProcessedMsg)

    # if an output filename is provided - write statistics to it (csv format)
    # This prints things we no longer calculate - clean up later
    doNotUse = 0
    if doNotUse:
        # check if file exists
        isItThere = os.path.isfile(outFile)

        # now open the file
        stream_out = open(outFile,mode='at')

        # write the column headers if this is a new file
        if not isItThere:
            # set up a table format order
            headerString = 'Who, finish State, Finish2, lastMsg Date, podOn (hrs), radioOn (hrs), radioOn (%), ' + \
               '#Messages, #Completed, % Completed, #Send, #Recv, ' + \
               '#Nonce Resync, #TB, #Bolus, ' \
               '#Basal, #Status Check, ' + \
               '#Schedule Before TempBasal, #TB Spaced <30s, ' + \
               '#Repeat TB Value, #Repeat TB <30s, ' + \
               ' #RepTB 30s to 19min, #incomplete TB, ' + \
               'insulin Delivered, # Initialize Cmds, # AssignID (0x07), ' + \
               '# SetUpPod (0x03), Pod Lot, PI Version, PM Version, ' + \
               'raw fault, filename'
            stream_out.write(headerString)
            stream_out.write('\n')

        # Extract items from actionSummary
        if actionSummary.get('CnxSetTmpBasal'):
            subDict = actionSummary.get('CnxSetTmpBasal')
            numberOfTB = subDict['countCompleted']
            numberScheduleBeforeTempBasal = subDict['numSchBasalbeforeTB']
            numberTBSepLessThan30sec = subDict['numShortTB']
            numRepeatedTB = subDict['numRepeatedTB']
            numRepeatedShortTB = subDict['numRepeatedShortTB']
            numrepeated19MinTB = subDict['numrepeated19MinTB']
        else:
            numberOfTB = 0
            numberScheduleBeforeTempBasal = 0
            numberTBSepLessThan30sec = 0
            numRepeatedTB = 0

        if actionSummary.get('Bolus'):
            subDict = actionSummary.get('Bolus')
            numberOfBolus = subDict['countCompleted']
        else:
            numberOfBolus = 0

        if actionSummary.get('Basal'):
            subDict = actionSummary.get('Basal')
            numberOfBasal = subDict['countCompleted']
        else:
            numberOfBasal = 0

        if actionSummary.get('StatusCheck'):
            subDict = actionSummary.get('StatusCheck')
            numberOfStatusRequests = subDict['countCompleted']
        else:
            numberOfStatusRequests = 0

        if actionSummary.get('CancelTB'):
            subDict = actionSummary.get('CancelTB')
            numIncomplCancelTB = subDict['countIncomplete']
        else:
            numIncomplCancelTB = 0

        # write out the information for csv (don't want extra spaces for this )
        #stream_out.write(f'{thisPerson},{thisFinish},{thisFinish2},{lastDate},')
        stream_out.write('{:.1f},'.format(msgLogHrs))
        stream_out.write('{:.2f},'.format(radioOnHrs))
        stream_out.write('{:.2f},'.format(100*radioOnHrs/msgLogHrs))
        stream_out.write('{:d},'.format(number_of_messages))
        stream_out.write(f'{totalCompletedMessages},')
        stream_out.write('{:.2f},'.format(percentCompleted))
        stream_out.write(f'{send_receive_messages[1]},{send_receive_messages[0]},')
        stream_out.write(f'{numberOfNonceResync},{numberOfTB},{numberOfBolus},{numberOfBasal},')
        stream_out.write(f'{numberOfStatusRequests},{numberScheduleBeforeTempBasal},')
        stream_out.write(f'{numberTBSepLessThan30sec},{numRepeatedTB},{numRepeatedShortTB},')
        stream_out.write(f'{numrepeated19MinTB},{numIncomplCancelTB},')
        stream_out.write('{:.2f},'.format(insulinDelivered))
        stream_out.write('{:d}, {:d}, {:d},'.format(numInitSteps, numberOfAssignID, numberOfSetUpPod))
        stream_out.write('{:s}, {:s},'.format(lot, piv))
        stream_out.write(f'{rawFault},{thisFile}')
        stream_out.write('\n')
        stream_out.close()

    return df, podState, actionFrame, actionSummary
