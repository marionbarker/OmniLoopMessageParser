import pandas as pd
from messageLogs_functions import *
from byteUtils import *
from podStateAnalysis import *
from messagePatternParsing import *
from checkAction import *

def analyzeMessageLogsRev3(thisPath, thisFile, outFile):
    # Rev3 uses the new checkAction code
    #  this replaces code used by New (rev2)
    #       deprecated: getPodSuccessfulActions
    #       deprecated: basal_analysis code (assumed perfect message order)

    # This is time (sec) radio on Pod stays awake once comm is initiated
    radio_on_time   = 30

    filename = thisPath + '/' + thisFile

    # read the MessageLogs from the file
    commands, podDict = read_file(filename)

    # add more stuff and return as a DataFrame
    df = generate_table(commands, radio_on_time)

    # set up a few reportable values here from df, time is in UTC
    first_command = df.iloc[0]['time']
    last_command = df.iloc[-1]['time']
    send_receive_commands = df.groupby(['type']).size()
    number_of_messages = len(df)
    thisPerson, thisFinish, thisAntenna = parse_info_from_filename(thisFile)
    thisFinish2 = 'Success' # default is 'Success'
    if thisFinish == 'WIP':
        thisFinish2 = 'WIP'  # pod is still running

    lastDate = last_command.date()

    # Process df to generate the podState associated with every message
    #   Updates to states occur with pod message (mostly 1d) status
    #     (the state for extended_bolus_active is NOT included (always False))
    #   Includes values for requested bolus and TB
    # Note that .iloc for df and podState are identical
    podState, emptyMessageList, faultProcessedMsg = getPodState(df)

    # From the podState, extract some values to use in reports
    msgLogHrs = podState.iloc[-1]['timeCumSec']/3600
    radioOnHrs = podState.iloc[-1]['radioOnCumSec']/3600
    numberOfAssignID = len(podState[podState.message_type=='0x7'])
    numberOfSetUpPod = len(podState[podState.message_type=='0x3'])
    numberOfNonceResync = len(podState[podState.message_type=='06'])
    insulinDelivered = podState.iloc[-1]['insulinDelivered']
    sourceString = 'from last 0x1d'

    # special handling if an 0x02 messages aka fault was received
    if len(faultProcessedMsg):
        hasFault = True
        thisFault = faultProcessedMsg['logged_fault']
        checkInsulin = faultProcessedMsg['insulinDelivered']
        rawFault = faultProcessedMsg['raw_value']
        if checkInsulin >= insulinDelivered:
            insulinDelivered = checkInsulin
            sourceString = 'from 0x02 msg'
    else:
        hasFault = False
        rawFault = 'n/a'
        thisFault = thisFinish

    # checkAction returns actionFrame with indices and times for every action
    #     completed actions and incomplete requests are separate columns
    #     see also function getActionDict
    #   actionFrame  dataframe of processed analysis from podState (by action)
    #   initIdx      indices in podState to extract pod initilization
    actionFrame, initIdx = checkAction(podState)

    if outFile == 2:
        # print a few things then returns
        lot = podDict['lot']
        tid = podDict['tid']
        piv = podDict['piVersion']
        print(f'{thisPerson},{thisAntenna},{thisFault},{first_command},{last_command},{msgLogHrs},{lot},{tid},{piv}')
        actionSummary = []
        return df, podState, actionFrame, actionSummary

    if True:
        # print out summary information to command window
        # need this True to get the actionSummary used to fill csv file
        print('\n    First command in Log          :', first_command)
        print('    Last  command in Log          :', last_command)
        print('    Lot and TID                   :', podDict['lot'], podDict['tid'])
        print('__________________________________________\n')
        print(' Summary for {:s} with {:s} ending'.format(thisFile, thisFinish))
        print('  Pod Lot: {:s}, PI: {:s}, PM: {:s}'.format(podDict['lot'], podDict['piVersion'], podDict['pmVersion']))
        print('  Total elapsed time in log (hrs) : {:6.1f}'.format(msgLogHrs))
        print('        Radio on estimate         : {:6.1f}, {:5.1f}%'.format(radioOnHrs, 100*radioOnHrs/msgLogHrs))
        print('        Number of messages        : {:6d}'.format(number_of_messages))
        print('        Number of nonce resyncs   : {:6d}'.format(numberOfNonceResync))
        print('        Insulin delivered (u)     : {:6.2f} ({:s})'.format(insulinDelivered, sourceString))
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
        print('\n  Pod was initialized with {:d} messages, {:d} AssignID, {:d} SetUpPod required'.format(len(initIdx), \
           numberOfAssignID, numberOfSetUpPod))
        if emptyMessageList:
            print('    ***  Detected {:d} empty message(s) during life of the pod'.format(len(emptyMessageList)))
            print('    ***  indices:', emptyMessageList)

        # process the action frame (returns a dictionary plus total completed message count)
        actionSummary, totalCompletedMessages = processActionFrame(actionFrame, podState)
        printActionSummary(actionSummary)

        percentCompleted = 100*totalCompletedMessages/number_of_messages
        print('  #Messages in completed actions : {:5d} : {:.1f}%'.format( \
            totalCompletedMessages, percentCompleted))

    if hasFault:
        print('\nFault Details')
        printDict(faultProcessedMsg)

    # if an output filename is provided - write statistics to it (csv format)
    if outFile:
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
        if actionSummary.get('TB'):
            subDict = actionSummary.get('TB')
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
        stream_out.write(f'{thisPerson},{thisFinish},{thisFinish2},{lastDate},')
        stream_out.write('{:.1f},'.format(msgLogHrs))
        stream_out.write('{:.2f},'.format(radioOnHrs))
        stream_out.write('{:.2f},'.format(100*radioOnHrs/msgLogHrs))
        stream_out.write('{:d},'.format(number_of_messages))
        stream_out.write(f'{totalCompletedMessages},')
        stream_out.write('{:.2f},'.format(percentCompleted))
        stream_out.write(f'{send_receive_commands[1]},{send_receive_commands[0]},')
        stream_out.write(f'{numberOfNonceResync},{numberOfTB},{numberOfBolus},{numberOfBasal},')
        stream_out.write(f'{numberOfStatusRequests},{numberScheduleBeforeTempBasal},')
        stream_out.write(f'{numberTBSepLessThan30sec},{numRepeatedTB},{numRepeatedShortTB},')
        stream_out.write(f'{numrepeated19MinTB},{numIncomplCancelTB},')
        stream_out.write('{:.2f},'.format(insulinDelivered))
        stream_out.write('{:d}, {:d}, {:d},'.format(len(initIdx), numberOfAssignID, numberOfSetUpPod))
        stream_out.write('{:s}, {:s}, {:s},'.format(podDict['lot'], podDict['piVersion'], podDict['pmVersion']))
        stream_out.write(f'{rawFault},{thisFile}')
        stream_out.write('\n')
        stream_out.close()

    return df, podState, actionFrame, actionSummary
