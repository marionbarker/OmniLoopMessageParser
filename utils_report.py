import pandas as pd
import numpy as np
import os
from utils_pod import *

"""
utils_report.py
    This code has functions to handle reporting to stdout
"""

def printActionSummary(actionSummary, vFlag):
    # initialize values just in case
    numShortTB = np.nan
    numSchBasalbeforeTB = np.nan
    numRepeatedTB = np.nan
    print('\n  Action Summary with sequential 4 or 2 message sequences with action response times in sec')
    print('      Action        : #Success,  mean, [  min,  max  ] : #Incomplete')
    #actionSummary
    #printDict(actionSummary)

    for keys, values in actionSummary.items():
        subDict = values
        print('    {:14s}  :  {:5.0f},  {:5.0f},  [{:5.0f}, {:5.0f} ] : {:5d}'.format( \
          keys, subDict['countCompleted'], subDict['meanResponseTime'], \
          subDict['minResponseTime'], subDict['maxResponseTime'], \
          subDict['countIncomplete']))
        # deprecated (Pete fixed code)
        #if keys=='CnxSetTmpBasal':
        #    numShortTB          = subDict['numShortTB']
        #    numSchBasalbeforeTB = subDict['numSchBasalbeforeTB']
        #    numRepeatedTB       = subDict['numRepeatedTB']
        #    numRepeatedShortTB  = subDict['numRepeatedShortTB']
        #    numrepeated19MinTB  = subDict['numrepeated19MinTB']

    # deprecated (Pete fixed code)
    #if vFlag==1:
    #    print('\n    #TB with SchBasal before     : {:5d}'.format(numSchBasalbeforeTB))
    #    print('    #TB sent at <30s interval    : {:5d}'.format(numShortTB))
    #    print('    #TB repeated value           : {:5.0f}'.format(numRepeatedTB))
    #    print('    #TB repeated value <30s      : {:5.0f}'.format(numRepeatedShortTB))
    #    print('    #TB rep value >=30s & <19min : {:5.0f}'.format(numrepeated19MinTB))
    return

def printInitFrame(podInitFrame):
    print('\n  CumSec: seqNum: expectAction  : expMT  :success: actMT  : ' \
           'actPP: ppMeaning')
    for index, row in podInitFrame.iterrows():
        print('  {:5.0f}: {:7d}: {:14s}: {:7s}:    {:3s}: {:7s}: ' \
            '{:5d}: {:14s}'.format(row['timeCumSec'],
            row['seqNum'], row['expectAction'], row['expectMT'],
            getStringFromLogic(row['statusBool']), row['actualMT'],
            row['actualPP'], row['ppMeaning']))
    return

def printPodInfo(podInfo, nomNumSteps):
    if 'rssiValue' in podInfo:
        # print('\n')
        if podInfo['numInitSteps'] > nomNumSteps:
            print('    *** pod exceeded nominal init steps of {:d}' \
                  ' ***'.format(nomNumSteps))
        print('    Pod: Address {:s}, Lot {:s}, PI: {:s}, gain {:d}, rssi {:d}, ' \
              'numInitSteps {:d}'.format(podInfo['address'], podInfo['lot'],
              podInfo['piVersion'],
              podInfo['recvGain'], podInfo['rssiValue'], podInfo['numInitSteps']))
    return

def printLogInfoSummary(logInfoDict):
    #
    # print out summary information to stdout window
    # need this True to get the actionSummary used to fill csv file
    podOnTimeString = ''
    if logInfoDict.get('podOnTime'):
        podOnTimeString = '            Pod active time (hrs) : {:6.1f}'.format(logInfoDict['podOnTime']/60)
    if logInfoDict.get('logFileHasInit'):
        print('\n  This log starts from initialization of pod')
        print(podOnTimeString)
    else:
        print('\n  This log contains only a portion of pod messages')
        print(podOnTimeString)
        print('\n  Report below is just for the portion contained in the log')
    print('\n            First message for pod :', logInfoDict['first_msg'])
    print('            Last  message for pod :', logInfoDict['last_msg'])
    print('  Total elapsed time in log (hrs) : {:6.1f}'.format(logInfoDict['msgLogHrs']))
    print('                Radio on estimate : {:6.1f}, {:5.1f}%'.format(logInfoDict['radioOnHrs'], 100*logInfoDict['radioOnHrs']/logInfoDict['msgLogHrs']))
    print('   Number of messages (sent/recv) :{:5d} ({:4d} / {:4d})'.format(logInfoDict['numMsgs'],
        logInfoDict['send_receive_messages'][1], logInfoDict['send_receive_messages'][0]))
    print('    Messages in completed actions :{:5d} : {:.1f}%'.format( \
        logInfoDict['totalCompletedMessages'], logInfoDict['percentCompleted']))
    print('          Number of nonce resyncs :{:5d}'.format(logInfoDict['numberOfNonceResync']))
    print('            Insulin delivered (u) : {:7.2f} ({:s})'.format(logInfoDict['insulinDelivered'], logInfoDict['sourceString']))
    print('       Total Bolus Req in log (u) : {:7.2f}'.format(logInfoDict['totBolus']))
    if 'autB' in logInfoDict:
        if logInfoDict['manB'] < logInfoDict['totBolus']:
            print('                       Manual (u) : {:7.2f}, {:3.0f} %'.format(logInfoDict['manB'], 100*logInfoDict['manB']/logInfoDict['totBolus']))
            print('                    Automatic (u) : {:7.2f}, {:3.0f} %'.format(logInfoDict['autB'], 100*logInfoDict['autB']/logInfoDict['totBolus']))
    return

def printLoopVersion(loopVersionDict):
    print('  ----------------------------------------')
    print('        Version : {:s}'.format(loopVersionDict['Version']))
    print('      gitBranch : {:s}'.format(loopVersionDict['gitBranch']))
    print('      gitRev    : {:s}'.format(loopVersionDict['gitRevision'][0:8]))
    print('      buildDate : {:s}'.format(loopVersionDict['buildDateString']))
    print('     sourceRoot : {:s}'.format(loopVersionDict['sourceRoot']))
    return

def writePodInfoToOutputFile(outFile, lastDate, thisFile, podInfo):
    # check if file exists
    isItThere = os.path.isfile(outFile)
    # now open the file
    stream_out = open(outFile,mode='at')
    if not isItThere:
        # set up a table format order
        headerString = 'date, filename, lot, rssi, numInitSteps'
        stream_out.write(headerString)
        stream_out.write('\n')
    stream_out.write(f'{lastDate},')
    stream_out.write('{:s},'.format(thisFile))
    stream_out.write('{:s},'.format(podInfo['lot']))
    stream_out.write('{:d},'.format(podInfo['rssiValue']))
    stream_out.write('{:d},'.format(podInfo['numInitSteps']))
    stream_out.write('\n')
    stream_out.close()

def printPodDict(podDict):
    # print a few things then returns
    # add protection here
    if 'address' in podDict:
        print('    Pod: Address {:s} (pod), (newest pod)(Lot {:s}, PI: {:s}'.format(podDict['address'],
                podDict['lot'], podDict['piVersion']))
    else:
        print('      Missing podDict, check report for ## OmnipodPumpManager section')

def printFrameDebug(frame):
    print('\n Debug printout of head and tail')
    print(frame.head())
    print('\n')
    print(frame.tail())
    print('\n')
    return

def writePodInitStateToOutputFile(outFile, commentString, podInitState):
    print('\n *** Sending podInitState {:s}, to \n     {:s}'.format(commentString, outFile))
    # select the desired columns and order for output
    columnList = ['logIdx','timeStamp','deltaSec','timeCumSec',
        'seqNum','expectAction','expectMT','expectPP','success',
        'actualMT','actualPP','ppMeaning','address','msgDict']
    podInitState['success'] = podInitState['statusBool'].apply(getStringFromLogic)
    podInitState = podInitState[columnList]
    podInitState.to_csv(outFile)
    return

def writePodStateToOutputFile(outFile, commentString, podState, logInfoDict):
    print('\n *** Sending podState {:s}, to \n     {:s}'.format(commentString, outFile))
    # change the True False columns to 'y' and '' (make Joe happy)
    podState['TB'] = podState['TB'].apply(getStringFromLogic)
    podState['SchB'] = podState['SchBasal'].apply(getStringFromLogic)
    podState['Bolus'] = podState['Bolus'].apply(getStringFromLogic)
    # select the desired columns and order for output
    if 'manB' in logInfoDict:
        podState['autoBolus'] = podState['autoBolus'].apply(getStringFromLogic)
        columnList = ['logIdx','timeStamp','deltaSec','timeCumSec',
            'radioOnCumSec','seqNum','pod_progress','type','msgType',
            'insulinDelivered','reqTB','TB','SchB','reqBolus','Bolus',
            'autoBolus','address','msgDict']
    else:
        columnList = ['logIdx','timeStamp','deltaSec','timeCumSec',
            'radioOnCumSec','seqNum','pod_progress','type','msgType',
            'insulinDelivered','reqTB','TB','SchB','reqBolus','Bolus',
            'address','msgDict']
    podState = podState[columnList]
    podState.to_csv(outFile)
    return


def writeDescriptivePodStateToOutputFile(outFile, commentString, podState):
    print('\n *** Sending descriptivePodState {:s}, to \n     {:s}'.format(commentString, outFile))
    # create descriptive string based on message
    podState['description'] = podState.apply(lambda row : getDescriptiveStringFromPodStateRow(row['msgDict'],
                                  row['reqTB'], row['reqBolus'], row['pod_progress']), axis = 1)
    # select the desired columns and order for output
    podState['timeCumMin'] = podState['timeCumSec'].apply(minStrFromSec)
    verboseFlag = 1
    # add ,'msgDict' if want more verbosity
    if verboseFlag:
        columnList = ['timeStamp','deltaSec','timeCumSec',
            'radioOnCumSec','seqNum','address','pod_progress',
            'type','msgType', 'insulinDelivered','description']
    else:
        columnList = ['timeStamp','deltaSec','timeCumMin',
            'pod_progress', 'msgType', 'insulinDelivered','description']
    podState = podState[columnList]
    podState.to_csv(outFile)
    return

def getStringFromLogic(bool):
    if bool:
        return 'y'
    else:
        return ''

def minStrFromSec(value):
    minStr = '{:.1f}'.format(value / 60)
    return minStr

def writePodox0115ToOutputFile(outFile, thisFile, pod0x0115Response):
    # check if file exists
    isItThere = os.path.isfile(outFile)
    # now open the file
    stream_out = open(outFile,mode='at')
    if not isItThere:
        # set up a table format order
        headerString = 'time, cumSec, #07toPod, #03toPod, #0115frmPod, ' + \
            'address, gain, rssi, podProg, podAddr, piVer, ' + \
            'lot, tid, filename'
        stream_out.write(headerString)
        stream_out.write('\n')
    for index, row in pod0x0115Response.iterrows():
        stream_out.write(f'{row.timeStamp},')
        stream_out.write(f'{row.timeCumSec},')
        stream_out.write(f'{row.num07},')
        stream_out.write(f'{row.num03},')
        stream_out.write(f'{row.num0115},')
        stream_out.write(f'{row.address},')
        stream_out.write(f'{row.recvGain},')
        stream_out.write(f'{row.rssiValue},')
        stream_out.write(f'{row.pod_progress},')
        stream_out.write(f'{row.podAddr},')
        stream_out.write(f'{row.piVersion},')
        stream_out.write(f'{row.lot},')
        stream_out.write(f'{row.tid},')
        stream_out.write(f'{thisFile}\n')
    stream_out.close()
