from parsers.messageLogs_functions import loop_read_file
from util.pd import findBreakPoints
from util.report import writeCombinedLogToOutputFile


def podPairing(thisPath, thisFile, outFile, vFlag):
    filename = thisPath + '/' + thisFile

    noPair = 0
    hasPair = 1
    numSteps = 0
    startRow = 0

    try:
        fileType, logDF, podMgrDict, faultInfoDict, loopVersionDict = \
            loop_read_file(filename)
    except ValueError:
        print('Failed to parse file, ', thisFile)
        return noPair, numSteps, startRow

    # determine type of Loop Report
    if fileType == "unknown":
        # print(thisFile, 'Did not recognize file type' )
        return noPair, numSteps, startRow

    if logDF.loc[0, 'address'] == 'ffffffff':
        # there can be at most one pair here
        # print(thisFile, ', messageLog, hasPair' )
        startRow = 0
        numSteps = stepsToPaired(logDF, startRow, outFile, vFlag)
        return hasPair, numSteps, startRow

    podAddresses, breakPoints = findBreakPoints(logDF)
    numChunks = len(breakPoints)-1

    if fileType == "deviceLog" and numChunks > 1:
        startRow = breakPoints[1]
        if startRow == len(logDF):
            return noPair, numSteps, startRow
        else:
            numSteps = stepsToPaired(logDF, startRow, outFile, vFlag)
            return hasPair, numSteps, startRow

    return noPair, numSteps, startRow


def stepsToPaired(logDF, startRow, outFile, vFlag):
    thisSection = logDF.iloc[startRow:len(logDF)]
    numSteps = 0
    for index, row in thisSection.iterrows():
        numSteps += 1
        if 'pod_progress' in row['msgDict'] and \
                row['msgDict']['pod_progress'] == 8:
            break

    if vFlag == 5 and (numSteps < 3 or numSteps > 25):
        writeCombinedLogToOutputFile(outFile, thisSection.iloc[0:numSteps])

    return numSteps
