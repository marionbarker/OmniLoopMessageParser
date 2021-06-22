# run the most recent file and append to master csv
from fileio.get_file_list import get_file_list
from fileio.getAnalysisIO import getAnalysisIO

filePath, outFile = getAnalysisIO(1, 1, 0)
fileDateList = get_file_list(filePath)

print('Last Loop Report is {:s}'.format(fileDateList[-1][0]))
