# run the example files - output to screen should match corresponding example output files
# usage:  python test.py > exampleFiles/exampleOutput_test.txt
from main import *

outFile = 0
vFlag = 0
filePath = '.'

## Persistent log version, multiple pod session:
thisFile = 'exampleFiles/DeviceCommunicationsLogExample_multiplePods.md'
main(filePath, thisFile, outFile, vFlag)

## old-style log version, single pod session:
thisFile = 'exampleFiles/MessageLogExample_singlePod.md'
main(filePath, thisFile, outFile, vFlag)
