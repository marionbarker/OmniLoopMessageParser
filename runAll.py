# runAll LoopReportFiles in the associated folder
from analyzeMessageLogs import *
from get_file_list import *

filePath = 'm:/SharedFiles/LoopReportFiles'
outFile = 'm:/SharedFiles/LoopReportPythonAnalysis/output_20190221.csv'
fileList = get_file_list(filePath)

verboseFlag =  0   # if this is 1 then more print stmts
numRowsBeg  =  10   # if >0, print this many messages from beginning of record
numRowsEnd  =  10   # if >0, print this many messages from end of record

count=0
for thisFile in fileList:
    analyzeMessageLogs(filePath, thisFile, outFile)
    count += 1

print('Completed running', count,'files')
