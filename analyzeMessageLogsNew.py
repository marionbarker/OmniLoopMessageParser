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
    # add a time_delta column
    df['timeDelta'] = (df['time']-df['time'].shift()).dt.seconds.fillna(0).astype(float)

    # set up a few reportable values here from df, time is in UTC
    first_command = df.iloc[0]['time']
    last_command = df.iloc[-1]['time']
    send_receive_commands = df.groupby(['type']).size()
    number_of_messages = len(df)
    thisPerson, thisFinish, thisAntenna = parse_info_from_filename(thisFile)
    lastDate = last_command.date()
    lastTime = last_command.time()
    deltaTime = (last_command - first_command)
    msgLogHrs = deltaTime.total_seconds()/3600

    # see if there is a fault or nonceResync
    faultRow = df[df.command=='02']
    nonceResync = df[df.command=='06']

    # Process the dataframes and update the pod state
    # First get the pair and insert frames
    minPodProgress = 0
    maxPodProgress = 8
    podInit, emptyMessageList = getPodState(df, minPodProgress, maxPodProgress)
    setUpPodCommands = podInit[podInit.message_type=='0x3']
    numberOfSetUpPodCommands = len(setUpPodCommands)

    # Iterate through the podState to determine successful commands for requestDict
    podInitSuccessfulActions, podInitOtherMessages = getPodSuccessfulActions(podInit)

    # Now get the rest of the pod states while in pod_progress 8 and beyond
    minPodProgress = 8
    maxPodProgress = 15
    podRun, emptyMessageList = getPodState(df, minPodProgress, maxPodProgress)

    # Iterate through the podState to determine successful commands for requestDict
    podSuccessfulActions, podOtherMessages = getPodSuccessfulActions(podRun)

    if printReport:
        # print out summary information to command window
        print('__________________________________________\n')
        print(f' Summary for {thisFile} with {thisFinish} ending')
        print('  Total elapsed time in log (hrs) : {:6.1f}'.format(msgLogHrs))
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

        doThePrintSuccess(podSuccessfulActions)

    # add other analysis here  like TB timing etc

    if len(faultRow):
        msg = faultRow.iloc[0]['raw_value']
        pmsg = processMsg(msg)
        printDict(pmsg)

    if verboseFlag:
        print('\nReport other message types during pod run')
        doThePrintOther(podOtherMessages)

        print('\nReport expected message types during pod init')
        doThePrintSuccess(podInitSuccessfulActions)

        print('\nReport other message types during pod init')
        doThePrintOther(podInitOtherMessages)

    return df, podInit, podRun
