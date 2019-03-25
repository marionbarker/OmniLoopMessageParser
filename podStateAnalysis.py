from utils import *
from podUtils import *
from messagePatternParsing import *

## This file has higher level pod-specific functions

# iterate through all messages and apply parsers to update the pod state
# some messages are not parsed (they show up as 0x##)
def getPodState(frame):
    """
    Purpose: Evaluate state changes while the pod_progress is in range

    Input:
        frame: DataFrame with all messages

    Output:
       podStateFrame       dataframe with pod state extracted from messages
       emptyMessageList    indices of any messages with blank commands
       faultProcessedMsg   dictionary for the fault message

    """
    # initialize values for pod states that we will update
    timeCumSec = 0
    pod_progress = 0
    faultProcessedMsg = {}
    insulinDelivered = getUnitsFromPulses(0)
    reqTB = getUnitsFromPulses(0)
    reqBolus = getUnitsFromPulses(0)
    #extBo = False # since extended bolus is always false, don't put into dataframe
    Bolus = False
    TB    = False
    schBa = False
    emptyMessageList = []
    sendDict, recvDict = getMessageDict()
    list_of_recv = listFromDict(recvDict)
    radio_on_time = 30 # radio is on for 30 seconds every time pod wakes up
    radioOnCumSec = radio_on_time

    list_of_states = []

    colNames = ('df_idx', 'timeStamp', 'time_delta', 'timeCumSec', \
                'message_type', 'pod_progress', 'radioOnCumSec',\
                'insulinDelivered', 'reqTB', \
                'reqBolus', 'Bolus','TB','SchBasal', 'raw_value' )

    # iterate through the DataFrame, should already be sorted into send-recv pairs
    for index, row in frame.iterrows():
        # reset each time
        timeStamp = row['time']
        time_delta = row['time_delta']
        timeCumSec += time_delta
        msg = row['raw_value']
        if msg == '':
            #print('Empty command for {} at dataframe index of {:d}'.format(row['type'], index))
            pmsg = {}
            pmsg['message_type'] = 'unknown'
            emptyMessageList.append(index)
            #continue
        else:
            pmsg = processMsg(msg)

        message_type = pmsg['message_type']
        if message_type == '02':
            faultProcessedMsg = pmsg

        timeAsleep = row['time_asleep']
        if np.isnan(timeAsleep):
            radioOnCumSec += time_delta
        else:
            radioOnCumSec += time_delta - timeAsleep

        # fill in pod state based on message_type
        if message_type == '1a16':
            reqTB = pmsg['temp_basal_rate_u_per_hr']

        elif message_type == '1a17':
            reqBolus = pmsg['prompt_bolus_u']

        elif message_type == '1d':
            pod_progress = pmsg['pod_progress']
            insulinDelivered = pmsg['insulinDelivered_delivered']
            Bolus = pmsg['immediate_bolus_active']
            TB    = pmsg['temp_basal_active']
            schBa = pmsg['basal_active']

        elif message_type == '1f':
            #Bolus = Bolus and not pmsg['cancelBolus']
            #TB    = TB and not pmsg['cancelTB']
            #schBa = schBa and not pmsg['suspend']
            # rename the message_type per Joe's request
            message_type = '1f0{:d}'.format(pmsg['cancelByte'])

        list_of_states.append((index, timeStamp, time_delta, timeCumSec, \
                              message_type, pod_progress, radioOnCumSec, \
                              insulinDelivered, reqTB, \
                              reqBolus, Bolus, TB, schBa, msg))

    podStateFrame = pd.DataFrame(list_of_states, columns=colNames)
    return podStateFrame, emptyMessageList, faultProcessedMsg
