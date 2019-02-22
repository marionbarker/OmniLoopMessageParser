import os
from os import listdir

def get_file_list(thisPath):
    """
    Returns a list of folders and their associated *.md files in a list

    PARAMS:
        path folder where the MessageLog files by person are stored

    RETURNS:
        list_of_files including subfolders
    """
    list_of_reports = []
    list_of_dates = []

    for x in listdir(thisPath):
        #print(x)
        for y in listdir(thisPath + '/' + x):
            thisFile = x + '/' + y
            list_of_reports.append(thisFile)
            list_of_dates.append(os.path.getmtime(thisPath + '/' + thisFile))

    return (list_of_reports, list_of_dates)
