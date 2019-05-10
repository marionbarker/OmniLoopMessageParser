# run the most recent file and append to master csv
from get_file_list import *
from getAnalysisIO import *

filePath, outFile = getAnalysisIO(1,1)
fileDateList = get_file_list(filePath)

print('Last Loop Report is {:s}'.format(fileDateList[-1][0]))
