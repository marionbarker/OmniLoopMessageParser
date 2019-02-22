# runAll LoopReportFiles in the associated folder
from analyzeMessageLogs import *
from get_file_list import *

filePath = 'm:/SharedFiles/LoopReportFiles'
outFile = 'm:/SharedFiles/LoopReportPythonAnalysis/output_20190221.csv'
fileList = get_file_list(filePath)

count=0
for thisFile in fileList:
    analyzeMessageLogs(filePath, thisFile, outFile)
    count += 1

print('Completed running', count,'files')
