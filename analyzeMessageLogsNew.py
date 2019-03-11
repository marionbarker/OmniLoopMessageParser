import pandas as pd
from messageLogs_functions import *
from byteUtils import *
from podStateAnalysis import *
from messagePatternParsing import *

def analyzeMessageLogsNew(thisPath, thisFile, outFile, printReport, verboseFlag):

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

    # see if there is a fault or nonceResync
    faultRow = df[df.command=='02']
    nonceResync = df[df.command=='06']

    # new from Eelke 2/27/2019 and updated 3/2/2019 - use as it
    df_basals, df2 = basal_analysis(df)
    numberScheduleBeforeTempBasal = df_basals["command"].count()
    numberScheduleBasalLessThan30sec = df_basals["command"].loc[(df_basals["normal_basal_running_seconds"] < 30)].count()

    # Process the dataframes and update the pod state
    podState, emptyMessageList = getPodState(df)
    msgLogHrs = podState.iloc[-1]['timeCumSec']/3600
    radioOnHrs = podState.iloc[-1]['radioOnCumTime']/3600

    # now combine requests (send) that match with desired response (recv)
    # note that undesired responses such as 02 or 06 show up in podOtherMessages
    podSuccessfulActions, podOtherMessages = getPodSuccessfulActions(podState)

    # split into the initialization portion and the run portion
    runPodProgressValue = 8
    podInitSuccessfulActions = podSuccessfulActions[podSuccessfulActions.end_pod_progress < runPodProgressValue]
    podRunSuccessfulActions = podSuccessfulActions[podSuccessfulActions.end_pod_progress >= runPodProgressValue]

    podInit = podState[podState.pod_progress < runPodProgressValue]
    podRun  = podState[podState.pod_progress >= runPodProgressValue]

    setUpPodCommands = podInit[podInit.message_type=='0x3']
    numberOfSetUpPodCommands = len(setUpPodCommands)

    if printReport:
        # print out summary information to command window
        print('__________________________________________\n')
        print(f' Summary for {thisFile} with {thisFinish} ending')
        print('  Total elapsed time in log (hrs) : {:6.1f}'.format(msgLogHrs))
        print('        Radio on estimate         : {:6.1f}, {:5.1f}%'.format(radioOnHrs, 100*radioOnHrs/msgLogHrs))
        print('        Number of messages        : {:6d}'.format(len(df)))
        print('        Number of nonce resyncs   : {:6d}'.format(len(nonceResync)))
        print('        Insulin delivered (u)     : {:6.2f}'.format(podRun.iloc[-1]['total_insulin']))
        if len(faultRow):
            print('    An 0x0202 message was reported - details later')
        print('\n  Pod was initialized with {:d} messages, {:d} SetUp (0x03) required'.format(len(podInit), \
           numberOfSetUpPodCommands))
        if emptyMessageList:
            print('    ***  Detected {:d} empty message(s) while initializing the pod'.format(len(emptyMessageList)))
            print('    ***  indices:', emptyMessageList)

        print('\n  Pod run (pod_progress>=8) included {:d} messages'.format(len(podRun)))
        if emptyMessageList:
            print('    ***  Detected {:d} empty message(s) while running the pod'.format(len(emptyMessageList)))
            print('    ***  indices:', emptyMessageList)

        doThePrintSuccess(podRunSuccessfulActions)

        print('\n  Using all messages:')
        print('    {:5d} normal Basals ran before a new TB was sent'.format(numberScheduleBeforeTempBasal))
        print('    {:5d} normal Basals ran for < 30 seconds'.format(numberScheduleBasalLessThan30sec))

    # add other analysis here  like TB timing etc

    if len(faultRow):
        msg = faultRow.iloc[0]['raw_value']
        pmsg = processMsg(msg)
        printDict(pmsg)
        thisFault = msg
    else:
        thisFault = 'n/a'

    if verboseFlag:
        print('\nReport expected message types during pod init')
        doThePrintSuccess(podInitSuccessfulActions)

        print('\nReport other message that did not get desired response (includes 02 and 06)')
        doThePrintOther(podOtherMessages)

    # if an output filename is provided - write out summary to it (csv format)
    if outFile:
        # set up a table format order
        headerString = 'Who, finish State, antenna, lastMsg Date, podOn (hrs), radioOn (hrs), radioOn (%), ' + \
           'num Messages, numSend, numRecv, ' + \
           '#Nonce Resync, #0e, ' \
           '#Basal, #TB, #Bolus, ' + \
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

        # Calculate items not yet generated
        insulinDelivered = podRun.iloc[-1]['total_insulin']
        numberOfStatusRequests = len(podSuccessfulActions[podSuccessfulActions.startMessage=='0e'])
        numberOfBasal = len(podSuccessfulActions[podSuccessfulActions.startMessage=='1a13'])
        numberOfTB = len(podSuccessfulActions[podSuccessfulActions.startMessage=='1a16'])
        numberOfBolus = len(podSuccessfulActions[podSuccessfulActions.startMessage=='1a17'])

        # write out the information for csv (don't want extra spaces for this )
        stream_out.write(f'{thisPerson},{thisFinish},{thisAntenna},{lastDate},{msgLogHrs},')
        stream_out.write(f'{radioOnHrs},{100*radioOnHrs/msgLogHrs},{number_of_messages},')
        stream_out.write(f'{send_receive_commands[1]},{send_receive_commands[0]},')
        stream_out.write(f'{len(nonceResync)},{numberOfStatusRequests},{numberOfBasal},{numberOfTB},')
        stream_out.write(f'{numberOfBolus},{numberScheduleBeforeTempBasal},{numberScheduleBasalLessThan30sec},')
        stream_out.write(f'{insulinDelivered},')
        stream_out.write(f'{thisFault},{thisFile}')
        stream_out.write('\n')
        stream_out.close()

    return df, podState, podSuccessfulActions
