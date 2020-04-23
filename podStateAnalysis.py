from utils import *
from utils_pd import *
from utils_pod import *
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
       ackMessageList    indices of any blank messages (ACK)
       faultProcessedMsg   dictionary for the fault message
       podInfo             dictionary for pod

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
    ackMessageList = []
    radio_on_time = 30 # radio is on for 30 seconds every time pod wakes up
    radioOnCumSec = radio_on_time
    podInfo = {}

    list_of_states = []

    colNames = ('df_idx', 'timeStamp', 'time_delta', 'timeCumSec', \
                'radioOnCumSec', 'seq_num', 'pod_progress', 'msg_type', \
                'msgMeaning', 'insulinDelivered', 'reqTB', \
                'reqBolus', 'Bolus','TB','SchBasal', 'address', 'msg_body' )

    # iterate through the DataFrame, should already be sorted into send-recv pairs
    for index, row in frame.iterrows():
        # reset each time
        timeStamp = row['time']
        time_delta = row['time_delta']
        timeCumSec += time_delta
        msg = row['msg_body']
        # prevent excel from treating 1e as exponent
        msgForPodState = 'hex {:s}'.format(msg)
        seq_num = row['seq_num']
        pmsg = processMsg(msg)
        msgMeaning  = pmsg['msgMeaning']
        if pmsg['msg_type'] == 'ACK':
            ackMessageList.append(index)

        msg_type = pmsg['msg_type']
        if msg_type == '0x02':
            faultProcessedMsg = pmsg

        timeAsleep = row['time_asleep']
        if np.isnan(timeAsleep):
            radioOnCumSec += time_delta
        else:
            radioOnCumSec += time_delta - timeAsleep

        # fill in pod state based on msg_type
        if msg_type == '0x1a16':
            reqTB = pmsg['temp_basal_rate_u_per_hr']

        elif msg_type == '0x1a17':
            reqBolus = pmsg['prompt_bolus_u']

        elif msg_type == '0x1d':
            pod_progress = pmsg['pod_progress']
            insulinDelivered = pmsg['insulinDelivered_delivered']
            Bolus = pmsg['immediate_bolus_active']
            TB    = pmsg['temp_basal_active']
            schBa = pmsg['basal_active']

        elif msg_type == '0x0115':
            pod_progress = pmsg['pod_progress']
            podInfo['piVersion'] = pmsg['piVersion']
            podInfo['lot']  = str(pmsg['lot'])
            podInfo['tid']  = str(pmsg['tid'])
            podInfo['address']  = pmsg['address']
            podInfo['recv_gain']  = pmsg['recv_gain']
            podInfo['rssi_value']  = pmsg['rssi_value']

        elif msg_type == '0x011b':
            pod_progress = pmsg['pod_progress']
            podInfo['piVersion'] = pmsg['piVersion']
            podInfo['lot']  = str(pmsg['lot'])
            podInfo['tid']  = str(pmsg['tid'])
            podInfo['address']  = pmsg['address']

        list_of_states.append((index, timeStamp, time_delta, timeCumSec, \
                              radioOnCumSec, seq_num, pod_progress, msg_type, \
                              msgMeaning, insulinDelivered, reqTB, \
                              reqBolus, Bolus, TB, schBa, row['address'], msgForPodState))

    podStateFrame = pd.DataFrame(list_of_states, columns=colNames)
    return podStateFrame, ackMessageList, faultProcessedMsg, podInfo
