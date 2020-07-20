from parsers.messageLogs_functions import loop_read_file
from analysis.analyzePodMessages import analyzePodMessages
from analysis.analyzeAllPodsInDeviceLog import analyzeAllPodsInDeviceLog
from util.report import printLoopVersion, writeCombinedLogToOutputFile

# Configure for new Device Communication Log (Loop 2.2)
# Need this to work with either format - change logic stepwise to be
# more modular until done


def main(thisPath, thisFile, outFile, vFlag):
    # determine type of Loop Report
    filename = thisPath + '/' + thisFile
    loopReadDict = loop_read_file(filename)
    # loopReadDict has keys:
    #   fileType, logDF, podMgrDict, faultInfoDict, loopVersionDict

    print('\n------------------------------------------')
    print('  File: {:s}'.format(thisFile))
    if len(loopReadDict['loopVersionDict']):
        printLoopVersion(loopReadDict['loopVersionDict'])

    if loopReadDict['fileType'] == "unknown":
        print('\n *** Did not recognize file type')
        print('  Parser did not find required section in file: \n',
              '     ', thisFile, '\n',
              '     ## MessageLog or\n',
              '     ## Device Communication Log')
        return

    if loopReadDict['fileType'] == "messageLog":
        print('  ----------------------------------------')
        print('  This file uses MessageLog')
        print('  ----------------------------------------')
        numChunks = 1  # number of pods in log file is always 1
        analyzePodMessages(thisFile, loopReadDict['logDF'],
                           loopReadDict['podMgrDict'],
                           loopReadDict['faultInfoDict'],
                           outFile, vFlag, numChunks)
        if vFlag == 4:
            thisOutFile = 'm:/SharedFiles/LoopReportPythonAnalysis' + '/' \
                          + 'verboseOutput' + '/' + 'logDF_out.csv'
            writeCombinedLogToOutputFile(thisOutFile, loopReadDict['logDF'])

    elif loopReadDict['fileType'] == "deviceLog":
        print('  ----------------------------------------')
        print('  This file uses Device Communication Log')
        analyzeAllPodsInDeviceLog(thisFile, loopReadDict, outFile, vFlag)
        if vFlag == 4:
            thisOutFile = 'm:/SharedFiles/LoopReportPythonAnalysis' + '/' \
                + 'verboseOutput' + '/' + 'logDFCmb_out.csv'
            writeCombinedLogToOutputFile(thisOutFile, loopReadDict['logDF'])
