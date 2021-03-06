# Determine the location (Mac or PC)
import os
import platform


def getAnalysisIO(pathOption, vFlag):
    """
    return filePath, outFlag
       When doing "real" analysis, use (1, 4)

       pathOption:
          0 use folder for partial / special purpose / older LoopReportFiles
          1 use folder with complete Loop Reports
          2 specify a specific users' folder by their name

       vFlag:
         0: output analysis to terminal window, outFlag = 0
         1: deprecated, outFlag = 0
         2: output analysis to terminal window, outFlag = 0
         3: output podInitCmdCount to survey file, outFlag is filename
         4: (init, podState, full df) to csv, outFlag verboseOutput folder
    """

    thisPlatform = platform.system()

    if thisPlatform == 'Darwin':
        topPath = os.path.expanduser('~/dev/LoopReportRepository')
    elif thisPlatform == 'Windows':
        topPath = 'm:/SharedFiles'
    else:
        print('Platform of', thisPlatform, 'not handled')
        topPath = ''

    if pathOption == 0:
        filePath = topPath + '/' + 'Other_LoopReportFiles'
    elif pathOption == 1:
        filePath = topPath + '/' + 'LoopReportFiles'
    elif type(pathOption) == str:
        filePath = topPath + '/' + 'LoopReportFiles' + '/' + pathOption
    else:
        print(' pathOption not recognized for getAnalysisIO')
        filePath = ''

    if vFlag == 0:
        outFlag = 0
    elif vFlag == 1:
        outFlag = 0
    elif vFlag == 2:
        outFlag = 0
    elif vFlag == 3:
        outFlag = topPath + '/' + 'LoopReportPythonAnalysis' + '/' \
                  + 'init_survey.csv'
    elif vFlag == 4:
        outFlag = topPath + '/' + 'LoopReportPythonAnalysis' + '/' \
                  + 'verboseOutput' + '/'
    else:
        print('  vFlag not recognized for getAnalysisIO')
        outFlag = 0

    return filePath, outFlag
