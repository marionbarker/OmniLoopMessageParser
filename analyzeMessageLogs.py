import pandas as pd
from messageLogs_functions import *
from byteUtils import *
from basal_analysis import *
from messagePatternParsing import *

def analyzeMessageLogs(thisPath, thisFile, outFile, verboseFlag, numRowsBeg, numRowsEnd):

    # This is time (sec) radio on Pod stays awake once comm is initiated
    radio_on_time   = 30

    filename = thisPath + '/' + thisFile
    if verboseFlag:
        print('File relative path:', thisFile)
        print('File absolute path:', filename)

    # read the MessageLogs from the file
    commands = read_file(filename)

    # add more stuff and return as a DataFrame
    df = generate_table(commands, radio_on_time)

    if numRowsBeg>0:
        headList = df.head(numRowsBeg)
        print(headList)

    if numRowsEnd>0:
        tailList = df.tail(numRowsEnd)
        print(tailList)

    # set up a few reportable values here from df
    first_command = df.iloc[0]['time']
    last_command = df.iloc[-1]['time']
    send_receive_commands = df.groupby(['type']).size()
    number_of_messages = len(df)

    # this is Eelke's formatting, leave it here,
    # set up summary as a dictionary to use for printing out later
    summary = {}
    summary['first_command'] = '{} (UTC)'.format(df.iloc[0]['time'])
    summary['last_command'] = '{} (UTC)'.format(df.iloc[-1]['time'])
    summary['total time'] = '{}'.format(last_command - first_command)
    summary['# Sent to Pod'] = send_receive_commands[1]
    summary['# Received from Pod']= send_receive_commands[0]
    summary['# Send and Received']= df['command'].count()

    # calculate average times between messages
    mean_seconds_time_delta = (df['time_delta']).mean()
    mean_receive_time_delta = (df.loc[df['type'] == 'receive']['time_delta']).mean()

    if verboseFlag:
        print('Average time between commands =',time.strftime("%H:%M:%S",time.gmtime(mean_seconds_time_delta.astype(int))))
        print('Average time between commands =',round(mean_seconds_time_delta/60,3), 'minutes')
        print('Average receive time after send command =',round(mean_receive_time_delta,3), 'seconds')

    # Prepare a list of the indices to dataframes that are part of a single sequence
    #   i.e., send receive exchanges within one radio-on time
    #   and another list of send only events grouped by adjacency
    #   each list_of is a list of grouped indices
    list_of_sequence_indices, list_of_send_only_indices = generate_sequence(df)
    number_of_sequences = len(list_of_sequence_indices)
    number_of_send_only_sequences = len(list_of_send_only_indices)

    # Prepare of list of the number of individual commands in each sequence
    #     tuples of [number of commands in a sequence, number of sequences with that length]
    # These are not sorted, so the 12-message pair sequence is typically first
    cmds_per_sequence = count_cmds_per_sequence(list_of_sequence_indices)
    cmds_per_send_only_sequence = count_cmds_per_sequence(list_of_send_only_indices)

    # extract timing and parameters from sequences
    time_vs_sequenceLength = create_time_vs_sequenceLength(df, list_of_sequence_indices, radio_on_time)

    # split into cummulative on time for Pod and Radio, with #messages and response time for each sequence
    podOnCumHrs, radioOnCumHrs, numCmdThisSeq, responseTimeThisSeq = zip(*time_vs_sequenceLength)

    degOfFit = 1
    mPodHrs, bPodHrs = np.polyfit(podOnCumHrs, responseTimeThisSeq, degOfFit)
    mRadioHrs, bRadioHrs = np.polyfit(radioOnCumHrs, responseTimeThisSeq, degOfFit)

    totalPodHrs = podOnCumHrs[-1]
    totalRadioHrs = radioOnCumHrs[-1]
    initialResponseSec = bPodHrs
    finalResponseSec = bPodHrs + mPodHrs*totalPodHrs

    # find all instances of '06' - request for nonce resync
    nonceResync = df[df.command=='06']
    numberOfNonceResync = len(nonceResync)

    faultInFile = df[df.command=='02'].raw_value
    isFaultInFile = len(faultInFile)

    seqDelTime = [podOnCumHrs[n+1]-podOnCumHrs[n] for n in range (0, len(podOnCumHrs)-1)]

    medSeqDelTime  = 60.0*np.median(seqDelTime)  # median time in minutes
    meanSeqDelTime = 60.0*np.mean(seqDelTime) # mean time in minutes
    minSeqDelTime  = 60.0*np.min(seqDelTime)  # min time in minutes
    maxSeqDelTime  = 60.0*np.max(seqDelTime)  # max time in minutes

    cmds_per_seq_histogram, total_messages_all_seq = get_cmds_per_seq_histogram(cmds_per_sequence)
    cmds_per_send_only_seq_histogram, total_messages_send_only = get_cmds_per_seq_histogram(cmds_per_send_only_sequence)
    longestSendOnlyRun = len(cmds_per_send_only_seq_histogram)

    # get distribution for all commands from full DataFrame
    cmd_count = df.groupby(['type','command']).size().reset_index(name='count')
    if verboseFlag:
        print('Distribution of all messages by command')
        print(cmd_count)

    # get distribution for all commands in the Sequences
    flatListSequence = flatten(list_of_sequence_indices)
    seqDF = df.iloc[flatListSequence]
    seq_cmd_count = seqDF.groupby(['type','command']).size().reset_index(name='count')
    if verboseFlag:
        print('Distribution of messages in sequences by command')
        print(seq_cmd_count)

    # get distribution for all commands in the send-only lists
    flatListSendOnly = flatten(list_of_send_only_indices)
    soDF = df.iloc[flatListSendOnly]
    so_cmd_count = soDF.groupby(['type','command']).size().reset_index(name='count')
    if verboseFlag:
        print('Distribution of messages sent without a response, by command')
        print(so_cmd_count)

    # new from Eelke 2/27/2019 and updated 3/2/2019
    df_basals_all_messages, df2 = basal_analysis(df)
    print('Using ALL messages:')
    if verboseFlag:
        print(df_basals_all_messages.loc[:,["time", "command", "normal_basal_running_time"]])
        print(df2.sort_values(by=['time']))

    print('  {} normal Basals ran before a new TB was sent'.format(df_basals_all_messages["command"].count()))
    print('  {} normal Basals ran for < 30 seconds'.format(df_basals_all_messages["command"].loc[(df_basals_all_messages["normal_basal_running_seconds"] < 30)].count()))

    df_basals_seq, df2 = basal_analysis(seqDF)
    print('Using just messages that follow send-recv pattern:')
    if verboseFlag:
        print(df_basals_seq.loc[:,["time", "command", "normal_basal_running_time"]])
        print(df2.sort_values(by=['time']))

    # capture the normal basal information
    numberScheduleBeforeTempBasal = df_basals_seq["command"].count()
    numberScheduleBasalLessThan30sec = df_basals_seq["command"].loc[(df_basals_seq["normal_basal_running_seconds"] < 30)].count()
    print('  {} normal Basals ran before a new TB was sent'.format( numberScheduleBeforeTempBasal))
    print('  {} normal Basals ran for < 30 seconds'.format( numberScheduleBasalLessThan30sec))

    # partition file to extract useful information
    (thisPerson, thisFinish, thisAntenna) = parse_info_from_filename(thisFile)
    lastDate = last_command.date()
    lastTime = last_command.time()

    idx = -1
    thisMessage = df.iloc[idx]['raw_value']
    parsedMessage = processMsg(thisMessage)

    insulinDelivered = parsedMessage['total_insulin_delivered']
    insulinNotDelivered = parsedMessage['insulin_not_delivered']
    specialComments = 'None'

    if insulinDelivered == 0 or np.isnan(insulinDelivered):
        # assume this is a fault that doesn't return this information
        # or a nonce Resync
        idx -= 1
        while df.iloc[idx]['type'] != 'receive':
            idx -= 1
        lastRecv = df.iloc[idx]['raw_value']
        parsedPriorMessage = processMsg(lastRecv)

        while parsedPriorMessage['message_type'] == '06':
            idx -= 1
            while df.iloc[idx]['type'] != 'receive':
                idx -= 1
            lastRecv = df.iloc[idx]['raw_value']
            parsedPriorMessage = processMsg(lastRecv)

        print(' idx = ', idx)
        print(' parsedPriorMessage message_type = ', parsedPriorMessage['message_type'])
        print(' parsedPriorMessage raw_value = ', parsedPriorMessage['raw_value'])

        insulinDelivered = parsedPriorMessage['total_insulin_delivered']
        insulinNotDelivered = parsedPriorMessage['insulin_not_delivered']
        specialComments = 'Insulin from {:d} pod message before last'.format(-idx-1)


    # use cmds_per_seq_histogram
    print(' Summary for', thisFile)
    print(f' Upload by {thisPerson} with {thisFinish} ending using {thisAntenna}')
    print('__________________________________________\n')
    print('  Number of Messages in Sequence, Number Occurrences')
    count=0
    for idx in cmds_per_seq_histogram:
        count += 1
        if idx==0:
            continue
        print(' {:5d}, {:8d}'.format(count,idx))

    print('__________________________________________\n')
    print('  Number of Messages in Send-only, Number Occurrences')
    count=0
    for idx in cmds_per_send_only_seq_histogram:
        count += 1
        if idx==0:
            continue
        print(' {:5d}, {:8d}'.format(count,idx))

    print('__________________________________________\n')

    # report nonceResync and faultInFile
    if isFaultInFile:
        thisFault = faultInFile.iloc[0]
    else:
        thisFault = 'N/A'

    print('Fault in MessageLog :', thisFault)

    print('__________________________________________\n')

    # shortened report to copy and paste:
    print('__________________________________________\n')

    print(' Summary for', thisFile)
    print('')
    print('UTC for First Message : {}'.format(first_command))
    print('Pod On   : {:.1f} hrs, '.format(totalPodHrs), \
        'Radio On : {:.2f} hrs, {:.1f}%'.format(totalRadioHrs, 100*totalRadioHrs/totalPodHrs))
    print('Messages: Sent = {:5d},'.format(send_receive_commands[1]), \
        'Recv = {:5d}'.format(send_receive_commands[0]))
    print('Sequences: {:d}, median period {:.2f} minutes'.format(number_of_sequences, medSeqDelTime))
    print('Number nonce resync : {:d}'.format(numberOfNonceResync))
    print('Number send-only msg {:d} in {:d} sequences, longest series : {:d}'.format(total_messages_send_only, number_of_send_only_sequences, longestSendOnlyRun))
    print('Distribution of messages sent without a response:\n       #, command')
    for index, row in so_cmd_count.iterrows():
        print('   {:5d}, {}'.format(row['count'], row['command']))

    print('Response time (sec) : Initial {:.1f}, Final  {:.1f}, Slope {:.3f} s/hrPodLife, {:.3f} s/hrRadioLife'.format(initialResponseSec, finalResponseSec, mPodHrs, mRadioHrs))
    print('Count of normal basal running before TB :', numberScheduleBeforeTempBasal)
    print('Count of normal basal running < 30 sec :', numberScheduleBasalLessThan30sec)
    print('Total insulin delivered = {:.2f} u'.format(insulinDelivered))
    print('Insulin not delivered   = {:.2f} u'.format(insulinNotDelivered))
    print('Special Comments = ', specialComments)


    # report nonceResync and faultInFile
    if isFaultInFile:
        thisFault = faultInFile.iloc[0]
    else:
        thisFault = 'N/A'

    print('Fault in MessageLog :', thisFault)

    print('__________________________________________\n')

    if isFaultInFile:
        processedMsg = processMsg(thisFault)
        for keys,values in processedMsg.items():
            print('  {} =   {}'.format(keys, values))

    # set up a table format order
    headerString = 'Who, finish State, antenna, lastMsg Date, podOn (hrs), radioOn (hrs), radioOn (%), ' + \
       'num Messages, numSend, numRecv, medianMinutes Between Seq, # Sequences, longest SendRecv Seq, ' + \
       '# messages send_only, # send_only sequences, longest SendOnly Run, #Nonce Resync, ' \
       '#Schedule Before TempBasal, #Schedule BasalLess Than30sec, ' + \
       'Initial Pod Response (sec), Final Pod Response (sec), Response Slope (s/podHr), Response Slope (s/radioHr), ' + \
       ' insulin Delivered, insulin Not Delivered, specialComments, #faultInFile, filename'

    if verboseFlag:
        print(headerString)
        print(f'{thisPerson}, {thisFinish}, {thisAntenna}, {lastDate}, '\
              '{:.2f}, {:5.2f}, '.format(totalPodHrs, totalRadioHrs), \
              '{:.1f}%, '.format(100*totalRadioHrs/totalPodHrs),  \
              f'{number_of_messages}, {send_receive_commands[1]}, {send_receive_commands[0]},', \
              '{:5.2f}, '.format(medSeqDelTime), \
              '{:5d}, {:5d}, '.format(number_of_sequences, len(cmds_per_seq_histogram)), \
              '{:5d}, {:5d}, '.format(total_messages_send_only, number_of_send_only_sequences), \
              '{:5d}, {:5d}, '.format(longestSendOnlyRun, numberOfNonceResync), \
              '{:5d}, {:5d}, '.format(numberScheduleBeforeTempBasal, numberScheduleBasalLessThan30sec), \
              '{:5.1f}, {:5.1f}, {:6.3f}, {:6.3f}, '.format(initialResponseSec, finalResponseSec, mPodHrs, mRadioHrs), \
              f'{insulinDelivered}, {insulinNotDelivered}, {specialComments}, {thisFault}, {thisFile}')

    # save the output to a file

    # check if file exists
    isItThere = os.path.isfile(outFile)

    # now open the file
    stream_out = open(outFile,mode='at')

    # write the column headers if this is a new file
    if not isItThere:
        stream_out.write(headerString)
        stream_out.write('\n')

    # write out the information for csv (don't want extra spaces for this )
    stream_out.write(f'{thisPerson},{thisFinish},{thisAntenna},{lastDate},{totalPodHrs},')
    stream_out.write(f'{totalRadioHrs},{100*totalRadioHrs/totalPodHrs},{number_of_messages},')
    stream_out.write(f'{send_receive_commands[1]},{send_receive_commands[0]},')
    stream_out.write(f'{medSeqDelTime}, {number_of_sequences}, {len(cmds_per_seq_histogram)},')
    stream_out.write(f'{total_messages_send_only},{number_of_send_only_sequences},{longestSendOnlyRun},')
    stream_out.write(f'{numberOfNonceResync},{numberScheduleBeforeTempBasal},{numberScheduleBasalLessThan30sec},')
    stream_out.write(f'{initialResponseSec},{finalResponseSec},{mPodHrs},{mRadioHrs},')
    stream_out.write(f'{insulinDelivered},{insulinNotDelivered},')
    stream_out.write(f'{specialComments},{thisFault},{thisFile}')
    stream_out.write('\n')
    stream_out.close()

    # Resync nonce table
    groupBy0602 = df.loc[df['command'].isin(['06','02'])]

    # table for each command
    groupByCmdType = df.groupby(['type','command']).size().reset_index(name='count')

    return df
