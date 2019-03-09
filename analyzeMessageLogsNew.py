import pandas as pd
from messageLogs_functions import *
from byteUtils import *
from podStateAnalysis import *
from messagePatternParsing import *

def doThePrintRequest(dictList, frame):
    if len(frame) == 0:
        return
    print('    Successful Basal, TB or Bolus:')
    print('      Request(code)           : #Requests, mean, [ min, max ], response time (sec) ')
    for key,value in dictList.items():
        thisSel   = frame[frame.startMessage==key]
        numberSel = len(thisSel)
        if numberSel:
            print('      {:14s} ({:4s})   : {:5d}, {:5.1f}, [ {:5.1f}, {:5.1f} ]'.format(value, \
                key, numberSel, thisSel['responseTime'].mean(), \
                thisSel['responseTime'].min(), thisSel['responseTime'].max() ))
    return


def doThePrintOther(dictList, frame):
    if len(frame) == 0:
        return
    print('      Message(code)  : #Messages')
    for key,value in dictList.items():
        thisSel   = frame[frame.startMessage==key]
        numberSel = len(thisSel)
        if numberSel:
            print('      {:14s} ({:4s})   : {:5d}'.format(value, key, numberSel))
    return

def analyzeMessageLogsNew(thisPath, thisFile, outFile, verboseFlag, numRowsBeg, numRowsEnd):

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
    # add a time_delta column
    df['timeDelta'] = (df['time']-df['time'].shift()).dt.seconds.fillna(0).astype(float)

    if numRowsBeg>0:
        headList = df.head(numRowsBeg)
        print(headList)

    if numRowsEnd>0:
        tailList = df.tail(numRowsEnd)
        print(tailList)

    # set up a few reportable values here from df, time is in UTC
    first_command = df.iloc[0]['time']
    last_command = df.iloc[-1]['time']
    send_receive_commands = df.groupby(['type']).size()
    number_of_messages = len(df)
    thisPerson, thisFinish, thisAntenna = parse_info_from_filename(thisFile)
    lastDate = last_command.date()
    lastTime = last_command.time()

    # print out summary information to command window
    print('__________________________________________\n')
    print(f' Summary for {thisFile} with {thisFinish} ending')
    print('  There were a total of {:d} messages in the log'.format(len(df)))

    # this is the list of commands that getPodSuccessfulActions uses
    requestDict = { \
      '1a13' : 'Basal', \
      '1a16' : 'TB' , \
      '1a17': 'Bolus'}
    otherDict = { \
      '0x1'  : 'Version', \
      '0x3'  : 'Setup', \
      '0x7'  : 'AssignID', \
      '0x8'  : 'CnfgDelivFlags', \
      '0e'   : 'Status Request', \
      '0x11' : 'Acknwl Alerts', \
      '0x19' : 'Cnfg Alerts', \
      '0x1c' : 'Deactivate Pod', \
      '0x1e' : 'Diagnose Pod', \
      '1f'   : 'CancelDelivery', \
      '1a13' : 'Basal', \
      '1a16' : 'TB', \
      '1a17' : 'Bolus',
      '06'   : 'NonceResync', \
      '02'   : 'Fault'}

    # Process the dataframes and update the pod state
    # First get the pair and insert frames
    minPodProgress = 0
    maxPodProgress = 8
    podInit, emptyMessageList = getPodState(df, minPodProgress, maxPodProgress)
    setUpPodCommands = podInit[podInit.message_type=='0x3']
    numberOfSetUpPodCommands = len(setUpPodCommands)
    print('\n  Pod was initialized with {:d} commands, {:d} SetUp (0x03) required'.format(len(podInit), \
       numberOfSetUpPodCommands))
    if emptyMessageList:
        print('    ***  Detected {:d} empty message(s) while initializing the pod'.format(len(emptyMessageList)))
        print('    ***  indices:', emptyMessageList)

    # Iterate through the podState to determine successful commands for requestDict
    podInitSuccessfulActions, podInitOtherMessages = getPodSuccessfulActions(podInit)

    doThePrintRequest(requestDict, podInitSuccessfulActions)

    # Now get the rest of the pod states while in pod_progress 8 and beyond
    minPodProgress = 8
    maxPodProgress = 15
    podRun, emptyMessageList = getPodState(df, minPodProgress, maxPodProgress)
    print('\n  Pod run (pod_progress>=8) included {:d} commands'.format(len(podRun)))
    if emptyMessageList:
        print('    ***  Detected {:d} empty message(s) while running the pod'.format(len(emptyMessageList)))
        print('    ***  indices:', emptyMessageList)

    # Iterate through the podState to determine successful commands for requestDict
    podSuccessfulActions, podOtherMessages = getPodSuccessfulActions(podRun)
    doThePrintRequest(requestDict, podSuccessfulActions)
    print('#TB after schBasal  :  {:5d}'.format( -99))
    print('#schBasal < 30 sec  :  {:5d}'.format( -99))
    print('Insulin delivered   : {:6.2f} u'.format(podRun.iloc[-1]['total_insulin']))

    # see if there is a fault
    faultRow = df[df.command=='02']
    if len(faultRow):
        msg = faultRow.iloc[0]['raw_value']
        pmsg = processMsg(msg)
        printDict(pmsg)

    print('\nCount of other message types during pod run')
    doThePrintOther(otherDict, podOtherMessages)

    print('\nCount of other message types during pod init')
    doThePrintOther(otherDict, podInitOtherMessages)

    return df, podInit, podRun
