# test snippets
from analyzeMessageLogs import *
from get_file_list import *

filePath = 'm:/SharedFiles/LoopReportFiles'
outFile = 'm:/SharedFiles/LoopReportPythonAnalysis/output_test.csv'

verboseFlag =  0   # if this is 1 then more print stmts
numRowsBeg  =  0   # if >0, print this many messages from beginning of record
numRowsEnd  =  10   # if >0, print this many messages from end of record

## not part of main test
df = analyzeMessageLogs(filePath, 'Marion/Loop Report 2019-02-27 17_27_50-08_00_Pod35_Nominal.md', outFile, verboseFlag, numRowsBeg, numRowsEnd)

df = analyzeMessageLogs(filePath, 'Eelke/Loop-Report-2019-02-27-1042520100_0x40.md', outFile, verboseFlag, numRowsBeg, numRowsEnd)
