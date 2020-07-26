# run the most recent file and append to master csv
from main import main
from fileio.get_file_list import get_file_list, getFileDict
from fileio.getAnalysisIO import getAnalysisIO

vFlag = 4
folderPath, outFlag = getAnalysisIO(1, vFlag)
fileDateList = get_file_list(folderPath)

# create fileDict
fileDict = getFileDict(folderPath, fileDateList[-1][0])

# nominal verbose output
main(fileDict, outFlag, vFlag)

# append to init_survey.csv
vFlag = 3
folderPath, outFlag = getAnalysisIO(1, vFlag)
main(fileDict, outFlag, vFlag)
