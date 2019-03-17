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
    commands = read_file(filename)

    # add more stuff and return as a DataFrame
    df = generate_table(commands, radio_on_time)

    # set up a few reportable values here from df, time is in UTC
    first_command = df.iloc[0]['time']
    last_command = df.iloc[-1]['time']
    send_receive_commands = df.groupby(['type']).size()
    number_of_messages = len(df)
    thisPerson, thisFinish, thisAntenna = parse_info_from_filename(thisFile)
    lastDate = last_command.date()

    # Process the dataframes and update the pod state
    podState, emptyMessageList, faultProcessedMsg = getPodState(df)
    msgLogHrs = podState.iloc[-1]['timeCumSec']/3600
    radioOnHrs = podState.iloc[-1]['radioOnCumSec']/3600

    # Use checkAction to return all the information about this pod
    #  Note - may rearrange / drop some of these returns later
    #   actionFrame  dataframe of processed analysis from podState (by action)
    #   initIdx      indices in podState to extract pod init
    #   nonceIdx     indices in podState to extract every Nonce
    #   faultIdx     indices in podState to extract Fault
    actionFrame, initIdx, nonceIdx, faultIdx = checkAction(podState)

    numberOfAssignID = len(podState[podState.message_type=='0x7'])
    numberOfSetUpPod = len(podState[podState.message_type=='0x3'])
    insulinDelivered = podState.iloc[-1]['insulinDelivered']
    sourceString = 'from last 0x1d'

    if len(faultProcessedMsg):
        thisFault = faultProcessedMsg['logged_fault']
        checkInsulin = faultProcessedMsg['insulinDelivered']
        if checkInsulin > insulinDelivered:
            insulinDelivered = checkInsulin
            sourceString = 'from 0x02 msg'
    else:
        thisFault = 'n/a'

    if True:
        # print out summary information to command window
        print('    First command in Log          :', first_command)
        print('    Last  command in Log          :', last_command)
        print('  Make sure these make sense (otherwise check maxChars in read_file)\n')
        print('__________________________________________\n')
        print(f' Summary for {thisFile} with {thisFinish} ending')
        print('  Total elapsed time in log (hrs) : {:6.1f}'.format(msgLogHrs))
        print('        Radio on estimate         : {:6.1f}, {:5.1f}%'.format(radioOnHrs, 100*radioOnHrs/msgLogHrs))
        print('        Number of messages        : {:6d}'.format(len(df)))
        print('        Number of nonce resyncs   : {:6d}'.format(len(nonceIdx)))
        print('        Insulin delivered (u)     : {:6.2f} ({:s})'.format(insulinDelivered, sourceString))
        if len(faultProcessedMsg):
            thisFinish = thisFault
            if thisFault == '0x1C':
                print('    An 0x0202 message of {:s} reported - 80 hour time limit'.format(thisFault))
            elif thisFault == '0x18':
                print('    An 0x0202 message of {:s} reported - out of insulin'.format(thisFault))
            else:
                print('    An 0x0202 message was reported - details later')
        print('\n  Pod was initialized with {:d} messages, {:d} AssignID, {:d} SetUpPod required'.format(len(initIdx), \
           numberOfSetUpPod, numberOfAssignID))
        if emptyMessageList:
            print('    ***  Detected {:d} empty message(s) during life of the pod'.format(len(emptyMessageList)))
            print('    ***  indices:', emptyMessageList)

        actionSummary, totalCompletedMessages = printActionFrame(actionFrame)
        percentCompleted = 100*totalCompletedMessages/len(df)
        print('\n  Messages part of a completed action  :          {:d} : {:.1f}%'.format( \
            totalCompletedMessages, percentCompleted))

    if len(faultProcessedMsg):
        print('\nFault Details')
        printDict(faultProcessedMsg)

    # if an output filename is provided - write out summary to it (csv format)
    # note that printReport must also be true
    if outFile:
        # set up a table format order
        headerString = 'Who, finish State, antenna, lastMsg Date, podOn (hrs), radioOn (hrs), radioOn (%), ' + \
           '#Messages, #Completed, % Completed, #Send, #Recv, ' + \
           '#Nonce Resync, #TB, #Bolus, ' \
           '#Basal, #Status Check, ' + \
           '#Schedule Before TempBasal, #Schedule BasalLess Than30sec, ' + \
           ' insulin Delivered, #faultInFile, filename'

        # if file doesn't exist, write the header, otherwise append the data
        # check if file exists
        isItThere = os.path.isfile(outFile)

        # now open the file
        stream_out = open(outFile,mode='at')

        # write the column headers if this is a new file
        if not isItThere:
            stream_out.write(headerString)
            stream_out.write('\n')

        # Extract items from actionSummary - not all are always present
        idx = 0
        if actionSummary[idx][0] == 'TB':
           numberOfTB = actionSummary[idx][1][0]
           numberScheduleBeforeTempBasal = actionSummary[idx][1][1]
           numberScheduleBasalLessThan30sec = actionSummary[idx][1][2]
           idx += 1
        if actionSummary[idx][0] == 'Bolus':
            numberOfBolus = actionSummary[idx][1]
            idx += 1
        else:
            numberOfBolus = 0
        if actionSummary[idx][0] == 'Basal':
            numberOfBasal = actionSummary[idx][1]
            idx += 1
        else:
            numberOfBasal = 0
        if actionSummary[idx][0] == 'StatusCheck':
            numberOfStatusRequests = actionSummary[idx][1]
            idx += 1
        else:
            numberOfStatusRequests = 0

        # write out the information for csv (don't want extra spaces for this )
        stream_out.write(f'{thisPerson},{thisFinish},{thisAntenna},{lastDate},{msgLogHrs},')
        stream_out.write(f'{radioOnHrs},{100*radioOnHrs/msgLogHrs},{number_of_messages},')
        stream_out.write(f'{totalCompletedMessages},{percentCompleted},')
        stream_out.write(f'{send_receive_commands[1]},{send_receive_commands[0]},')
        stream_out.write(f'{len(nonceIdx)},{numberOfStatusRequests},{numberOfBasal},{numberOfTB},')
        stream_out.write(f'{numberOfBolus},{numberScheduleBeforeTempBasal},{numberScheduleBasalLessThan30sec},')
        stream_out.write(f'{insulinDelivered},')
        stream_out.write(f'{thisFault},{thisFile}')
        stream_out.write('\n')
        stream_out.close()

    return df, podState, actionFrame, actionSummary
