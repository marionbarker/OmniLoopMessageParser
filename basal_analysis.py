from utils import *
import numpy as np
from messagePatternParsing import *

def basal_analysis(df):
  # add analysis per Eelke (2/27 and 3/2/2019 )

  # Add time between TBs
  df['time_diff_tbs'] = time_difference(df.loc[df['command']=='1a16']['time'])

  # Add time column a normal basal was running before this TB
  df["normal_basal_running_seconds"] = df.loc[df['time_diff_tbs'] > 30 * 60]['time_diff_tbs'] - (30 * 60)
  df_basals = df[df["normal_basal_running_seconds"].notnull()]

  # Normal basals running
  df_basals["normal_basal_running_time"]= df_basals["normal_basal_running_seconds"].astype(int).apply(to_time)
  # Previous 2 values of first TB send after >30 minutes
  df2 = df.loc[(df.normal_basal_running_seconds < 30),["time","command","normal_basal_running_seconds", "raw_value"]]
  df2 = df2.append(df[df.normal_basal_running_seconds.shift(-3) < 30].loc[:,["time","command","normal_basal_running_seconds", "raw_value"]])
  df2 = df2.append(df[df.normal_basal_running_seconds.shift(-2) < 30].loc[:,["time","command","normal_basal_running_seconds", "raw_value"]])
  df2 = df2.append(df[df.normal_basal_running_seconds.shift(-1).notnull()].loc[:,["time","command","normal_basal_running_seconds", "raw_value"]])

  return df_basals, df2

# generate a list of times for when bits are modified for the following states
#   may be slow and stupid, but I can understand it when I iterate through
def podStateAnalysis(frame):
    """
    Purpose: Evaluate state changes

    Input:
        frame: DataFrame with just send-recv pairs

    Output:
       not sure yet - designing as I'm coding
       usage:
       sentList, recvList, updatedFrame = podStateAnalysis(seqDF)

    """
    # set up tuple with
    #   time, lastTB, lastBolus, ext_bolus_active, bolus_active, TB_active, basal_active
    #   with Loop               always False      False/True    only one of these can be true
    # initialize current TB rate to nan and time
    thisIdx = 0
    original_index = np.nan
    timeLastEvent = frame.iloc[0]['time']
    lastTB = np.nan
    lastBolus = np.nan
    extBo = False
    Bolus = False
    TB    = False
    schBa = True

    list_of_states = []

    colNames = ('seqDF_idx', 'df_idx', 'timeStamp', 'TB_u_per_hr', 'Bolus_u', 'extendedBolus','bolus','TB','SchBasal' )

    # iterate through the DataFrame, should already be sorted into send-recv pairs
    for index, row in frame.iterrows():
        # reset each time
        stateChanged = False
        #print(index, row['type'], row['command'])

        # first check if this is a send and if it is a 0x1a16
        # if so, get current TB value
        if row['type'] == 'send' and row['command'] == '1a16':
            pmsg = processMsg(row['raw_value'])
            thisIdx = index
            original_index = row['original_index']
            timeLastEvent = row['time']
            lastTB = pmsg['temp_basal_rate_u_per_hr']
            currentBolus = np.nan
            extBo = False
            Bolus = False
            TB    = True
            schBa = False
            stateChanged = True

        if stateChanged:
            list_of_states.append((thisIdx, original_index, timeLastEvent, lastTB, lastBolus, extBo, Bolus, TB, schBa))

    podState = pd.DataFrame(list_of_states, columns=colNames)
    return podState, list_of_states
