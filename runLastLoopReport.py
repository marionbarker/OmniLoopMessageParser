# run the most recent file and append to master csv
from analyzeMessageLogsRev3 import *
from get_file_list import *
from getAnalysisIO import *

filePath, outFile = getAnalysisIO(1,1)
fileDateList = get_file_list(filePath)

## Rev3 analysis
df, podState, actionFrame, actionSummary = analyzeMessageLogsRev3(filePath, fileDateList[-1][0], outFile)
