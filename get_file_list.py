import os
from os import listdir

def get_file_list(thisPath):
    """
    Returns a filenames with associated creation times in a list

    PARAMS:
        thisPath: path folder where the MessageLog files by person are stored

    RETURNS:
        returnList list of filename(relative to thisPath), creation time for file
                where returnList is sorted by creation time
    """
    list_of_reports = []
    list_of_dates = []

    for x in listdir(thisPath):
        if x == '.DS_Store':
            continue
        #print(x)
        for y in listdir(thisPath + '/' + x):
            if y == '.DS_Store':
                continue
            thisFile = x + '/' + y
            list_of_reports.append(thisFile)
            list_of_dates.append(os.path.getmtime(thisPath + '/' + thisFile))

    zippedTuple = zip(list_of_reports, list_of_dates)
    zippedList = list(zippedTuple)
    returnList = sorted(zippedList, key = lambda x: x[1])

    # return the list of files and dates sorted by date
    return returnList
