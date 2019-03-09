# test snippets, 3/8/2019
from analyzeMessageLogsNew import *

filePath = 'm:/SharedFiles/LoopReportFiles'
outFile = 'm:/SharedFiles/LoopReportPythonAnalysis/output_test.csv'

verboseFlag =  0   # if this is 1 then more print stmts
numRowsBeg  =  0   # if >0, print this many messages from beginning of record
numRowsEnd  =  0   # if >0, print this many messages from end of record

df, podInit, podRun = analyzeMessageLogsNew(filePath, 'Ben/Loop-Report-2019-02-18-201950-0600_0x34.md', outFile, verboseFlag, numRowsBeg, numRowsEnd)

doPrint = 0
if doPrint:
  print(df.head(20))
  print(podRun.head())
  print(df.tail(20))
  print(podRun.tail())

doPrint = 0
if doPrint:

    print(podRun.head(20))
    print(podSuccessfulActions.head(10))
    print(podOtherMessages.head(10))

    print(podRun.tail(20))
    print(podSuccessfulActions.tail(10))
    print(podOtherMessages.tail(10))


doPrint = 0
if doPrint:

    printMe = df.head()
    print('head of full df'); print(printMe)

    print('all of podInit'); print(podInit)

    printMe = podRun.head()
    print('head of podRun'); print(printMe)

    printMe = df.tail()
    print('tail of df'); print(printMe)

    printMe = podRun.tail()
    print('tail of podRun'); print(printMe)
