# run the most recent file and append to master csv
from main import main
from fileio.get_file_list import get_file_list, getFileDict
from fileio.getAnalysisIO import getAnalysisIO

pathOption = 3  # use standard FreeAPS X file location
vFlag = 4  # Verbose output - all files to Output location
macFlag = 1  # use Drobo rather than Mac hard drive

folderPath, outFlag = getAnalysisIO(pathOption, vFlag, macFlag)
fileDateList = get_file_list(folderPath)

# create fileDict
fileDict = getFileDict(folderPath, fileDateList[-1][0])

# nominal verbose output
main(fileDict, outFlag, vFlag)
