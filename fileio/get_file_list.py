import re
import os
from os import listdir


def get_file_list(folderPath):
    """
    Returns a filenames with associated creation times in a list

    PARAMS:
        folderPath: path folder where the files by person are stored
                  if folder contains Loop Reports, then just return that list

    RETURNS:
        returnList list of filename(relative to folderPath),
                   creation time for file
                   returnList is sorted by creation time
    """
    list_of_reports = []
    list_of_dates = []

    thisLevel = listdir(folderPath)

    if thisLevel[0][0:4] == 'Loop':
        for y in thisLevel:
            if y == '.DS_Store':
                continue
            personFile = y
            list_of_reports.append(personFile)
            list_of_dates.append(os.path.getmtime(folderPath +
                                                  '/' + personFile))

    else:
        for x in thisLevel:
            if x == '.DS_Store':
                continue
            # print(x)
            for y in listdir(folderPath + '/' + x):
                if y == '.DS_Store':
                    continue
                personFile = x + '/' + y
                list_of_reports.append(personFile)
                list_of_dates.append(os.path.getmtime(folderPath +
                                                      '/' + personFile))

    zippedTuple = zip(list_of_reports, list_of_dates)
    zippedList = list(zippedTuple)
    returnList = sorted(zippedList, key=lambda x: x[1])

    # return the list of files and dates sorted by date
    # note - can touch a file to make it most recent to rerun
    # date of data in file internal to the file
    return returnList


def getFileDict(folderPath, personFile, loopType):
    thisDate = "unknown"
    fileDict = {'filename': folderPath + '/' + personFile,
                'path': folderPath,
                'personFile': personFile,
                'loopType': loopType,
                'recordType': "unknown",
                'date': thisDate}
    # parse the person and date from in personFile
    #   For loopType = "Loop", get date from person/LoopReport_date.md)
    #   For loopType = "FX", the first 8 characters in the file are the date.
    # The recordType and date may be updated in parsers/loop_read_file
    val = '^.*/'
    thisPerson = re.findall(val, personFile)
    if not thisPerson:
        thisPerson = 'Unknown'
    else:
        thisPerson = thisPerson[0][0:-1]

    fileDict['person'] = thisPerson

    if loopType.lower() == "loop":
        val = '/.*$'
        thisFullName = re.findall(val, personFile)
        thisFullName = thisFullName[0]
        thisFullName = thisFullName[1:]
        thisFullName = thisFullName.replace(' ', '')  # remove spaces
        thisFullName = thisFullName.replace('-', '')  # remove hypens
        thisFullName = thisFullName.replace('_', '')  # remove underscores
        # trim off some characters
        thisDate = thisFullName[10:18] + '_' + thisFullName[18:22]
        fileDict['date'] = thisDate

    elif loopType.lower() == "fx":
        fileDict['date'] = "WillReadFromFileAndUpdate"

    else:
        print("loopType is not recognized: ", loopType)

    return fileDict
