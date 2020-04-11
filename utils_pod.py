# utils_pod - lower level functions related to omnipod

def getPodProgressMeaning(thisInt):
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

    Ordering: with the exception of commands that are only used during
            initialization, put the sequences of 4 messages first so that
            getPodState pulls those out of the frame of sequential frames
            first.  Then the sequences of 2 commands are identified next
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
    This is the list of messages that should be sequential for a successful "action"
        getPodInitDict {
            seq# : ('initStepName', message_type, ppRange), \
            ... \
            }
    The expected pod_progress (pp) for the 01 after 0x7 can be 1 or 2,
    so had to set up as a range
    """
    podInitDict = { \
            0           : ( 'assignID', '0x7',  [0]), \
            1           : ( 'successID', '0115',  [1, 2]), \
            2           : ( 'setupPod', '0x3',  [1, 2]), \
            3           : ( 'successSetup', '011b',  [3]), \
            4           : ( 'cnfgDelivFlags', '0x8',  [3]), \
            5           : ( 'successDF', '1d',  [3]), \
            6           : ( 'cnfgAlerts1', '0x19',  [3]), \
            7           : ( 'successCA1', '1d',  [3]), \
            8           : ( 'prime', '1a17',  [3]), \
            9           : ( 'successPrime', '1d',  [4]), \
            10          : ( 'programBasal', '1a13', [4]), \
            11          : ( 'successBasal', '1d',  [6]), \
            12          : ( 'cnfgAlerts2', '0x19',  [6]), \
            13          : ( 'successCA2', '1d',  [6]), \
            14          : ( 'insertCanu', '1a17',  [6]), \
            15          : ( 'successIns', '1d',  [7]), \
            16          : ( 'statusCheck', '0e',  [7]), \
            17          : ( 'initSuccess', '1d',  [8])
            }

    return podInitDict

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
    # if captured initialization steps, update podInfo and  get podInitFrame
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
