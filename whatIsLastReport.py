# run the most recent file and append to master csv
from fileio.get_file_list import get_file_list
from fileio.getAnalysisIO import getAnalysisIO

vFlag = 1  # just get the filelist
macFlag = 0  # 0 = use Drobo; 1 use Mac hard drive

filePath, outFile = getAnalysisIO(1, "Loop", vFlag, macFlag)
fileDateList = get_file_list(filePath)

print(' *** Last Loop Report:      {:s}'.format(fileDateList[-1][0]))

macFlag = 0  # 0 = use Drobo; 1 use Mac hard drive

filePath, outFile = getAnalysisIO(1, "FX", vFlag, macFlag)
fileDateList = get_file_list(filePath)

print(' *** Last FreeAPS X Report: {:s}'.format(fileDateList[-1][0]))
