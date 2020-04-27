import pandas as pd
import numpy as np
import os

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

def printInitFrame(podInitFrame):
    print('\n  CumSec, seqNum, expectAction  , expMT, status, actMT, ' \
           'actPP, ppMeaning')
    for index, row in podInitFrame.iterrows():
        print('  {:5.0f}, {:7d}, {:14s}, {:7s}, {:5d}, {:7s}, ' \
            '{:5d}, {:14s}'.format(row['timeCumSec'],
            row['seq_num'], row['expectAction'], row['expectMT'],
            row['status'], row['actualMT'],
            row['actualPP'], row['ppMeaning']))

def printPodInfo(podInfo, nomNumSteps):
    if 'rssi_value' in podInfo:
        print('\n')
        if podInfo['numInitSteps'] > nomNumSteps:
            print('    *** pod exceeded nominal init steps of {:d}' \
                  ' ***'.format(nomNumSteps))
        print('    Pod: Address {:s}, Lot {:s}, PI: {:s}, gain {:d}, rssi {:d}, ' \
              'numInitSteps {:d}'.format(podInfo['address'], podInfo['lot'],
              podInfo['piVersion'],
              podInfo['recv_gain'], podInfo['rssi_value'], podInfo['numInitSteps']))
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
    stream_out.write('{:d},'.format(podInfo['rssi_value']))
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
