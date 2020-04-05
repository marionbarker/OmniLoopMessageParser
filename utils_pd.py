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
    podAddress = list(podFrame['address'].unique())
    if 'noPod' in podAddress:
        podAddress.remove('noPod')
    frameLength = len(podFrame)
    # initialize firstRow as an empty list
    firstRow = []

    for val in podAddress:
        mask = podFrame['address'] == val
        idx = next(iter(mask.index[mask]), False)
        firstRow.append(idx)

    # set up default breakPoint array (full podFrame)
    breakPoints = [0, frameLength]

    # if 'noPod' split points exist, return them
    if len(firstRow) > 1:
        # use lastRow to accumlate row indices
        lastRow = [frameLength]
        idx = 0
        for val in firstRow:
            lastRow.insert(idx, val-2)
            idx = idx+1

        # replace the first value with 0 instead of -2
        lastRow[0] = 0

        breakPoints = lastRow

    # check for special (and most important case), where podFrame ends in 'noPod'
    oldLast = breakPoints[-1]
    if podFrame.iloc[breakPoints[-1]-1]['address'] == 'noPod':
        thisIdx = breakPoints[-1]
        while thisIdx > breakPoints[-2]:
            if podFrame.iloc[thisIdx-1]['address'] != 'noPod':
                break
            thisIdx = thisIdx-1
        breakPoints[-1] = thisIdx
        breakPoints.append(oldLast)

    # all done, return list
    return podAddress, breakPoints
