from parsers.messageLogs_functions import loop_read_file
from analysis.analyzePodMessages import analyzePodMessages
from analysis.analyzeAllPodsInDeviceLog import analyzeAllPodsInDeviceLog
from util.report import printLoopDict
from util.report import writeCombinedLogToOutputFile
from util.report import generatePlot
import platform


def main(fileDict, outFlag, vFlag):
    # read file, create dictionaries and DataFrames
    loopReadDict = loop_read_file(fileDict)
    # loopReadDict has keys:
    #   fileDict, logDF, podMgrDict, faultInfoDict,
    #   loopVersionDict, determBasalDF
    fileDict = loopReadDict['fileDict']
    print("fileDict['recordType'] = ", fileDict['recordType'])
    fapsxDF = loopReadDict['determBasalDF']
    if len(fapsxDF) > 0:
        print("Max # json lines ", fapsxDF['num_json_lines'].max())

    print('\n------------------------------------------')
    print('  File: {:s}'.format(fileDict["personFile"]))
    if len(loopReadDict['loopVersionDict']):
        commentString = 'Loop Version reported in file'
        maxItems = 10
        printLoopDict(commentString, maxItems, loopReadDict['loopVersionDict'])

    if len(loopReadDict['faultInfoDict']) and vFlag == 4:
        commentString = 'PodInfoFaultEvent reported in file'
        maxItems = 10
        printLoopDict(commentString, maxItems, loopReadDict['faultInfoDict'])

    if len(loopReadDict['podMgrDict']) and vFlag == 4:
        commentString = 'podMgrDict reported in file'
        maxItems = 3  # address, activated at, expired at
        printLoopDict(commentString, maxItems, loopReadDict['podMgrDict'])

    if fileDict['recordType'] == "unknown":
        print('\n *** Did not recognize file type')
        print('  Parser did not find required section in file: \n',
              '     ', fileDict["personFile"], '\n',
              '     ## MessageLog or\n',
              '     ## Device Communication Log')
        return

    if fileDict['recordType'] == "messageLog":
        print('  ----------------------------------------')
        print('  This file uses MessageLog')
        print('  ----------------------------------------')
        numChunks = 1  # number of pods in log file is always 1
        analyzePodMessages(fileDict, loopReadDict['logDF'],
                           loopReadDict['podMgrDict'],
                           outFlag, vFlag, numChunks)
        if vFlag == 4:
            thisOutFile = outFlag + '/' + 'logDF_out.csv'
            writeCombinedLogToOutputFile(thisOutFile, loopReadDict['logDF'])

    elif fileDict['recordType'] == "deviceLog":
        print('  ----------------------------------------')
        print('  This file uses Device Communication Log')
        analyzeAllPodsInDeviceLog(fileDict, loopReadDict, outFlag, vFlag)
        if vFlag == 4:
            thisOutFile = outFlag + '/' + 'logDFCmb_out.csv'
            writeCombinedLogToOutputFile(thisOutFile, loopReadDict['logDF'])

    elif fileDict['recordType'] == 'FAPSX':
        print('  ----------------------------------------')
        print('  This file a FAPSX log file')
        analyzeAllPodsInDeviceLog(fileDict, loopReadDict, outFlag, vFlag)
        thisOutFile = outFlag + '/' + 'logDFCmb_out.csv'
        writeCombinedLogToOutputFile(thisOutFile, loopReadDict['logDF'])

        # Prepare the output from parsing the Determine Basal record FreeAPS X
        fapsxDF = loopReadDict['determBasalDF']
        # create a csv file but don't add unique user name/dates to it
        thisOutFile = outFlag + '/' + 'fapsxDF_out.csv'
        print("Determine Basal csv file created: ", thisOutFile)
        fapsxDF.to_csv(thisOutFile)

        # until we get it updated, PC does not yet do plots
        thisPlatform = platform.system()

        if thisPlatform == 'Windows':
            print("PC plots do not work yet, skip plots")
        else:
            # plot pandas dataframe containing detemine basal data
            thisOutFile = generatePlot(outFlag, fileDict, fapsxDF)
            print('Determine Basal plot created:     ', thisOutFile)

        # repeat this at end of report to make it easier to find
        if len(fapsxDF) > 0:
            print("Min # json lines ", fapsxDF['num_json_lines'].min())
            print("Max # json lines ", fapsxDF['num_json_lines'].max())
