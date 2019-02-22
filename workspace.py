"""
code is stashed here

m:
cd SharedFiles

"""

from analyzeMessageLogs import *
from get_file_list import *

filePath = 'm:/SharedFiles/LoopReportFiles'
outFile = 'm:/SharedFiles/LoopReportPythonAnalysis/output_20190221.csv'
fileList = get_file_list(filePath)

count=0
for thisFile in fileList:
    analyzeMessageLogs(filePath, thisFile, outFile)
    count += 1


## not part of main test
(df, groupBy0602, groupByCmdType) = analyzeMessageLogs('m:/SharedFiles/LoopReportFiles', 'Joe/Loop-Report-2019-02-04-020637-0800_Nominal_origAnt.md', 'm:/SharedFiles/LoopReportPythonAnalysis/output_20190220.csv')

analyzeMessageLogs('m:/SharedFiles/LoopReportFiles', 'Joe/Loop-Report-2019-02-20-184503-0800_Nominal.md', 'm:/SharedFiles/LoopReportPythonAnalysis/output_20190220.csv')
analyzeMessageLogs(filePath, fileList[0], outFile)
analyzeMessageLogs(filePath, fileList[5], outFile)
analyzeMessageLogs(filePath, fileList[11], outFile)
analyzeMessageLogs(filePath, fileList[12], outFile)

(thisPerson, thisFinish, thisAntenna) = parse_info_from_filename(fileList[0])
thisPerson
thisFinish
thisAntenna


"""

Also - Feb 9 is when Pete posted the code that triggers from BG entry
 so will update at 5 min intervals and match sensor timing

Maybe I found something regarding the $40 fault.

In the 2 occasions of my $40 fault it had around 10 occurrences where the normal basal started again after a 30 minute TB which had a duration of <30 seconds.
In comparison with some successful runs these short durations occured < 10 times.
Joe: 7 times, Theresa 3 times, Phillip 2 times and Anders only 1 time.

My first $40:
Ids of TBs where a normal Basal is running beforehand

And from Joe:
for Ben's Loop-Report-2019-02-09-223401-0600_0x40.md
He says:
your $40 fault appears to be another case of depleted Pod batteries.
Your message log was 3760 minutes in length for 4223 commands for an
average of 0.890 minutes per message. The few successful runs that I looked
had an average interval of > 1 min/message and/or < 3500 total messages
(if I had the complete log to look at).

"""

"""

 old way of doing stuff
# control the output here, numRowsXXX is number of rows printed at the beginning and end of the command list
verboseFlag =  0   # if this is 1 then more print stmts
numRowsBeg  =  10   # if >0, print this many messages from beginning of record
numRowsEnd  =  10   # if >0, print this many messages from end of record

thisFile  = 'Ben/MessageLogsFrom_Loop-Report-2019-02-18-201950-0600_0x34.md'
analyzeMessageLogs(thisFile, verboseFlag, numRowsBeg, numRowsEnd)

##
thisFile  = 'Philipp/Loop-Report-2019-02-19-2252300100_Nominal.md'
analyzeMessageLogs(thisFile, verboseFlag, numRowsBeg, numRowsEnd)

##
thisFile  = 'Marion/Loop Report 2019-02-19 17_15_54-08_00_Pod32_Nominal.md'
analyzeMessageLogs(thisFile, verboseFlag, numRowsBeg, numRowsEnd)

##
thisFile  = 'Alessandro/MessageLogs-2019-02-14-1320570100_0x40_800MHzRL.md'
analyzeMessageLogs(thisFile, verboseFlag, numRowsBeg, numRowsEnd)

##
thisFile  = 'Alessandro/MessageLogs-2019-02-17-0921340100_0x40_800MHzRL.md'
analyzeMessageLogs(thisFile, verboseFlag, numRowsBeg, numRowsEnd)

##
thisFile  = 'Anders/Loop-Report-2019-02-18-00_12_5801_00_Nominal.md'
analyzeMessageLogs(thisFile, verboseFlag, numRowsBeg, numRowsEnd)

##
thisFile  = 'Joe/Loop-Report-2019-02-18-131406-0800_0x14.md'
analyzeMessageLogs(thisFile, verboseFlag, numRowsBeg, numRowsEnd)

##
thisFile  = 'Philipp/Loop-Report-2019-02-16-2150540100_Nominal.md'
analyzeMessageLogs(thisFile, verboseFlag, numRowsBeg, numRowsEnd)

##
thisFile  = 'Theresa/Loop-Report-2019-02-18-18_51_42-07_00_Nominal.md'
analyzeMessageLogs(thisFile, verboseFlag, numRowsBeg, numRowsEnd)
"""
