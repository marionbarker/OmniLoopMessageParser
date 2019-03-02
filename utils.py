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
