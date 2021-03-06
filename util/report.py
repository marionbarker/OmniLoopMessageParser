import os
from util.pod import getDescriptiveStringFromPodStateRow, getNameFromMsgType
from util.pod import getPodProgressMeaning
from util.misc import printDict

"""
This code has functions to handle reporting to stdout or files
    printXXX: goes to stdout
    writeXXX: written to a file
"""


def printActionSummary(actionSummary):
    print('\n  Action Summary with sequential 4 or 2 message sequences with'
          ' action response times in sec')
    print('      Action        : #Success,  mean, [  min,  max  ] : '
          '#Incomplete')

    for keys, values in actionSummary.items():
        subDict = values
        print('    {:14s}  :  {:5.0f},  {:5.0f},  [{:5.0f}, {:5.0f} ] '
              ': {:5d}'.format(
               keys, subDict['countCompleted'], subDict['meanResponseTime'],
               subDict['minResponseTime'], subDict['maxResponseTime'],
               subDict['countIncomplete']))

    return


def deprecated_printInitFrame(podInitFrame):
    print('\n  CumSec: seqNum: expectAction  : expMT  :success: actMT  : '
          'actPP: ppMeaning')
    for index, row in podInitFrame.iterrows():
        msgDict = row['msgDict']
        seqNum = msgDict['seqNum']
        print('  {:5.0f}: {:7d}: {:14s}: {:7s}:    {:3s}: {:7s}: '
              '{:5d}: {:14s}'.format(
               row['timeCumSec'], seqNum, row['expectAction'],
               row['expectMT'], getStringFromLogic(row['statusBool']),
               row['actualMT'], row['actualPP'], row['ppMeaning']))
    return


def printInitFrame(podInitFrame):
    idx = podInitFrame[podInitFrame.msgType == 'ACK']
    if len(idx):
        print(f'    There were {len(idx)} ACK recorded')
        print('    Note: ACK packet number reported under seqNum column')
    print('\n  CumSec: seqNum: msgType :   msgName       : '
          'lastPP: pod_progressMeaning : podTimeOn(min)')
    last_pod_progress = 0
    cumTime = -podInitFrame.loc[0]['deltaSec']
    for index, row in podInitFrame.iterrows():
        msgDict = row['msgDict']
        cumTime = cumTime + row['deltaSec']
        if 'pod_progress' in msgDict:
            last_pod_progress = msgDict['pod_progress']
        print('  {:5.0f}: {:7d}: {:8s}: {:16s}:  '
              '{:5s}: {:20s}: {:7s}'.format(
               cumTime, msgDict['seqNum'], msgDict['msgType'],
               getNameFromMsgType(msgDict['msgType']),
               getStringFromInt(last_pod_progress),
               getPodProgressMeaning(last_pod_progress),
               getStringFromInt(row['podOnTime'])))
    return


def getStringFromInt(thisValue):
    if thisValue == 0:
        thisString = ''
    else:
        thisString = f'{thisValue}'

    return thisString


def printPodInfo(podInfo, nomNumSteps):
    if 'rssiValue' in podInfo:
        # print('\n')
        if 'numInitSteps' in podInfo:
            if podInfo['numInitSteps'] > nomNumSteps:
                print('    *** Pod exceeded nominal init steps of {:d}'
                      ' ***'.format(nomNumSteps))
            print(f'   Pod: Addr {podInfo["podAddr"]}, '
                  f'Lot {podInfo["lot"]}, '
                  f'PI: {podInfo["piVersion"]}, '
                  f'gain {podInfo["recvGain"]}, '
                  f'rssi {podInfo["rssiValue"]}'
                  f', numInitSteps {podInfo["numInitSteps"]}')
        else:
            printDict(podInfo)
    return


def printLogInfoSummary(logInfoDict):
    #
    # print out summary information to stdout window
    # need this True to get the actionSummary used to fill csv file
    podOnTimeString = ''
    if logInfoDict.get('podOnTime'):
        podOnTimeString = 'Pod active time (hrs) : {:6.1f}'.format(
                           logInfoDict['podOnTime']/60)
    print('\n  This pod status:')
    print('           ', podOnTimeString)
    print('     Insulin delivered by pod (u) : {:7.2f} ({:s})'.format(
           logInfoDict['insulinDelivered'], logInfoDict['sourceString']))
    if logInfoDict.get('logFileHasInit'):
        print('\n  Report below is for all messages to date for this pod')
    else:
        print('\n  Report below is for the subset of messages contained '
              'in the log')
    print('\n            First message in log :', logInfoDict['first_msg'])
    print('            Last  message in log :', logInfoDict['last_msg'])
    print('  Total elapsed time in log (hrs) : {:6.1f}'.format(
           logInfoDict['msgLogHrs']))
    print('                Radio on estimate : {:6.1f}, {:5.1f}%'.format(
           logInfoDict['radioOnHrs'],
           100*logInfoDict['radioOnHrs']/logInfoDict['msgLogHrs']))
    print('   Number of messages (sent/recv) :{:5d} ({:4d} / {:4d})'.format(
           logInfoDict['numMsgs'], logInfoDict['send_receive_messages'][1],
           logInfoDict['send_receive_messages'][0]))
    print('    Messages in completed actions :{:5d} : {:.1f}%'.format(
           logInfoDict['totalCompletedMessages'],
           logInfoDict['percentCompleted']))
    print('          Number of nonce resyncs :{:5d}'.format(
           logInfoDict['numberOfNonceResync']))
    print('       Total Bolus Req in log (u) : {:7.2f}'.format(
           logInfoDict['totBolus']))
    if 'autB' in logInfoDict:
        if logInfoDict['manB'] < logInfoDict['totBolus']:
            print('                  Manual (u) : {:7.2f}, ''{:3.0f} %'.format(
                   logInfoDict['manB'],
                   100*logInfoDict['manB']/logInfoDict['totBolus']))
            print('               Automatic (u) : {:7.2f}, {:3.0f} %'.format(
                   logInfoDict['autB'],
                   100*logInfoDict['autB']/logInfoDict['totBolus']))
    return


def printLoopDict(commentString, maxItems, loopDict):
    print('  ----------------------------------------')
    print(f'  ** {commentString} **')
    cnt = 0
    for key, value in loopDict.items():
        cnt += 1
        if cnt <= maxItems:
            print(f'       {key:20} =   {value}')
    return


def writePodInfoToOutputFile(outFile, lastDate, fileDict, podInfo):
    # check if file exists
    isItThere = os.path.isfile(outFile)
    # now open the file
    stream_out = open(outFile, mode='at')
    if not isItThere:
        # set up a table format order
        headerString = 'date, personFile, lot, rssi, numInitSteps'
        stream_out.write(headerString)
        stream_out.write('\n')
    stream_out.write(f'{lastDate},')
    stream_out.write(f'{fileDict["personFile"]},')
    stream_out.write(f'{podInfo["lot"]},')
    stream_out.write(f'{podInfo["rssiValue"]},')
    stream_out.write(f'{podInfo["numInitSteps"]},')
    stream_out.write('\n')
    stream_out.close()


def printPodDict(podDict):
    # print a few things then returns
    # add protection here
    if 'address' in podDict:
        print('    Pod: Address {:s}'.format(podDict['address']))
    else:
        print('      Missing podDict, check report for ## OmnipodPumpManager '
              'section')


def printFrameDebug(frame):
    print('\n Debug printout of head and tail')
    print(frame.head())
    print('\n')
    print(frame.tail())
    print('\n')
    return


def writepodInitFrameToOutputFile(outFile, commentString, podInitFrame):
    print('\n *** Sending podInitFrame {:s}, to \n     {:s}'.format(
           commentString, outFile))
    writeDescriptivePodStateToOutputFile(outFile, commentString, podInitFrame)
    return


def printUncategorizedMessages(frameBalance, podState):
    # used to report uncategorized messages
    if len(frameBalance) == 0:
        return

    print('\n *** There were {:d} messages not in completed Actions'.format(
           len(frameBalance)))
    # extract msgType and number of occurences
    nonCatDict = frameBalance.groupby(['msgType']).groups
    print('       msgType     : Meaning             : #NotCategorized')
    for keys, values in nonCatDict.items():
        print('        {:10s} :  {:18s} :     {:3d}'.format(
               keys, getNameFromMsgType(keys), len(values)))
    print('\n')

    frameBalance['description'] = frameBalance.apply(
                  lambda row: getDescriptiveStringFromPodStateRow(
                   row['msgDict'], row['reqTB'], row['reqBolus'],
                   row['pod_progress']), axis=1)
    columnList = ['timeStamp', 'deltaSec', 'pod_progress', 'type', 'msgType',
                  'description']
    frameBalance = frameBalance[columnList]
    return


def writePodStateToOutputFile(outFile, commentString, podState, logInfoDict):
    print('\n *** Sending podState {:s}, to \n     {:s}'.format(
           commentString, outFile))
    # change the True False columns to 'y' and '' (make Joe happy)
    podState['TB'] = podState['TB'].apply(getStringFromLogic)
    podState['SchB'] = podState['SchBasal'].apply(getStringFromLogic)
    podState['Bolus'] = podState['Bolus'].apply(getStringFromLogic)
    # select the desired columns and order for output
    if 'manB' in logInfoDict:
        podState['autoBolus'] = podState['autoBolus'].apply(getStringFromLogic)
        columnList = ['logIdx', 'timeStamp', 'deltaSec', 'timeCumSec',
                      'radioOnCumSec', 'seqNum', 'pod_progress', 'type',
                      'msgType', 'insulinDelivered', 'reqTB', 'TB', 'SchB',
                      'reqBolus', 'Bolus', 'autoBolus', 'address', 'msgDict']
    else:
        columnList = ['logIdx', 'timeStamp', 'deltaSec', 'timeCumSec',
                      'radioOnCumSec', 'seqNum', 'pod_progress', 'type',
                      'msgType', 'insulinDelivered', 'reqTB', 'TB', 'SchB',
                      'reqBolus', 'Bolus', 'address', 'msgDict']
    podState = podState[columnList]
    podState.to_csv(outFile)
    return


def writeDescriptivePodStateToOutputFile(outFile, commentString, podState):
    print('\n *** Sending descriptivePodState {:s}, to \n     {:s}'.format(
           commentString, outFile))
    # create descriptive string based on message
    podState['description'] = \
        podState.apply(lambda row: getDescriptiveStringFromPodStateRow(
                row['msgDict'], row['reqTB'], row['reqBolus'],
                row['pod_progress']), axis=1)
    # select the desired columns and order for output
    podState['timeCumMin'] = podState['timeCumSec'].apply(minStrFromSec)
    verboseFlag = 1
    # add ,'msgDict' if want more verbosity
    if verboseFlag:
        columnList = ['timeStamp', 'deltaSec', 'timeCumMin', 'seqNum',
                      'address', 'pod_progress', 'type', 'msgType',
                      'insulinDelivered', 'msgDict', 'description']
    else:
        columnList = ['timeStamp', 'deltaSec', 'timeCumMin',
                      'pod_progress', 'msgType', 'insulinDelivered', 'msgDict',
                      'description']
    podState = podState[columnList]
    podState.to_csv(outFile)
    return


def getStringFromLogic(bool):
    if bool:
        return 'y'
    else:
        return ''


def minStrFromSec(value):
    minStr = '{:.2f}'.format(value / 60)
    return minStr


def writePodInitCmdCountToOutputFile(outFile, thisFile, podInitCmdCount):
    # check if file exists
    isItThere = os.path.isfile(outFile)
    # now open the file
    stream_out = open(outFile, mode='at')
    if not isItThere:
        # set up a table format order
        headerString = 'time(first_or_115), deltaSec(first_or_115), ' + \
                       'gain, rssi, PP(115), lastPP, #initSteps, ' + \
                       '#ACK, #0115, #011b, #1d, ' + \
                       '#07, #03, #08, #19, #1a17, #1a13, #0e, ' + \
                       'podAddr, piVersion, lot, tid, filename'
        stream_out.write(headerString)
        stream_out.write('\n')
    # report values of podInitCmdCount dictionary
    stream_out.write(f'{podInitCmdCount["timeStamp"]},')
    stream_out.write(f'{podInitCmdCount["deltaSec"]},')
    stream_out.write(f'{podInitCmdCount["recvGain"]},')
    stream_out.write(f'{podInitCmdCount["rssiValue"]},')
    stream_out.write(f'{podInitCmdCount["PP115"]},')
    stream_out.write(f'{podInitCmdCount["lastPP"]},')
    stream_out.write(f'{podInitCmdCount["numInitSteps"]},')
    stream_out.write(f'{podInitCmdCount["cntACK"]},')
    stream_out.write(f'{podInitCmdCount["cnt0115"]},')
    stream_out.write(f'{podInitCmdCount["cnt011b"]},')
    stream_out.write(f'{podInitCmdCount["cnt1d"]},')
    stream_out.write(f'{podInitCmdCount["cnt07"]},')
    stream_out.write(f'{podInitCmdCount["cnt03"]},')
    stream_out.write(f'{podInitCmdCount["cnt08"]},')
    stream_out.write(f'{podInitCmdCount["cnt19"]},')
    stream_out.write(f'{podInitCmdCount["cnt1a17"]},')
    stream_out.write(f'{podInitCmdCount["cnt1a13"]},')
    stream_out.write(f'{podInitCmdCount["cnt0e"]},')
    stream_out.write(f'{podInitCmdCount["podAddr"]},')
    stream_out.write(f'{podInitCmdCount["piVersion"]},')
    stream_out.write(f'{podInitCmdCount["lot"]},')
    stream_out.write(f'{podInitCmdCount["tid"]},')
    stream_out.write(f'{thisFile}\n')
    stream_out.close()


def writeCombinedLogToOutputFile(outFile, logDF):
    # print('\n *** Sending Report Dataframe to \n     {:s}'.format(outFile))
    # print('   input columns', logDF.columns)
    columnList = ['time', 'deltaSec', 'address',
                  'type', 'msgDict']
    logDF = logDF[columnList]
    logDF.to_csv(outFile)
    return
