# run the most recent file and append to master csv
from analyzeMessageLogs import *
from get_file_list import *

verboseFlag =  1   # if this is 1 then more print stmts
numRowsBeg  =  10   # if >0, print this many messages from beginning of record
numRowsEnd  =  10   # if >0, print this many messages from end of record

filePath = 'm:/SharedFiles/LoopReportFiles'
outFile = 'm:/SharedFiles/LoopReportPythonAnalysis/output_master.csv'
fileDateList = get_file_list(filePath)

## last runs to csv file
analyzeMessageLogs(filePath, fileDateList[-1][0], outFile, verboseFlag, numRowsBeg, numRowsEnd)
