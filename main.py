from messageLogs_functions import *
from analyzePodMessages import *
from analyzeAllPodsInDeviceLog import *
from utils_report import *

    # Copied from analyzeMessageLogsRev3 then configure for new Device Log
    # Need this to work with either format - change logic stepwise to be
    # more modular until done

def main(thisPath, thisFile, outFile):
    # configure default values to return if something goes wrong
    df = []
    podState = []
    actionFrame = []
    actionSummary = []
    # decide how to manage this
    filename = thisPath + '/' + thisFile
    fileType, podFrame, podDict, fault_report = persist_read_file(filename)
    print('__________________________________________\n')
    lot, tid, piv = writePodDict(thisFile, podDict)

    if fileType == "unknown":
        print('Did not recognize file type')
    else:
        if fileType == "messageLog":
            print('This file uses MessageLog')
            vFlag = 1; # single pod, be more verbose
            df, podState, actionFrame, actionSummary = analyzePodMessages(thisFile,
                podFrame, podDict, fault_report, outFile, vFlag)

        elif fileType == "deviceLog":
            print('This file uses Device Communication Log; Code to handle this is WIP')
            df, podState, actionFrame, actionSummary = analyzeAllPodsInDeviceLog(thisFile,
                podFrame, podDict, fault_report, outFile)

    return df, podState, actionFrame, actionSummary
