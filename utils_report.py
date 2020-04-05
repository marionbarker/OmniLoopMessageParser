import pandas as pd
import numpy as np

"""
utils_report.py
    This code has functions to handle reporting to stdout
"""

def writePodDict(thisFile, podDict):
    # print a few things then returns
    print(' Report on Omnipod from {:s}'.format(thisFile))
    print(' Remember - pod lot, etc., is limited to the pod currently active')
    if 'lot' in podDict:
        lot = podDict['lot']
        tid = podDict['tid']
        piv = podDict['piVersion']
    else:
        lot = 'unknown'
        tid = 'unknown'
        piv = 'unknown'
    print('  Pod Lot: {:s}, PI: {:s}, PM: {:s}\n'.format(podDict['lot'],
        podDict['piVersion'], podDict['pmVersion']))

    return lot, tid, piv


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
        if keys=='TB':
            numShortTB          = subDict['numShortTB']
            numSchBasalbeforeTB = subDict['numSchBasalbeforeTB']
            numRepeatedTB       = subDict['numRepeatedTB']
            numRepeatedShortTB  = subDict['numRepeatedShortTB']
            numrepeated19MinTB  = subDict['numrepeated19MinTB']

    if vFlag:
        print('\n    #TB with SchBasal before     : {:5d}'.format(numSchBasalbeforeTB))
        print('    #TB sent at <30s interval    : {:5d}'.format(numShortTB))
        print('    #TB repeated value           : {:5.0f}'.format(numRepeatedTB))
        print('    #TB repeated value <30s      : {:5.0f}'.format(numRepeatedShortTB))
        print('    #TB rep value >=30s & <19min : {:5.0f}'.format(numrepeated19MinTB))
