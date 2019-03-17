# run the most recent file and append to master csv
from analyzeMessageLogsRev3 import *
from get_file_list import *

filePath = 'm:/SharedFiles/LoopReportFiles'
fileDateList = get_file_list(filePath)

## Rev3 analysis
outFile = 'm:/SharedFiles/LoopReportPythonAnalysis/output_master_rev3.csv'
df, podState, actionFrame, actionSummary = analyzeMessageLogsRev3(filePath, fileDateList[-1][0], outFile)
