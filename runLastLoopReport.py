# run the most recent file and append to master csv
from main import main
from fileio.get_file_list import get_file_list
from fileio.getAnalysisIO import getAnalysisIO

vFlag = 4
filePath, outFile = getAnalysisIO(1, vFlag)
fileDateList = get_file_list(filePath)

# Rev3 analysis
main(filePath, fileDateList[-1][0], outFile, vFlag)
