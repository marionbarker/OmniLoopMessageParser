# runAll LoopReportFiles in the associated folder with updated antenna
from analyzeMessageLogsNew import *
from get_file_list import *

filePath = 'm:/SharedFiles/LoopReportFiles'
outFile = 'm:/SharedFiles/LoopReportPythonAnalysis/output_master_new.csv'
fileDateList = get_file_list(filePath)

printReport =  1   # print report to screen in nice format
verboseFlag =  0   # if this is 1 then more print stmts

count=0
for row in fileDateList:
    thisFile = row[0]
    (thisPerson, thisFinish, thisAntenna) = parse_info_from_filename(thisFile)
    if thisAntenna != '433MHz':
        print('    Skipping : ', thisFile)
        continue
    print('Processing: ', thisFile)
    analyzeMessageLogsNew(filePath, thisFile, outFile, printReport, verboseFlag)
    count += 1

print('Completed running', count,'files')
