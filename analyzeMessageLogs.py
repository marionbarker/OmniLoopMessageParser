import pandas as pd
from messageLogs_functions import *

def analyzeMessageLogs(thisPath, thisFile, outFile):

    # hard code these for now
    verboseFlag =  0   # if this is 1 then more print stmts
    numRowsBeg  =  10   # if >0, print this many messages from beginning of record
    numRowsEnd  =  10   # if >0, print this many messages from end of record

    # set up the asleep time as an adjustable parameter
    #   Eelke hard coded 30 sec - which is the time the radio stays on for the Pod
    radio_on_time   = 30 # add new variable name, same as sleep_time_param

    ##filepath = 'M:/SharedFiles/LoopReports/'
    filename = thisPath+'/'+thisFile
    print(thisFile)
    print(filename)
    commands = read_file(filename)
    df = generate_table(commands, radio_on_time)


    if numRowsBeg>0:
        df.head(numRowsBeg)

    if numRowsEnd>0:
        df.tail(numRowsEnd)

    summary = {}

    first_command = df.iloc[0]['time']
    last_command = df.iloc[-1]['time']
    run_time_hours = last_command-first_command
    run_time_hours = run_time_hours.total_seconds()/3600

    summary['first_command'] = df.iloc[0]['time']
    summary['total time'] = '{}'.format(last_command - first_command)

    send_receive_commands = df.groupby(['type']).size()

    summary['# Sent to Pod'] = send_receive_commands[1]
    summary['# Received from Pod']= send_receive_commands[0]

    summary['# Send and Received']= df['command'].count()

    asleep_time = (round(df['time_asleep'].sum()/df['time_delta'].sum() * 100 ,2))
    summary['Asleep Time'] = '{} %'.format(asleep_time)
    summary['Awake Time'] = '{} %'.format(round(100 - asleep_time , 4))

    if verboseFlag:
        print('{:.2f}'.format(run_time_hours))

    # calculate average times between messages

    mean_seconds_time_delta = (df['time_delta']).mean()
    mean_receive_time_delta = (df.loc[df['type'] == 'receive']['time_delta']).mean()

    if verboseFlag:
        print('Average time between commands =',time.strftime("%H:%M:%S",time.gmtime(mean_seconds_time_delta.astype(int))))
        print('Average time between commands =',round(mean_seconds_time_delta/60,3), 'minutes')
        print('Average receive time after send command =',round(mean_receive_time_delta,3), 'seconds')

    # Prepare a list of the indices to dataframes that are part of a single sequence
    sequence_of_cmds = generate_sequence(df)
    number_of_messages = len(df)
    number_of_sequences = len(sequence_of_cmds)

    # Prepare of list of the number of individual commands in each sequence
    #     tuples of [number of commands in a sequence, number of sequences with that length]
    cmds_per_sequence = count_cmds_per_sequence(sequence_of_cmds)


    # Prepare an array of the time since pod started to the first command in each
    #   sequence and the number of commands in that sequence and radio on time
    time_vs_sequenceLength = create_time_vs_sequenceLength(df, sequence_of_cmds, radio_on_time)
    lastElement = time_vs_sequenceLength[-1]
    totalRadioHrs = lastElement[2]

    # break into times (hours since pod start) and #cmds in sequence for plotting
    times = [x[0] for x in time_vs_sequenceLength]
    lengths = [y[1] for y in time_vs_sequenceLength]
    singleton_times = create_singleton_times(time_vs_sequenceLength)
    number_of_singletons = len(singleton_times)
    singleton_ones = [1 for n in range (0, number_of_singletons)]

    # print(f'singleton_times = {singleton_times}')
    # print(f'singleton_ones = {singleton_ones}')
    #print(f'cmds_per_sequence = {cmds_per_sequence}')

    seqDelTime = [times[n+1]-times[n] for n in range (0, len(times)-1)]
    # print('First and last seqDelTime (hrs) =', seqDelTime[0],  seqDelTime[-1])
    # print('First and last seqDelTime (min) =', 60.0*seqDelTime[0],  60.0*seqDelTime[-1])

    medSeqDelTime  = 60.0*np.median(seqDelTime)  # median time in minutes
    meanSeqDelTime = 60.0*np.mean(seqDelTime) # mean time in minutes
    minSeqDelTime  = 60.0*np.min(seqDelTime)  # min time in minutes
    maxSeqDelTime  = 60.0*np.max(seqDelTime)  # max time in minutes

    cmds_per_seq_histogram = get_cmds_per_seq_histogram(cmds_per_sequence)

    print(' Summary for', thisFile)
    print('__________________________________________\n')
    print('  Instances, Number of S/R in Sequence')
    for idx in cmds_per_sequence:
        print(' {:5d}'.format(idx[1]), ' {:8d}'.format(idx[0]))

    print('__________________________________________\n')

    # use cmds_per_seq_histogram
    print(' Summary for', thisFile)
    print('__________________________________________\n')
    print('  Number of Messages in Sequence, Number Occurrences')
    count=0
    for idx in cmds_per_seq_histogram:
        count += 1
        if idx==0:
            continue
        print(' {:5d}'.format(count), ' {:8d}'.format(idx))

    print('__________________________________________\n')


    cmd_count = df.groupby(['type','command']).size().reset_index(name='count')
    cmd_count
    # manually read the number of 06 receives

    # part

    (thisPerson, thisFinish, thisAntenna) = parse_info_from_filename(thisFile)
    lastDate = last_command.date()
    lastTime = last_command.time()

    # set up a table format order
    headerString = 'Who, finishState, antenna, lastMsgDate, podOn(hrs), radioOn(hrs), radioOn(%), ' + \
       'numMessages, numSend, numRecv, medianMinBetweenSeq, #Sequences, ' + \
       ' MaxMsgInSingleSeq, #of1MsgPerSeq, #of2MsgPerSeq, #of4MsgPerSeq, #of6MsgPerSeq, filename'

    print(headerString)
    # Please - no spaces for person, finish or antenna or date - works better for excel import
    print(f'{thisPerson},{thisFinish},{thisAntenna},{lastDate}, '\
          '{:.2f},'.format(run_time_hours), '{:5.2f},'.format(totalRadioHrs), \
          '{:.1f}%,'.format(100*totalRadioHrs/run_time_hours),  \
          f'{number_of_messages}, {send_receive_commands[1]}, {send_receive_commands[0]},', \
          '{:5.2f},'.format(medSeqDelTime), \
          '{:5d},'.format(number_of_sequences), '{:5d},'.format(len(cmds_per_seq_histogram)), \
          '{:5d},'.format(cmds_per_seq_histogram[0]), '{:5d},'.format(cmds_per_seq_histogram[1]), \
          '{:5d},'.format(cmds_per_seq_histogram[3]), '{:5d},'.format(cmds_per_seq_histogram[5]), \
           thisFile)

    # save the output to a file

    # check if file exists
    isItThere = os.path.isfile(outFile)

    # now open the file
    stream_out = open(outFile,mode='at')

    # write the column headers if this is a new file
    if not isItThere:
        stream_out.write(headerString)
        stream_out.write('\n')

    # write out the information
    stream_out.write(f'{thisPerson}, {thisFinish}, {thisAntenna}, {lastDate}, {run_time_hours}, ')
    stream_out.write(f'{totalRadioHrs}, {100*totalRadioHrs/run_time_hours}, {number_of_messages}, ')
    stream_out.write(f'{send_receive_commands[1]}, {send_receive_commands[0]}, ')
    stream_out.write(f'{medSeqDelTime}, {number_of_sequences}, {len(cmds_per_seq_histogram)}, ')
    stream_out.write(f'{cmds_per_seq_histogram[0]}, {cmds_per_seq_histogram[1]}, {cmds_per_seq_histogram[3]}, {cmds_per_seq_histogram[5]}, ')
    stream_out.write(f'{thisFile}')
    stream_out.write('\n')
    stream_out.close()

    # Resync nonce table
    groupBy0602 = df.loc[df['command'].isin(['06','02'])]

    # table for each command
    groupByCmdType = df.groupby(['type','command']).size().reset_index(name='count')

    return (df, groupBy0602, groupByCmdType)
