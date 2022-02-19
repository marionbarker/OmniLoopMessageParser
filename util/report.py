import os
from util.pod import getDescriptiveStringFromPodStateRow, getNameFromMsgType
from util.pod import getPodProgressMeaning
from util.misc import printDict
import matplotlib.pyplot as plt
import numpy as np
from util.crc_16 import crc_16


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
    if 'pmVersion' in podInfo:
        # print('\n')
        printDict(podInfo)
        if 'numInitSteps' in podInfo:
            if podInfo['numInitSteps'] > nomNumSteps:
                print('    *** Pod exceeded nominal init steps of {:d}'
                      ' ***'.format(nomNumSteps))
            if podInfo['podStyle'] == 'Dash':
                # BLE pod
                print(f' Dash Pod: Addr {podInfo["podAddr"]}, '
                      f'Lot {podInfo["lot"]}, '
                      f'Seq {podInfo["tid"]}, '
                      f'Pod_FW: {podInfo["pmVersion"]}, '
                      f'BLE_FW: {podInfo["piVersion"]}'
                      f', numInitSteps {podInfo["numInitSteps"]}')
            elif podInfo['podStyle'] == 'Eros':
                # Eros Pod
                print(f' Eros Pod: Addr {podInfo["podAddr"]}, '
                      f'Lot {podInfo["lot"]}, '
                      f'Tid {podInfo["tid"]}, '
                      f'PM: {podInfo["pmVersion"]}, '
                      f'PI: {podInfo["piVersion"]}, '
                      f'gain {podInfo["recvGain"]}, '
                      f'rssi {podInfo["rssiValue"]}'
                      f', numInitSteps {podInfo["numInitSteps"]}')
            else:
                # Unknown Type of Pod
                print(f' Unkn Pod: Addr {podInfo["podAddr"]}, '
                      f'Lot {podInfo["lot"]}, '
                      f'Tid {podInfo["tid"]}, '
                      f'PM: {podInfo["pmVersion"]}, '
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
    if (('send_receive_messages' in logInfoDict) and
       (logInfoDict['send_receive_messages'].count() == 2)):
        print('   Number of messages (sent/recv) :{:5d} ({:4d} / {:4d})'.
              format(logInfoDict['numMsgs'],
                     logInfoDict['send_receive_messages'][1],
                     logInfoDict['send_receive_messages'][0]))
    # comment out Completed Actions, have not kept that code up to date
    # not relevant for dash testing
    # print('    Messages in completed actions :{:5d} : {:.1f}%'.format(
    #       logInfoDict['totalCompletedMessages'],
    #       logInfoDict['percentCompleted']))
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
    if (logInfoDict['numberOfNonceResync'] > 0):
        print('\n   ## Eros Only')
        print('          Number of nonce resyncs :{:5d}'.format(
               logInfoDict['numberOfNonceResync']))
    # radio on was only needed in early days of Eros testing, drop this
    # print('                Radio on estimate : {:6.1f}, {:5.1f}%'.format(
    #        logInfoDict['radioOnHrs'],
    #        100*logInfoDict['radioOnHrs']/logInfoDict['msgLogHrs']))
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


def generatePlot(outFlag, fileDict, df):
    person = fileDict['person']
    datestring = fileDict['date']
    thisOutFile = outFlag + '/' + person + '_' + \
        datestring + '_' + 'plot.png'
    thisOutFile

    # Defin near 0 IOB
    nearZeroVal = 0.2

    tb_filt0 = df[df.TB_Success == 0]
    tb_filt1 = df[df.TB_Success == 1]
    # value is nan if no TB or SMB was attempted
    tm_failed = len(tb_filt0)
    tb_success = len(tb_filt1)
    tb_suggest = tm_failed+tb_success
    tb_pctSucc = 100 * tb_success / tb_suggest

    smb_filt0 = df[df.SMB_Success == 0]
    smb_filt1 = df[df.SMB_Success == 1]
    # value is nan if no TB or SMB was attempted
    smb_failed = len(smb_filt0)
    smb_success = len(smb_filt1)
    smb_suggest = smb_failed+smb_success
    smb_pctSucc = 100 * smb_success / smb_suggest

    nrow = 5
    ncol = 1
    day_in_sec = 24*60*60
    two_hr_in_sec = day_in_sec/12
    xRange = [0, day_in_sec+1]
    bottom_ticks = np.arange(0, day_in_sec+1, step=two_hr_in_sec)
    mkSize = 10

    fig, axes = plt.subplots(nrow, ncol, figsize=(15, 7))

    title_string = (person + ' ' + datestring +
                    '; Neg IOB < {:4.1f}; '.format(-nearZeroVal) +
                    'Enact Success: {:3.0f}% TB'.format(tb_pctSucc) +
                    ' ({:4d}'.format(tb_success) +
                    ' of {:4d}); '.format(tb_suggest) +
                    '{:3.0f}% SMB'.format(smb_pctSucc) +
                    ' ({:4d}'.format(smb_success) +
                    ' of {:4d})'.format(smb_suggest))

    print()
    print("Plot Title:")
    print(" *** ", title_string)

    axes[0].set_title(title_string)

    df.plot(x='time', y='BG', c='green', ax=axes[0], style='-',
            xlim=xRange, xticks=bottom_ticks)
    df.plot(x='time', y='IOB', c='blue', ax=axes[1], style='-',
            xlim=xRange, xticks=bottom_ticks)
    df.plot(x='time', y='COB', c='green', ax=axes[2], style='-',
            xlim=xRange, xticks=bottom_ticks)

    # plot all the suggestions in green/blue
    df.plot(x='time', y='Basal', c='green', ax=axes[3], style="+",
            xlim=xRange, xticks=bottom_ticks, label="TB(U/hr)")
    df.plot(x='time', y='Bolus', c='blue', ax=axes[3], style=".",
            xlim=xRange, xticks=bottom_ticks, label="SMB(U)")

    # plot the "failed" suggestions in red
    tb_filt0.plot(x='time', y='Basal', c='red', ax=axes[3], style="+",
                  xlim=xRange, xticks=bottom_ticks, label="fail TB")
    smb_filt0.plot(x='time', y='Bolus', c='red', ax=axes[3], style=".",
                   xlim=xRange, xticks=bottom_ticks, label="fail SMB")

    df.plot(x='time', y='SensRatio', c='black', ax=axes[4], style="+",
            xlim=xRange, xticks=bottom_ticks)

    zeroIOB = df[(df.IOB > -nearZeroVal) & (df.IOB < nearZeroVal)]
    zeroIOB.plot(x='time', y='BG', c='blue', style='.', markersize=mkSize,
                 ax=axes[0], label="~0 IOB")
    zeroIOB.plot(x='time', y='IOB', c='blue', style='.', markersize=mkSize,
                 ax=axes[1], label="~0 IOB")
    zeroIOB.plot(x='time', y='COB', c='blue', style='.', markersize=mkSize,
                 ax=axes[2], label="~0 IOB")
    # negative IOB
    dfNegIOB = df[df.IOB < -nearZeroVal]
    dfNegIOB.plot(x='time', y='BG', c='red', style='.', markersize=mkSize,
                  ax=axes[0], label="Neg IOB")
    dfNegIOB.plot(x='time', y='IOB', c='red', style='.', markersize=mkSize,
                  ax=axes[1], label="Neg IOB")
    dfNegIOB.plot(x='time', y='COB', c='red', style='.', markersize=mkSize,
                  ax=axes[2], label="Neg IOB")

    for x in axes:
        x.grid('on')
        x.legend(bbox_to_anchor=(1.11, 1.0), framealpha=1.0)

    idx = 0
    while idx < 4:
        x_axis = axes[idx].axes.get_xaxis()
        # x_label = x_axis.get_label()
        x_axis.set_ticklabels([])
        idx += 1

    # set limits for BG (always in mg/dl)
    axes[0].set_ylabel("BG")
    bg_ylim = axes[0].get_ylim()
    a = min(bg_ylim[0], 0)
    b = max(1.1*bg_ylim[1], 200)
    axes[0].set_ylim([a, b])

    # handle case where IOB is never zero for entire plot
    axes[1].set_ylabel("IOB")
    iob_ylim = axes[1].get_ylim()
    a = min(1.1*iob_ylim[0], -1)
    b = max(1.1*iob_ylim[1], 10)
    axes[1].set_ylim([a, b])

    # handle case where COB is 0 for entire plot
    axes[2].set_ylabel("COB")
    cob_ylim = axes[2].get_ylim()
    a = max(cob_ylim[0], 0)
    b = max(cob_ylim[1], 100)
    axes[2].set_ylim([a, b])

    # Set up y axis for Basal/Bolus
    axes[3].set_ylabel("TB / SMB")
    unit_ylim = axes[3].get_ylim()
    a = min(unit_ylim[0], 0)
    b = 1.2 * unit_ylim[1]
    axes[3].set_ylim([a, b])

    # Set up sensitivity ratio axis scaling
    axes[4].set_ylabel("SensRatio")
    sensRatio_ylim = axes[4].get_ylim()
    a = min(sensRatio_ylim[0], 0.5)
    b = max(sensRatio_ylim[1], 1.5)
    axes[4].set_ylim([a, b])

    plt.draw()
    plt.pause(0.001)
    # plt.pause(5)
    # for use in interactive screen: plt.draw();plt.pause(0.001)
    plt.savefig(thisOutFile)
    plt.close(fig)

    return thisOutFile


def writeDashStats(outFile, podState, fileDict, logInfoDict, numInitSteps, 
                   faultProcessedMsg):
    # if final message is not 0x1d or 0x0202, return without printing
    # print('   podState columns', podState.columns)
    # printDict(logInfoDict)
    # printDict(fileDict)
    secondRow = podState.iloc[1][:]
    secondMsg = secondRow['msgDict']
    lastRow = podState.iloc[-1][:]

    # intialize variables to flag they have not been updated
    sendMsgs = -999
    recvMsgs = -999
    if (('send_receive_messages' in logInfoDict) and
       (logInfoDict['send_receive_messages'].count() == 2)):
        sendMsgs = logInfoDict['send_receive_messages'][1]
        recvMsgs = logInfoDict['send_receive_messages'][0]
    Finish1 = 'Nominal'
    Finish2 = 'Success'
    hexPattern = ''
    pdmRefCode = ''
    notAFault = {'0x1c', '0x18', '0x00'}
    if faultProcessedMsg:
        if faultProcessedMsg['logged_fault'] not in notAFault:
            hexPattern = faultProcessedMsg['rawHex']
            Finish1 = faultProcessedMsg['logged_fault']
            Finish2 = 'Fault'
            pdmRefCode = faultProcessedMsg['pdmRefCode']
    isItThere = os.path.isfile(outFile)
    # now open the file
    stream_out = open(outFile, mode='at')
    if not isItThere:
        # set up a table format order
        headerString = 'Who, Finish1, Finish2, lastMsgDate, podAddr, ' + \
                       'podHrs, logHrs, #Messages, #Sent, #Recv, ' + \
                       '#Recv/#Send%,  InsulinDelivered, LotNo, SeqNo, ' + \
                       'PodFW, BleFW, rawHex(Fault), PDM RefCode, ' + \
                       'filename ' + \
                       'appNameAndVersion, gitRevision, gitBranch, ' + \
                       'buildDate, Comment, More Comments'
        stream_out.write(headerString)
        stream_out.write('\n')
#    loopVersionDict = loopReadDict['loopVersionDict']
#    fileDict = loopReadDict['fileDict']

    if 'pmVersion' in secondMsg:
        podFw = secondMsg['pmVersion']
        bleFw = secondMsg['piVersion']
        lotNo = secondMsg['lot']
        seqNo = secondMsg['tid']
    else:
        podFw = ''
        bleFw = ''
        lotNo = ''
        seqNo = ''
    stream_out.write(f"{fileDict['person']},")
    stream_out.write(f"{Finish1},")
    stream_out.write(f"{Finish2},")
    stream_out.write(f"{logInfoDict['last_msg']},")
    stream_out.write(f"{lastRow['address']},")
    stream_out.write(f"{(logInfoDict['podOnTime']/60):6.2f},")
    stream_out.write(f"{logInfoDict['msgLogHrs']:6.2f},")
    stream_out.write(f"{logInfoDict['numMsgs']},")
    stream_out.write(f"{sendMsgs},")
    stream_out.write(f"{recvMsgs},")
    stream_out.write(f"{100*recvMsgs/sendMsgs:6.0f},")
    stream_out.write(f"{logInfoDict['insulinDelivered']:6.2f},")
    stream_out.write(f"{lotNo},")
    stream_out.write(f"{seqNo},")
    stream_out.write(f"{podFw},")
    stream_out.write(f"{bleFw},")
    stream_out.write(f"{hexPattern},")
    stream_out.write(f"{pdmRefCode},")
    stream_out.write(f"{fileDict['personFile']},")
    stream_out.write(f"{fileDict['appNameAndVersion']},")
    stream_out.write(f"{fileDict['gitRevision']},")
    stream_out.write(f"{fileDict['gitBranch']},")
    stream_out.write(f"{fileDict['buildDateString']},")
    stream_out.write('\n')
    stream_out.close()
    print('  Row appended to ', outFile)
    return
