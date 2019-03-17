import pandas as pd
import time

# new function (2/27/2019)
def time_difference(df_column):
    time_difference = (df_column - df_column.shift()).dt.seconds.fillna(0).astype(int)
    return time_difference

# new function (2/27/2019)
def to_time(df_time_column):
    return time.strftime("%H:%M:%S",time.gmtime(df_time_column))

# new function (MDB) (3/15/2019) - updated to recursive version to handle single items (not lists) up
# through multi-layered lists (lol = list of lists)
def flatten(lol):
    if type(lol) is list:
        if len(lol) == 1:
            return flatten(lol[0])
        else:
            return flatten(lol[0]) + flatten(lol[1:])
    else:
        return [lol]

# return a new DataFrame of just the selected indices in the original DataFrame
# maintain the original index as a new column in the returned DataFrame
def createSubsetDataFrame (frame, indexList):
    # add original index to the frame as a new column
    frame['original_index'] = frame.index.array
    # extract column list
    newCol = frame.columns
    subFrame = frame.iloc[indexList]
    newData = subFrame.values
    newFrame = pd.DataFrame(newData, columns = newCol)
    return newFrame

def printDict(thisDict):
    for keys,values in thisDict.items():
        print('  {} =   {}'.format(keys, values))

def printList(thisList):
    for item in thisList:
        print(item)

def listFromDict(thisDict):
    list_of_keys = []
    for keys, values in thisDict.items():
        list_of_keys.append(keys)
    return list_of_keys

def getPodProgessMeaning(thisInt):
    """ convert the value for pod progess into it's meaning """
    podProgress = { \
        0: 'Initial value', \
        1: 'Tank power activated', \
        2: 'Tank fill completed', \
        3: 'Pairing success', \
        4: 'Purging', \
        5: 'Ready for injection', \
        6: 'Injection done', \
        7: 'Priming cannula', \
        8: 'Running with > 50U in reservoir', \
        9: 'Running with <= 50U in reservoir', \
        10: '10 Not used (except for possible debug use)', \
        11: '11 Not used (except for possible debug use)', \
        12: '12 Not used (except for possible debug use)', \
        13: 'Fault event occurred, shutting down', \
        14: 'Failed to initialize in time, shutting down', \
        15: 'Pod inactive'}

    return podProgress[thisInt]

def getUnitsFromPulses(pulses):
    # given number of pulses convert to units of insulin
    #i = Decimal(0.05 * pulses)
    insulin = round(0.05 * pulses,2)
    return insulin
