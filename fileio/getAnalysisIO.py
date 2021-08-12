# Determine the location (Mac or PC)
import os
import platform


def getAnalysisIO(pathOption, loopType, vFlag, macFlag):
    """
    return filePath, outFlag
       When doing "real" analysis, use (1, type, 4, 0) or (1, type, 4, 1)
       Add macFlag to handle Mac to use shared drive (Drobo) - default
       Update pathOption to handle Loop vs FreeAPS X log files

       pathOption:
          # now common for Loop or FAPSX files
          0 use folder for partial / special purpose / older Files (Loop only)
          1 use standard folder for loopType of file
          string for specific users' folder by name

       loopType:
          # identify if Loop or FAPSX files
          "Loop" for Loop Report markdown file
          "FX"   for FreeAPS X files

       vFlag:
         0: output analysis to terminal window, outFlag = 0
         1: deprecated, outFlag = 0
         2: output analysis to terminal window, outFlag = 0
         3: output podInitCmdCount to survey file, outFlag is filename
         4: (init, podState, full df) to csv, outFlag verboseOutput folder

       macFlag:
         0: use Drobo folder for Mac
         1: use local disk for Mac
    """

    thisPlatform = platform.system()

    if thisPlatform == 'Darwin':
        if macFlag == 1:  # use local hard drive (not typical, remind user)
            topPath = os.path.expanduser('~/dev/LoopReportRepository')
            print(' *** Top Path for Mac: ', topPath)
        else:
            topPath = os.path.expanduser('/Volumes/MarionPC/SharedFiles')
    elif thisPlatform == 'Windows':
        topPath = 'm:/SharedFiles'
    else:
        print('Platform of', thisPlatform, 'not handled')
        topPath = ''

    if pathOption == 0:
        filePath = topPath + '/' + 'Other_LoopReportFiles'
    elif pathOption == 1 and loopType.lower() == "loop":
        filePath = topPath + '/' + 'LoopReportFiles'
    elif pathOption == 1 and loopType.lower() == "fx":
        filePath = topPath + '/' + 'FAPSX_Files' + '/' + 'Input'
    elif type(pathOption) == str and loopType.lower() == "loop":
        filePath = topPath + '/' + 'LoopReportFiles' + '/' + pathOption
    elif type(pathOption) == str and loopType.lower() == "fx":
        filePath = topPath + '/' + 'FAPSX_Files' + '/' + 'Input' + \
                   '/' + pathOption
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
    elif vFlag == 4 and loopType.lower() == "loop":
        outFlag = topPath + '/' + 'LoopReportPythonAnalysis' + '/' \
                  + 'verboseOutput'
    elif vFlag == 4 and loopType.lower() == "fx":
        outFlag = topPath + '/' + 'FAPSX_Files' + '/' + 'Output'
    else:
        print('  vFlag not recognized for getAnalysisIO')
        outFlag = 0

    return filePath, outFlag
