# test snippets, 3/7/2019
from analyzeMessageLogs import *

filePath = 'm:/SharedFiles/LoopReportFiles'
outFile = 'm:/SharedFiles/LoopReportPythonAnalysis/output_test.csv'

verboseFlag =  0   # if this is 1 then more print stmts
numRowsBeg  =  0   # if >0, print this many messages from beginning of record
numRowsEnd  =  0   # if >0, print this many messages from end of record

df, seqDF = analyzeMessageLogs(filePath, 'Marion/Loop Report 2019-02-06 18_38_18-08_00_Pod27_Nominal.md', outFile, verboseFlag, numRowsBeg, numRowsEnd)
#
podState, stateList = podStateAnalysis(seqDF)
print(podState.head())
print(podState.tail())
printList(stateList[0:5])
printList(stateList[-5:-1])

#df, seqDF = analyzeMessageLogs(filePath, 'Philipp/Loop-Report-2019-02-16-2150540100_Nominal_origAnt.md', outFile, verboseFlag, numRowsBeg, numRowsEnd)

#df, seqDF = analyzeMessageLogs(filePath, 'Marion/Loop Report 2019-02-27 17_27_50-08_00_Pod35_Nominal.md', outFile, verboseFlag, numRowsBeg, numRowsEnd)

#df, seqDF = analyzeMessageLogs(filePath, 'Eelke/Loop-Report-2019-02-27-1042520100_0x40.md', outFile, verboseFlag, numRowsBeg, numRowsEnd)
