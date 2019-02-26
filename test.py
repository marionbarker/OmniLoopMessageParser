# test snippets
from analyzeMessageLogs import *
from get_file_list import *

filePath = 'm:/SharedFiles/LoopReportFiles'
outFile = 'm:/SharedFiles/LoopReportPythonAnalysis/output_test.csv'

verboseFlag =  1   # if this is 1 then more print stmts
numRowsBeg  =  10   # if >0, print this many messages from beginning of record
numRowsEnd  =  10   # if >0, print this many messages from end of record

## not part of main test
df = analyzeMessageLogs(filePath, 'Anders/Loop-Report-2019-02-12-02_22_5601_00_0x12_adHocAnt.md', outFile, verboseFlag, numRowsBeg, numRowsEnd)
