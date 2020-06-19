# Determine the location (Mac or PC)
import os
import platform

def getAnalysisIO(pathOption, outputOption):
    # return the appropriate folder address depending on OS and pathOption
    #    When doing "real" analysis, use (1,1)
    #
    #    pathOption == 0 use folder for partial / special purpose / older LoopReportFiles
    #                  1 use folder with complete Loop Reports
    #                  2 specify a specific users' folder by their name
    #
    #    outputOption == 0 return 0 for output file (.csv)
    #                    1 return name for output_master_rev4.csv (post public release)
    #                    2 return name for test.csv
    #                    3 return name for init_master.csv
    #                    4 return prefix for verbose output for podInit and podState
    #                    5 return prefix for verbose output for log with pairing problems

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

    if outputOption == 0:
        outFile = 0
    elif outputOption == 1:
        outFile = topPath + '/' + 'LoopReportPythonAnalysis' + '/' + 'output_survey.csv'
    elif outputOption == 2:
        outFile = 0
    elif outputOption == 3:
        outFile = topPath + '/' + 'LoopReportPythonAnalysis' + '/' + 'init_survey.csv'
    elif outputOption == 4:
        outFile = topPath + '/' + 'LoopReportPythonAnalysis' + '/' + 'verboseOutput' + '/'
    elif outputOption == 5:
        outFile = topPath + '/' + 'LoopReportPythonAnalysis' + '/' + 'verboseOutputPairing' + '/'
    else:
        print('  outputOption not recognized for getAnalysisIO')
        outFile = 0

    return filePath, outFile
