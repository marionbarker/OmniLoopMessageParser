"""
code is stashed here

m:
cd SharedFiles

"""

from analyzeMessageLogs import *
from get_file_list import *

filePath = 'm:/SharedFiles/LoopReportFiles'
outFile = 'm:/SharedFiles/LoopReportPythonAnalysis/output_testing.csv'
fileDateList = get_file_list(filePath)

verboseFlag =  0   # if this is 1 then more print stmts
numRowsBeg  =  0   # if >0, print this many messages from beginning of record
numRowsEnd  =  0   # if >0, print this many messages from end of record

## run most recent report
df = analyzeMessageLogs(filePath, fileDateList[-2][0], outFile, verboseFlag, numRowsBeg, numRowsEnd)

df = analyzeMessageLogs(filePath, fileDateList[-1][0], outFile, verboseFlag, numRowsBeg, numRowsEnd)

# get a 1d message from pod
rawMsg = df.iloc[-3]['raw_value']
byteMsg = bytearray.fromhex(rawMsg)

if byteMsg[0] == 0x1d:
    thisValue = parse_1d(byteMsg)
else:
    thisValue = ignoreMsg(byteMsg)

print(thisValue)



####################################
## good stuff here
from byteUtils import *
from messagePatternParsing import *

msg = '060314217881e4'
processedMsg = processMsg(msg)


msg1 = '1d6804f3e88c004227ff039b'
processedMsg1 = processMsg(msg1)

msg2 = '0e0100032f'
processedMsg2 = processMsg(msg2)

msg3 = '0216020d00001b0d0a5b40108d03ff108f0000189708030d8010'
processedMsg = processMsg(msg3)

for keys,values in processedMsg.items():
    print('  {} =   {}'.format(keys, values))
#

thisMsg = processMsg(msg1)
thisMsg = processMsg(msg2)
thisMsg = processMsg(msg3)
keyList = *thisMsg,
for key in thisMsg:
    if key == 'total_insulin_delivered':
        print('  Total insulin delivered = {:.2f} u'.format(thisMsg[key]))


thisMsg.get('total_insulin_delivered',None)

thisKey = 'total_insulin_delivered'
if thisMsg.get(thisKey,None):
    print('  Total insulin delivered = {:.2f} u'.format(thisMsg[thisKey]))



byteMsg = bytearray.fromhex(msg)
byteList = list(byteMsg)
byte_0 = combineByte(byteList[0])
byte_1 = combineByte(byteList[1])
dword_3 = combineByte(byteList[2:6])
dword_4 = combineByte(byteList[6:10])
cksm = combineByte(byteList[10:12])
#print('0x{:x}'.format(combineByte(byte_0)))
#print('0x{:x}'.format(combineByte(byte_1)))
#print('0x{:x}'.format(combineByte(dword_3)))
#print('0x{:x}'.format(combineByte(dword_4)))














df = analyzeMessageLogs(filePath, fileDateList[-2][0], outFile, 0, 0, 0)
df = analyzeMessageLogs(filePath, fileDateList[-3][0], outFile, 0, 0, 0)

Joe - ended at 70+ hrs with 0x40

Ben - ended at 80 hrs
0216020d0000000e0c4b1c12c0037512c00400099909009000ee
Anders ended with 0x40
0216020d000038000593400e9603ff0e970000185808030d0066
Anders ended with 0x12
0216020d00000000000012ffff03ff0005000088b70800000138

# split up a 1d command:
thisCmd = df.iloc[-3].raw_value
# thisCmd is '1d6802a38084003a4fff035e'
# split into nibbles (characters = 8 bits)
chFromCmd = list(iter(thisCmd))


## this one has a fault
df = analyzeMessageLogs(filePath, fileDateList[6][0], outFile, verboseFlag, numRowsBeg, numRowsEnd)
## this one has no fault
df = analyzeMessageLogs(filePath, fileDateList[0][0], outFile, verboseFlag, numRowsBeg, numRowsEnd)

## code in function:
faultInFile = df[df.command=='02'].raw_value
isFaultInFile = len(faultInFile)

    if isFaultInFile:
        print('Fault found in MessageLogs')
    else:
        print('No Fault found in MessageLogs')
        faultInFile = 'N/A'

    print('  ', faultInFile)

## output if there is a fault:
Fault found in MessageLogs
   2985    0216020d00000000000034ffff03ff0000000089b00900...
Name: raw_value, dtype: object

## output if there is not a fault:
No Fault found in MessageLogs
   N/A

I want the string '0216020d00000000000034ffff03ff0000000089b00900' to paste into output report without the dataframe debris

## to loop through all
count=0
for x in fileDateList:
    analyzeMessageLogs(filePath, x[0], outFile, verboseFlag, numRowsBeg, numRowsEnd)
    count += 1
    if count>3:
        break


## selected tests
df = analyzeMessageLogs('m:/SharedFiles/LoopReportFiles', 'Joe/Loop-Report-2019-02-04-020637-0800_Nominal_origAnt.md', 'm:/SharedFiles/LoopReportPythonAnalysis/output_20190220.csv', verboseFlag, numRowsBeg, numRowsEnd)

analyzeMessageLogs('m:/SharedFiles/LoopReportFiles', 'Joe/Loop-Report-2019-02-20-184503-0800_Nominal.md', 'm:/SharedFiles/LoopReportPythonAnalysis/output_20190220.csv', verboseFlag, numRowsBeg, numRowsEnd)
analyzeMessageLogs(filePath, fileDateList[0][0], outFile, verboseFlag, numRowsBeg, numRowsEnd)

## this one has a fault
df = analyzeMessageLogs(filePath, fileDateList[6][0], outFile, verboseFlag, numRowsBeg, numRowsEnd)

analyzeMessageLogs(filePath, fileDateList[11][0], outFile, verboseFlag, numRowsBeg, numRowsEnd)
analyzeMessageLogs(filePath, fileDateList[12][0], outFile, verboseFlag, numRowsBeg, numRowsEnd)

(thisPerson, thisFinish, thisAntenna) = parse_info_from_filename(fileDateList[0][0])
thisPerson
thisFinish
thisAntenna

## test the get_file_list code
from get_file_list import *
filePath = 'm:/SharedFiles/LoopReportFiles'
fileDateList = get_file_list(filePath)
fileDateList

## test the get_file_list code
from get_file_list import *
filePath = 'm:/SharedFiles/LoopReportFiles'
fileDateList = get_file_list(filePath)
fileDateList
fileDateList[1][0]


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

idx = -1
thisMessage = df.iloc[idx]['raw_value']
parsedMessage = processMsg(thisMessage)

insulinDelivered = parsedMessage['total_insulin_delivered']
insulinNotDelivered = parsedMessage['insulin_not_delivered']
specialComments = 'None'

    if insulinDelivered == 0 or np.isnan(insulinDelivered):
        # assume this is a fault that doesn't return this information
        # or a nonce Resync
        idx = -1
        while df.iloc[idx] != 'receive':
            idx -= 1
        lastRecv = df.iloc[idx]['raw_value']
        parsedPriorMessage = processMsg(lastRecv)

        while parsedPriorMessage['message_type'] == '0x06':
            idx -= 1
            while df.iloc[idx] != 'receive':
                idx -= 1
            lastRecv = df.iloc[idx]['raw_value']
            parsedPriorMessage = processMsg(lastRecv)

        insulinDelivered = parsedPriorMessage['total_insulin_delivered']
        insulinNotDelivered = parsedPriorMessage['insulin_not_delivered']
        specialComments = 'Insulin from {:d} pod message before last'.format(-idx-1)
