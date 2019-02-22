# test snippets
from analyzeMessageLogs import *
from get_file_list import *

filePath = 'm:/SharedFiles/LoopReportFiles'
outFile = 'm:/SharedFiles/LoopReportPythonAnalysis/output_20190221.csv'
## not part of main test
(df, groupBy0602, groupByCmdType) = analyzeMessageLogs(filePath, 'Joe/Loop-Report-2019-02-04-020637-0800_Nominal_origAnt.md', outFile)
