# run the most recent file and append to master csv
from main import main
from fileio.get_file_list import get_file_list, getFileDict
from fileio.getAnalysisIO import getAnalysisIO

vFlag = 4
folderPath, outFile = getAnalysisIO(1, vFlag)
fileDateList = get_file_list(folderPath)

# create fileDict
fileDict = getFileDict(folderPath, fileDateList[-1][0])

# Rev3 analysis
main(fileDict, outFile, vFlag)
