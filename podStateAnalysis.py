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

# iterate through all messages and apply parsers to update the pod state
# The initial negotiations are not parsed
# Typically called once for pod_progress 0 through 7
# Then called again for pod_progress 8 through 15
def getPodState(frame, minPodProgress, maxPodProgress):
    """
    Purpose: Evaluate state changes while the pod_progress is in range

    Input:
        frame: DataFrame with all messages
        minPodProgress: ignore any pod_progress < minPodProgress
        maxPodProgress: once the pod_progress reaches this value, return

    Output:
       podStateFrame    dataframe with pod state extracted from messages
       emptyMessageList indices of any messages with blank commands

    """
    # initialize values for pod states that we will update
    timeStamp = frame.iloc[0]['time']
    pod_progress = 0
    total_insulin = getUnitsFromPulses(0)
    lastTB = getUnitsFromPulses(0)
    lastBolus = getUnitsFromPulses(0)
    #extBo = False # since extended bolus is always false, don't put into dataframe
    Bolus = False
    TB    = False
    schBa = False
    emptyMessageList = []

    list_of_states = []

    colNames = ('df_idx', 'timeStamp', 'timeDelta', 'message_type', 'pod_progress', 'total_insulin', 'lastTB', 'lastBolus', 'Bolus','TB','SchBasal', 'raw_value' )

    # iterate through the DataFrame, should already be sorted into send-recv pairs
    for index, row in frame.iterrows():
        # reset each time
        timeStamp = row['time']
        timeDelta = row['timeDelta']
        msg = row['raw_value']
        if msg == '':
            #print('Empty command for {} at dataframe index of {:d}'.format(row['type'], index))
            pmsg = {}
            pmsg['message_type'] = 'unknown'
            emptyMessageList.append(index)
            continue
        else:
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

        # check pod_progress
        if pod_progress < minPodProgress:
            continue
        elif pod_progress >= maxPodProgress:
            break

        list_of_states.append((index, timeStamp, timeDelta, message_type, pod_progress, total_insulin, lastTB, lastBolus, Bolus, TB, schBa, msg))

    podStateFrame = pd.DataFrame(list_of_states, columns=colNames)
    return podStateFrame, emptyMessageList

def getPodSuccessfulActions(podStateFrame):
    """
    Purpose: Evaluate each request for Basal, TB or Bolus ['1a13', '1a16', '1a17']

    Input:
        podStateFrame: Should be the pod running frames (pod_progress>=8)

    Output:
        podRequestSuccess  dataframe with successful responses to requests
        podOtherMessages   all other messages
    """
    list_of_success = []  # success for items in list_of_requests
    list_of_other   = []  # all other or unpaired messages
    nextIndex = -1;
    thisIndex = 0;
    list_of_requests = ['1a13', '1a16', '1a17']

    successColumnNames = ('start_df_idx', 'start_podState_idx', 'end_podState_idx', \
      'startTimeStamp', 'startMessage', 'endMessage', 'responseTime', 'total_insulin', \
      'lastTB', 'lastBolus', 'Bolus','TB','SchBasal' )
    otherColumnNames = ('start_df_idx', 'start_podState_idx', 'startTimeStamp', 'startMessage' )

    # iterate looking for requests and successful responses
    for index, row in podStateFrame.iterrows():
        if index <= nextIndex:
            continue
        # set up params we need for either case
        start_df_idx   = row['df_idx']
        startTimeStamp = row['timeStamp']
        startMessage   = row['message_type']
        # if not in list_of_requests, put it in other
        if row['message_type'] not in list_of_requests:
            list_of_other.append((start_df_idx, index, startTimeStamp, startMessage))
        # was in list_of_requests, look for successful return message
        # look for desired response, then once it's determined which this is, append to appropriate list
        else:
            # set the success criteria
            if startMessage == '1a16':
                colName = 'TB'
                colValue = True
                respMessage = '1d'

            elif startMessage == '1a17':
                colName = 'Bolus'
                colValue = True
                respMessage = '1d'

            elif startMessage == '1a13':
                colName = False
                colValue = True
                respMessage = '1d'

            nextIndex = index + 1
            didSucceed = False

            newRow = podStateFrame.iloc[nextIndex]
            timeToResponse = newRow['timeDelta']
            if  newRow['message_type'] == respMessage:
                if colName and newRow[colName]==colValue:
                    didSucceed = True
                if not colName:
                    didSucceed = True

            if didSucceed:
                list_of_success.append((start_df_idx, index, nextIndex, startTimeStamp, \
                  startMessage, respMessage, timeToResponse, newRow['total_insulin'], newRow['lastTB'], \
                  newRow['lastBolus'], newRow['Bolus'], newRow['TB'], newRow['SchBasal']))
            else:
                list_of_other.append((start_df_idx, index, startTimeStamp, startMessage))
                nextIndex = index

    podRequestSuccess = pd.DataFrame(list_of_success, columns=successColumnNames)
    podOtherMessages = pd.DataFrame(list_of_other, columns=otherColumnNames)

    return podRequestSuccess, podOtherMessages
