import os
from os import listdir


def get_file_list(thisPath):
    """
    Returns a filenames with associated creation times in a list

    PARAMS:
        thisPath: path folder where the files by person are stored
                  if folder contains Loop Reports, then just return that list

    RETURNS:
        returnList list of filename(relative to thisPath),
                   creation time for file
                   returnList is sorted by creation time
    """
    list_of_reports = []
    list_of_dates = []

    thisLevel = listdir(thisPath)

    if thisLevel[0][0:4] == 'Loop':
        for y in thisLevel:
            if y == '.DS_Store':
                continue
            thisFile = y
            list_of_reports.append(thisFile)
            list_of_dates.append(os.path.getmtime(thisPath + '/' + thisFile))

    else:
        for x in thisLevel:
            if x == '.DS_Store':
                continue
            # print(x)
            for y in listdir(thisPath + '/' + x):
                if y == '.DS_Store':
                    continue
                thisFile = x + '/' + y
                list_of_reports.append(thisFile)
                list_of_dates.append(os.path.getmtime(thisPath +
                                                      '/' + thisFile))

    zippedTuple = zip(list_of_reports, list_of_dates)
    zippedList = list(zippedTuple)
    returnList = sorted(zippedList, key=lambda x: x[1])

    # return the list of files and dates sorted by date
    return returnList
