# utils_pod - lower level functions related to omnipod

# and the nomenclature for pod_progress here:
#	https://github.com/openaps/openomni/wiki/Pod-Progress-State

def getPodProgressMeaning(thisInt):
    """ convert the value for pod progess into it's meaning """
    podProgress = { \
        0: '', \
        1: 'MemoryInitialized', \
        2: 'ReminderInitialized', \
        3: 'PairingCompleted', \
        4: 'Priming', \
        5: 'PrimingCompleted', \
        6: 'BasalInitialized', \
        7: 'InsertingCannula', \
        8: 'Running > 50U', \
        9: 'Running <= 50U', \
        10: '10 NotUsed', \
        11: '11 NotUsed', \
        12: '12 NotUsed', \
        13: 'FaultEvent', \
        14: 'ActivationTimeExceeded', \
        15: 'PodInactive'}

    return podProgress[thisInt]

def getUnitsFromPulses(pulses):
    # given number of pulses convert to units of insulin
    #i = Decimal(0.05 * pulses)
    insulin = round(0.05 * pulses,2)
    return insulin

def getActionDict():
    """
    This defines the list of messages that should be sequential
    for a successful "action":
        actionDict {
           'actionName' : (idxToNameForSearch list ('sendName', 'recvName','sendName', 'recvName'), \
           'actionName' : (idxToNameForSearch list ('sendName', 'recvName') \
                 }
    These will be searched for in this order and those indices removed from
    pod frame before the next search (see getPodState in checkAction.py)

    Ordering: with the exception of messages that are only used during
            initialization, put the sequences of 4 messages first so that
            getPodState pulls those out of the frame of sequential frames
            first.  Then the sequences of 2 messages are identified next
    """
    actionDict = { \
      'AssignID'        : (0, ('0x7' , '0115')), \
      'SetupPod'        : (0, ('0x3' , '011b')), \
      'CnfgDelivFlg'    : (0, ('0x8' , '1d')), \
      'CnxSetTmpBasal'  : (2, ('1f02', '1d', '1a16', '1d')), \
      'Status&Bolus'    : (2, ('0e',   '1d', '1a17', '1d')), \
      'CnxAllSetBasal'  : (2, ('1f07', '1d', '1a13', '1d')), \
      'StatusCheck'     : (0, ('0e'  , '1d')), \
      'AcknwlAlerts'    : (0, ('0x11', '1d')), \
      'CnfgAlerts'      : (0, ('0x19', '1d')), \
      'SetBeeps'        : (0, ('0x1e', '1d')), \
      'CnxDelivery'     : (0, ('1f'  , '1d')), \
      'CnxBasal'        : (0, ('1f01', '1d')), \
      'CnxTmpBasal'      : (0, ('1f02', '1d')), \
      'CnxBolus'        : (0, ('1f04', '1d')), \
      'CnxAll'          : (0, ('1f07', '1d')), \
      'BolusAlone'      : (0, ('1a17', '1d')), \
      'DeactivatePod'   : (0, ('0x1c', '1d')), \
      'PrgBasalSch'     : (0, ('1a13', '1d'))
       }
    return actionDict


def getPodInitDict():
    """
    This is the list of messages that should be sequential for a
    successful pod initialization
        getPodInitDict {
            initIdx : ['initStepName', msg_type, ppRange], \
            ... \
            }
    The expected pod_progress can sometimes vary so is a list
    """
    podInitDict = { \
            0           : [ 'assignID', '0x7',  [0, 2]], \
            1           : [ 'successID', '0115',  [1, 2]], \
            2           : [ 'setupPod', '0x3',  [1, 2]], \
            3           : [ 'successSetup', '011b',  [3]], \
            4           : [ 'cnfgDelivFlags', '0x8',  [3]], \
            5           : [ 'successDF', '1d',  [3]], \
            6           : [ 'cnfgAlerts1', '0x19',  [3]], \
            7           : [ 'successCA1', '1d',  [3]], \
            8           : [ 'prime', '1a17',  [3]], \
            9           : [ 'successPrime', '1d',  [4]], \
            10          : [ 'programBasal', '1a13', [4]], \
            11          : [ 'successBasal', '1d',  [6]], \
            12          : [ 'cnfgAlerts2', '0x19',  [6]], \
            13          : [ 'successCA2', '1d',  [6]], \
            14          : [ 'insertCanu', '1a17',  [6]], \
            15          : [ 'successIns', '1d',  [7]], \
            16          : [ 'statusCheck', '0e',  [7]], \
            17          : [ 'initSuccess', '1d',  [8]]
            }

    return podInitDict

def getPodInitRestartDict(restartType):
    """
    Update the list of messages following a restart of pod init sequence
        sett getPodInitDict {
    """
    podInitRestartDict = getPodInitDict()
    if restartType == 0:
        podInitRestartDict[1] = [ 'ack', 'ACK',  [1, 2]]
        podInitRestartDict[3] = [ 'ack', 'ACK',  [3]]

    return podInitRestartDict

def returnPodID(podDict, podInfo):
    """
    Some files have the OmnipodManager information (podDict)
    Some files have the 0x011b message which has more details (podInfo)
    Determine what is available and return the information in podID
    """
    # configure defaults:
    podID = { \
        'lot': 'unknown', \
        'tid': 'unknown', \
        'piVersion': 'unknown', \
        'address': 'unknown'}
    hasPodInit = False
    # if captured initialization steps, update podInfo
    if podInfo.get('rssi_value'):
        hasPodInit = True
        podID['lot'] = podInfo['lot']
        podID['tid'] = podInfo['tid']
        podID['piVersion'] = podInfo['piVersion']
        podID['address'] = podInfo['address']
    # otherwise use podDict if OmnipodManager was found in file
    elif podDict.get('lot'):
        podID['lot'] = podDict['lot']
        podID['tid'] = podDict['tid']
        podID['piVersion'] = podDict['piVersion']
        podID['address'] = podDict['address']

    return podID, hasPodInit
