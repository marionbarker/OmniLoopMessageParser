from utils import *
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
    timeStamp = frame.iloc[0]['time']
    pod_progress = 0
    total_insulin = getUnitsFromPulses(0)
    message_type = 'unknown'
    lastTB = getUnitsFromPulses(0)
    lastBolus = getUnitsFromPulses(0)
    #extBo = False # since extended bolus is always false, don't put into dataframe
    Bolus = False
    TB    = False
    schBa = False
    # add a time_delta column
    frame['timeDelta'] = (frame['time']-frame['time'].shift()).dt.seconds.fillna(0).astype(float)


    list_of_states = []

    colNames = ('original_index', 'timeStamp', 'timeDelta', 'pod_progress', 'total_insulin', 'message_type', 'lastTB', 'lastBolus', 'bolus','TB','SchBasal', 'raw_value' )

    # iterate through the DataFrame, should already be sorted into send-recv pairs
    for index, row in frame.iterrows():
        #print(index, row['raw_value'])
        # reset each time
        original_index = row['original_index']
        timeStamp = row['time']
        timeDelta = row['timeDelta']
        msg = row['raw_value']
        pmsg = processMsg(msg)
        message_type = pmsg['message_type']

        # fill in pod state based on message_type
        if message_type == '1a16':
            lastTB = pmsg['temp_basal_rate_u_per_hr']

        elif message_type == '1a17':
            lastBolus = pmsg['prompt_bolus_u']

        elif message_type == '1d':
            pod_progress = pmsg['pod_progress']
            total_insulin = pmsg['total_insulin_delivered']
            Bolus = pmsg['immediate_bolus_active']
            TB    = pmsg['temp_basal_active']
            schBa = pmsg['basal_active']

        elif message_type == '1f':
            Bolus = Bolus and not pmsg['cancelBolus']
            TB    = TB and not pmsg['cancelTB']
            schBa = schBa and not pmsg['suspend']

        list_of_states.append((original_index, timeStamp, timeDelta, pod_progress, total_insulin, message_type, lastTB, lastBolus, Bolus, TB, schBa, msg))

    podState = pd.DataFrame(list_of_states, columns=colNames)
    return podState, list_of_states
