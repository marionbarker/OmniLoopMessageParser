from messageLogs_functions import *
from analyzePodMessages import *
from analyzeAllPodsInDeviceLog import *
from utils_report import *
import pandas as pd

    # Configure for new Device Communication Log (Loop 2.2)
    # Need this to work with either format - change logic stepwise to be
    # more modular until done

def main(thisPath, thisFile, outFile, vFlag):
    # determine type of Loop Report
    filename = thisPath + '/' + thisFile
    fileType, logDF, podDict, fault_report = persist_read_file(filename)

    if fileType == "unknown":
        print('\n *** Did not recognize file type')
        print('  Parser did not find required section in file: \n', \
              '     ', thisFile, '\n',  \
              '     ## MessageLog or\n', \
              '     ## Device Communication Log')
        return

    if fileType == "messageLog":
        print('\n----------------------------------------')
        print('  This file uses MessageLog, {:s}'.format(thisFile))
        print('----------------------------------------')
        numChunks = 1 # number of pods in log file is always 1
        podFrame, podState, actionFrame, actionSummary = analyzePodMessages(thisFile,
            logDF, podDict, fault_report, outFile, vFlag, numChunks)
        if vFlag == 4:
            thisOutFile = 'm:/SharedFiles/LoopReportPythonAnalysis' + '/' \
                + 'verboseOutput' + '/' + 'logDF_out.csv'
            print('\n  Sending log dataframe output to \n    ',thisOutFile)
            logDF.to_csv(thisOutFile)

    elif fileType == "deviceLog":
        print('\n----------------------------------------')
        print('  This file uses Device Communication Log, {:s}'.format(thisFile))
        analyzeAllPodsInDeviceLog(thisFile,
            logDF, podDict, fault_report, outFile, vFlag)
        if vFlag == 4:
            thisOutFile = 'm:/SharedFiles/LoopReportPythonAnalysis' + '/' \
                + 'verboseOutput' + '/' + 'logDFCmb_out.csv'
            print('\n  Sending log dataframe (all pods in report) to \n    ',thisOutFile)
            logDF.to_csv(thisOutFile)
