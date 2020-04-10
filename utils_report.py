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
        if 0 and keys=='CnxSetTempBasal':
            numShortTB          = subDict['numShortTB']
            numSchBasalbeforeTB = subDict['numSchBasalbeforeTB']
            numRepeatedTB       = subDict['numRepeatedTB']
            numRepeatedShortTB  = subDict['numRepeatedShortTB']
            numrepeated19MinTB  = subDict['numrepeated19MinTB']

    # deprecated (Pete fixed code)
    if 0 and vFlag:
        print('\n    #TB with SchBasal before     : {:5d}'.format(numSchBasalbeforeTB))
        print('    #TB sent at <30s interval    : {:5d}'.format(numShortTB))
        print('    #TB repeated value           : {:5.0f}'.format(numRepeatedTB))
        print('    #TB repeated value <30s      : {:5.0f}'.format(numRepeatedShortTB))
        print('    #TB rep value >=30s & <19min : {:5.0f}'.format(numrepeated19MinTB))

def printInitFrame(podInitFrame):
    print('idx, timeCumSec, status, expectAction, expectMT, actualMT, ' \
           'expectPP, actualPP, ppMeaning')
    for index, row in podInitFrame.iterrows():
        print(' {:5d}, {:5.0f}, {:2d}, {:14s}, {:5s}, {:5s}, {:d}, ' \
            '{:d}, {:14s}'.format(index,
            row['timeCumSec'], row['status'], row['expectAction'],
            row['expectMT'], row['actualMT'], row['expectPP'],
            row['actualPP'], row['ppMeaning']))

def writePodInfo(podInfo, nomNumSteps):
    if 'rssi_value' in podInfo:
        if podInfo['numInitSteps'] > nomNumSteps:
            print('    *** pod exceeded nominal init steps of {:d}' \
                  ' ***'.format(nomNumSteps))
        print('    Pod: Address {:s}, Lot {:s}, gain {:d}, rssi {:d}, ' \
              'numInitSteps {:d}'.format(podInfo['pod_addr'], podInfo['lot'],
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

""" writePodDict is deprecated
def writePodDict(thisFile, podDict, podInfo):
    # print a few things then returns
    print(' Extracted from ## OmnipodPumpManager')
    if 'lot' in podDict:
        lot = podDict['lot']
        tid = podDict['tid']
        piv = podDict['piVersion']
    else:
        lot = 'unknown'
        tid = 'unknown'
        piv = 'unknown'
    print('  Pod Lot: {:s}, Pod TID: {:s}, PI: {:s}\n'.format(lot, tid, piv))

    if 'rssi_value' in podInfo:
        lot = podInfo['lot']
        tid = podInfo['tid']
        piv = podInfo['piVersion']
        print(' Extracted from 0x01 Message')
        print('  Pod Lot: {:s}, Pod TID: {:s}, PI: {:s}'.format(lot, tid, piv))
        print('  More pod info: recv_gain: {:d}, rssi_value: {:d}, address: {:s}\n'.format(podInfo['recv_gain'],
            podInfo['rssi_value'], podInfo['pod_addr']))

    return lot, tid, piv
"""
