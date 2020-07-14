# run the example files - output to screen should text in
#  test/exampleOutput.txt file
# usage:  python test.py
from main import main

outFile = 0
vFlag = 0
filePath = '.'

# Persistent log version, multiple pod session:
thisFile = 'test/DeviceCommunicationsLogExample_multiplePods.md'
main(filePath, thisFile, outFile, vFlag)

# old-style log version, single pod session:
thisFile = 'test/MessageLogExample_singlePod.md'
main(filePath, thisFile, outFile, vFlag)
