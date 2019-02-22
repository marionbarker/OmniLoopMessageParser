# test snippets
from analyzeMessageLogs import *
from get_file_list import *

filePath = 'm:/SharedFiles/LoopReportFiles'
outFile = 'm:/SharedFiles/LoopReportPythonAnalysis/output_20190221.csv'
## append new runs to csv file
analyzeMessageLogs(filePath, 'Marion/Loop Report 2019-02-21 22_29_55-08_00_Pod33_Nominal.md', outFile)
