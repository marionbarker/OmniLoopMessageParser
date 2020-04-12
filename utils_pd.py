import pandas as pd
import time

# combine useful repeated actions to do with pandas data frame

# new function (2/27/2019)
def time_difference(df_column):
    time_difference = (df_column - df_column.shift()).dt.seconds.fillna(0).astype(int)
    return time_difference

# new function (2/27/2019)
def to_time(df_time_column):
    return time.strftime("%H:%M:%S",time.gmtime(df_time_column))

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

"""
  Find the index array for splitting the podFrame by address using 'noPod'
  as the break point
"""
def findBreakPoints(podFrame):
    # get list of addresses
    addressList = podFrame['address'].to_list()

    # iterate to find breakPoints
    frameLength = len(addressList)
    breakPoints = [0]
    idx = 0
    noPodAddress = 'ffffffff'
    thisAddress = addressList[idx]
    for val in addressList:
        if (thisAddress != val) and (thisAddress != noPodAddress):
            breakPoints.append(idx)
        thisAddress = val
        idx = idx+1

    # special cases where final msg is noPodAddress
    if breakPoints[-1] != frameLength:
        breakPoints.append(frameLength)

    # get a list of the unique pod addresses in frame
    podAddresses = list(podFrame['address'].unique())
    if noPodAddress in podAddresses:
        podAddresses.remove(noPodAddress)

    # all done, return list
    return podAddresses, breakPoints
