# run the example files - output to screen should text in
#  test/exampleOutput.txt file
# usage:  python test.py
from main import main
from fileio.get_file_list import getFileDict

outFlag = 0
loopType = "Loop"
vFlag = 0
folderPath = '.'

# Persistent log version, multiple pod session:
testFile = 'test/DeviceCommunicationsLogExample_multiplePods.md'
fileDict = getFileDict(folderPath, testFile, loopType)
main(fileDict, outFlag, vFlag)

# old-style log version, single pod session:
testFile = 'test/MessageLogExample_singlePod.md'
fileDict = getFileDict(folderPath, testFile, loopType)
main(fileDict, outFlag, vFlag)
