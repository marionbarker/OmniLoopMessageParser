import pandas as pd
import time

# new function (2/27/2019)
def time_difference(df_column):
    time_difference = (df_column - df_column.shift()).dt.seconds.fillna(0).astype(int)
    return time_difference

# new function (2/27/2019)
def to_time(df_time_column):
    return time.strftime("%H:%M:%S",time.gmtime(df_time_column))

# new function (MDB) (3/1/2019)
def flatten(list_of_lists):
    flat_list = [item for sublist in list_of_lists for item in sublist]
    return flat_list

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
