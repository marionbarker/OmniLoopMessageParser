# Nov 16, 2019.  The logs got broken again with update done
before the 2019-11-06 18_26_19-08_00.md log

fixed it by putting ### in front of status after MessageLogs
Need to fix code too, but for now do manual file edit.


# Aug 2019, try to fix the "new" message logs in issue report

# set up code
from analyzeMessageLogsRev4 import *
from analyzeMessageLogsRev3 import *
from get_file_list import *
from getAnalysisIO import *

# choose one of these
# run from usual directory
filePath, outFile = getAnalysisIO(1,2)

# run from other directory
filePath, outFile = getAnalysisIO(0,2)

fileDateList = get_file_list(filePath)

df, podState, actionFrame, actionSummary = analyzeMessageLogsRev3(filePath, fileDateList[-12][0], outFile)

# run full code:
df, podState, actionFrame, actionSummary = analyzeMessageLogsRev3(filePath, fileDateList[-1][0], outFile)
df, podState, actionFrame, actionSummary = analyzeMessageLogsRev4(filePath, fileDateList[-1][0], outFile)

# prep to test inside analyzeMessageLogsRev3
thisPath = filePath
thisFile = fileDateList[-1][0]
df, podState, actionFrame, actionSummary = analyzeMessageLogsRev3(filePath, thisFile, outFile)

# run from usual directory and put into nominal outFile
filePath, outFile = getAnalysisIO(1,1)

# bottom of this file has "write to csv" instructions

# test reading
radio_on_time   = 30
filename = thisPath + '/' + thisFile

# read the MessageLogs from the file
commands, podDict = read_file(filename)

# add quick and dirty fix for new Issue Reports (Aug 2019)
tempRaw = commands[-1]['raw_value']
lastRaw = tempRaw.replace('\nstatus:','')
commands[-1]['raw_value'] = lastRaw

# add more stuff and return as a DataFrame
df = generate_table(commands, radio_on_time)



# test that older versions work with re-arranged code
from analyzeMessageLogs import *
from get_file_list import *

filePath = 'm:/SharedFiles/LoopReportFiles'
outFile = 'm:/SharedFiles/LoopReportPythonAnalysis/output_test.csv'
fileDateList = get_file_list(filePath)
thisFile = fileDateList[-1][0]

verboseFlag = 1
numRowsBeg = 10
numRowsEnd = 5

df, seqDF = analyzeMessageLogs(filePath, thisFile, outFile, verboseFlag, numRowsBeg, numRowsEnd)

from analyzeMessageLogsNew import *

# used by analyzeMessageLogsNew to report or not report to window
printReport = 1
verboseFlag = 1

thisFile = fileDateList[-1][0]
df, podState, podSuccessfulActions = analyzeMessageLogsNew(filePath, thisFile, outFile, printReport, verboseFlag)

from analyzeMessageLogsRev3 import *
outFile = 0
thisFile = 'Theresa/Loop-Report-2019-03-15-17_19_41Z_Nominal.md'
df, podState, actionFrame, actionSummary = analyzeMessageLogsRev3(filePath, thisFile, outFile)

thisPath = 'm:/SharedFiles/LoopReportFiles'

##
# run from other directory
from analyzeMessageLogsRev3 import *
from get_file_list import *
from getAnalysisIO import *

# run from usual directory
filePath, outFile = getAnalysisIO(1,2)

# run from other directory
filePath, outFile = getAnalysisIO(0,2)

fileDateList = get_file_list(filePath)

df, podState, actionFrame, actionSummary = analyzeMessageLogsRev3(filePath, fileDateList[-1][0], outFile)

thisPath = filePath
thisFile = fileDateList[-1][0]

podState.iloc[2300:2338,[1,2,4,7,8,9,10,11,12]]

podState.iloc[970:990,[1,2,4,7,8,9,10,11,12]]

podState['insulin_delta'] = (podState['insulinDelivered']-podState['insulinDelivered'].shift()).fillna(0).astype(float)

deltaIdx = podState[podState.insulin_delta != 0]
thisIdx = np.array(deltaIdx.index.to_list())

podState.iloc[thisIdx,[1,2,4,7,8,9,10,11,12,14]]
podState.iloc[thisIdx,[1,7,8,9,10,11,12,14]]

toWrite = podState.iloc[thisIdx,[1,2,4,7,8,9,10,11,12,14]]
toWrite.to_csv("testWrite.csv")


toWrite = podState.iloc[0:990,[1,2,4,7,8,9,10,11,12,14]]
toWrite.to_csv("testWriteAll.csv")

# Nancy Eastman analysis
podState.iloc[500:517,[1,2,4,7,8,9,10,11,12]]
toWrite = podState.iloc[500:517,[1,2,4,7,8,9,10,11,12]]
toWrite.to_csv("writeNancyEastman.csv")


toWrite = podState.iloc[0:1989,[1,2,4,7,8,9,10,11,12,13]]
toWrite.to_csv("testWriteAll.csv")

# to generate timestamp and total insulin delivered
# set up code
from analyzeMessageLogsRev3 import *
from analyzeMessageLogsRev4 import *
from get_file_list import *
from getAnalysisIO import *

# run from other directory
filePath, outFile = getAnalysisIO(0,2)

# run from usual directory
filePath, outFile = getAnalysisIO(1,2)
fileDateList = get_file_list(filePath)

# run full code:
df, podState, actionFrame, actionSummary = analyzeMessageLogsRev3(filePath, fileDateList[-1][0], outFile)
df, podState, actionFrame, actionSummary = analyzeMessageLogsRev4(filePath, fileDateList[-1][0], outFile)

toWrite = podState.iloc[:,[1,2,4,7,8,9,10,11,12,13]]
toWrite.to_csv("testWriteAll.csv")

podState.iloc[2100:2400,[1,2,4,7,8,9,10,11,12]]
podState.iloc[2180:2197,[1,2,4,7,8,9,10,11,12]]

podState.iloc[2180:2197,[2,4,8,9,10,11,12, 13]]

podState.iloc[2186:2197,[2,4,8,9,10,11,12, 13]]


podState.iloc[2400:2445,[1, 2,4,7, 8,9,10,11,12, 13]]


toWrite = podState.iloc[:,[4,7,8,9,10,11,12,13]]
toWrite.to_csv("forAAPScmp.csv")
