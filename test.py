# test that older versions work with re-arranged code
from analyzeMessageLogs import *
from get_file_list import *

filePath = 'm:/SharedFiles/LoopReportFiles'
outFile = 'm:/SharedFiles/LoopReportPythonAnalysis/output_test.csv'
fileDateList = get_file_list(filePath)
thisFile = fileDateList[-1][0]

verboseFlag = 1
numRowsBeg = 10
numRowsEnd = 5

df, seqDF = analyzeMessageLogs(filePath, thisFile, outFile, verboseFlag, numRowsBeg, numRowsEnd)

from analyzeMessageLogsNew import *

# used by analyzeMessageLogsNew to report or not report to window
printReport = 1
verboseFlag = 1

thisFile = fileDateList[-1][0]
df, podState, podSuccessfulActions = analyzeMessageLogsNew(filePath, thisFile, outFile, printReport, verboseFlag)

from analyzeMessageLogsRev3 import *
outFile = 0
thisFile = 'Theresa/Loop-Report-2019-03-15-17_19_41Z_Nominal.md'
df, podState, actionFrame, actionSummary = analyzeMessageLogsRev3(filePath, thisFile, outFile)

thisPath = 'm:/SharedFiles/LoopReportFiles'
