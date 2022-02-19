"""
lower level functions related to omnipod
and the nomenclature for pod_progress here
website ref: https://github.com/openaps/openomni/wiki/Pod-Progress-State
"""


def getPodProgressMeaning(thisInt):
    """ convert the value for pod progess into it's meaning """
    podProgress = {
        0: '',
        1: 'MemoryInitialized',
        2: 'ReminderInitialized',
        3: 'PairingCompleted',
        4: 'Priming',
        5: 'PrimingCompleted',
        6: 'BasalInitialized',
        7: 'InsertingCannula',
        8: 'Running > 50U',
        9: 'Running <= 50U',
        10: '10 NotUsed',
        11: '11 NotUsed',
        12: '12 NotUsed',
        13: 'FaultEvent',
        14: 'ActivationTimeExceeded',
        15: 'PodInactive'}

    return podProgress[thisInt]


def getUnitsFromPulses(pulses):
    # given number of pulses convert to units of insulin
    # i = Decimal(0.05 * pulses)
    insulin = round(0.05 * pulses, 2)
    return insulin


def getActionDict():
    """
    This defines the list of messages that should be sequential
    for a successful "action":
        actionDict {
           'actionName' : (idxToNameForSearch list
                           ('sendName', 'recvName','sendName', 'recvName'),
           'actionName' : (idxToNameForSearch list ('sendName', 'recvName')
                 }
    These will be searched for in this order and those indices removed from
    pod frame before the next search
        (see getPodState in analysis.podStateAnalysis)

    Remove 'Status&Bolus'    : (2, ('0x0e',   '0x1d', '0x1a17', '0x1d')),
    in preparation of newer Loop code that no longer issues a status request
    prior to a bolus command

    Ordering: with the exception of messages that are only used during
            initialization, put the sequences of 4 messages first so that
            getPodState pulls those out of the frame of sequential frames
            first.  Then the sequences of 2 messages are identified next
    """

    actionDict = {
      'AssignID': (0, ('0x07', '0x0115')),
      'SetupPod': (0, ('0x03', '0x011b')),
      'CnfgDelivFlg': (0, ('0x08', '0x1d')),
      'CnxSetTmpBasal': (2, ('0x1f2', '0x1d', '0x1a16', '0x1d')),
      'Status&Bolus': (2, ('0x0e',   '0x1d', '0x1a17', '0x1d')),
      'CnxAllSetBasal': (2, ('0x1f7', '0x1d', '0x1a13', '0x1d')),
      'StatusCheck': (0, ('0x0e', '0x1d')),
      'AcknwlAlerts': (0, ('0x11', '0x1d')),
      'CnfgAlerts': (0, ('0x19', '0x1d')),
      'SetBeeps': (0, ('0x1e', '0x1d')),
      'CnxDelivery': (0, ('0x1f', '0x1d')),
      'CnxBasal': (0, ('0x1f1', '0x1d')),
      'CnxTmpBasal': (0, ('0x1f2', '0x1d')),
      'CnxBolus': (0, ('0x1f4', '0x1d')),
      'CnxAll': (0, ('0x1f7', '0x1d')),
      'BolusAlone': (0, ('0x1a17', '0x1d')),
      'TBAlone': (0, ('0x1a16', '0x1d')),
      'DeactivatePod': (0, ('0x1c', '0x1d')),
      'PrgBasalSch': (0, ('0x1a13', '0x1d'))
       }
    return actionDict


def getPodInitDict():
    """
    This is the list of messages that should be sequential for a
    successful pod initialization
        getPodInitDict {
            initIdx : ['initStepName', msgType, ppRange],
            ... \
            }
    The expected pod_progress can sometimes vary so is a list
    """
    podInitDict = {
            0: ['assignID', '0x07',  [0, 2]],
            1: ['successID', '0x0115',  [1, 2]],
            2: ['setupPod', '0x03',  [1, 2]],
            3: ['successSetup', '0x011b',  [3]],
            4: ['cnfgDelivFlags', '0x08',  [3]],
            5: ['successDF', '0x1d',  [3]],
            6: ['cnfgAlerts1', '0x19',  [3]],
            7: ['successCA1', '0x1d',  [3]],
            8: ['prime', '0x1a17',  [3]],
            9: ['successPrime', '0x1d',  [4]],
            10: ['programBasal', '0x1a13', [4]],
            11: ['successBasal', '0x1d',  [6]],
            12: ['cnfgAlerts2', '0x19',  [6]],
            13: ['successCA2', '0x1d',  [6]],
            14: ['insertCanu', '0x1a17',  [6]],
            15: ['successIns', '0x1d',  [7]],
            16: ['statusCheck', '0x0e',  [7]],
            17: ['initSuccess', '0x1d',  [8]]
            }

    return podInitDict


def getPodInitRestartDict(restartType):
    """
    Update the list of messages following a restart of pod init sequence
        sett getPodInitDict {
    """
    podInitRestartDict = getPodInitDict()
    # if restartType == 0:
    # podInitRestartDict[1] = ['ack', 'ACK',  [1, 2]]
    # podInitRestartDict[3] = ['ack', 'ACK',  [3]]

    return podInitRestartDict


def returnPodID(podDict, podInfo):
    """
    Some files have the OmnipodManager information (podDict)
    Some files have the 0x011b message which has more details (podInfo)
    Determine what is available and return the information in podID
    """
    # configure podID as an empty dictionary
    podID = {}
    # if captured initialization steps, use info in podInfo
    if podInfo.get('podType'):
        podID['podType'] = podInfo['podType']
        podID['lot'] = podInfo['lot']
        podID['tid'] = podInfo['tid']
        podID['piVersion'] = podInfo['piVersion']
        podID['pmVersion'] = podInfo['pmVersion']
        podID['address'] = podInfo['podAddr']
    # sometimes we do not capture that message
    else:
        podID = {
            'podType': 'unknown',
            'lot': 'unknown',
            'tid': 'unknown',
            'piVersion': 'unknown',
            'pmVersion': 'unknown',
            'address': podInfo['podAddr']}
    if podID['podType'] == 2:
        podID['podStyle'] = 'Eros'
    elif podID['podType'] == 4:
        podID['podStyle'] = 'Dash'
    else:
        podID['podStyle'] = 'Unkn'

    return podID


def getLogInfoFromState(podState):
    logInfoDict = {}
    # if first message is not 0x07, then not a complete record
    logInfoDict['logFileHasInit'] = podState.iloc[0]['msgType'] == '0x07'
    logInfoDict['first_msg'] = podState.iloc[0]['timeStamp']
    logInfoDict['last_msg'] = podState.iloc[-1]['timeStamp']
    logInfoDict['lastDate'] = logInfoDict['first_msg'].date()
    logInfoDict['send_receive_messages'] = podState.groupby(['type']).size()
    logInfoDict['msgLogHrs'] = podState.iloc[-1]['timeCumSec']/3600
    logInfoDict['radioOnHrs'] = podState.iloc[-1]['radioOnCumSec']/3600
    logInfoDict['numberOfAssignID'] = len(podState[podState.msgType == '0x07'])
    logInfoDict['numberOfSetUpPod'] = len(podState[podState.msgType == '0x03'])
    logInfoDict['numberOfNonceResync'] = \
        len(podState[podState.msgType == '0x0614'])
    logInfoDict['insulinDelivered'] = podState.iloc[-1]['insulinDelivered']
    logInfoDict['sourceString'] = 'from last 0x1d'
    logInfoDict['numMsgs'] = len(podState)
    logInfoDict['podOnTime'] = podState.iloc[-1]['podOnTime']
    # extract all 0x1a17 command (bolus)
    bolusState = podState[podState.msgType == '0x1a17']
    logInfoDict['totBolus'] = bolusState.sum()['reqBolus']
    # if autoBolus is present and any values are true, add that to logInfoDict
    """
    # todo - this is not robust
    if 'autoBolus' in podState.columns:
        bolusSum = bolusState.groupby('autoBolus').sum()['reqBolus']
        if len(bolusSum) > 0:
            logInfoDict['manB'] = bolusSum[0]
        if len(bolusSum) > 1:
            logInfoDict['autB'] = bolusSum[1]
    """

    return logInfoDict


def getDescriptiveStringFromPodStateRow(md, reqTB, reqBolus, pod_progress):
    # generate a descriptive string based on the msgDict.msgType
    dStr = ''
    # print(md)
    # print(reqTB, reqBolus)
    # organize by loop sent then pod sent
    loopPrefix = 'Loop Sent: '
    podPrefix = 'Pod  Sent: '
    '''
        Sent by loop to pod (group the initialization commands first
        and in expected order)
    '''
    if md['msgType'] == '0x07':
        dStr = loopPrefix + \
            'Assign address of {:s} to Pod'.format(md['useAddr'])
    elif md['msgType'] == '0x03':
        dStr = loopPrefix + 'Setup pod (address = {:s})'.format(md['podAddr'])
    elif md['msgType'] == '0x08':
        dStr = loopPrefix + 'Configure Delivery Flags, ' + \
            '(Values are {:d}, {:d})'.format(md['JJ(1)'], md['KK(0)'])
    elif md['msgType'] == '0x19':
        dStr = loopPrefix + 'Configure Alerts'
    elif md['msgType'] == '0x1a13':
        if pod_progress < 5:
            dStr = loopPrefix + 'Set Basal Schedule during initialization'
        else:
            dStr = loopPrefix + 'Modify Basal Schedule'
    elif md['msgType'] == '0x1a16':
        dStr = loopPrefix + 'Set Temp Basal Rate of {:.2f} u/hr'.format(
            md['temp_basal_rate_u_per_hr'])
    elif md['msgType'] == '0x1a17':
        if pod_progress < 5:
            dStr = loopPrefix + \
                'Prime of {:.2f} u'.format(md['prompt_bolus_u'])
        elif pod_progress < 8:
            dStr = loopPrefix + \
                'InsertCannula with {:.2f} u'.format(md['prompt_bolus_u'])
        elif 'autoBolus' in md and md['autoBolus']:
            dStr = loopPrefix + \
                'AutoBolus of {:.2f} u'.format(md['prompt_bolus_u'])
        else:
            dStr = loopPrefix + \
                'SetBolus of {:.2f} u'.format(md['prompt_bolus_u'])
    elif md['msgType'] == '0x0e':
        dStr = loopPrefix + '{:s}'.format(md['msgMeaning'])
    elif md['msgType'] == '0x11':
        dStr = loopPrefix + '0x11 message, {:s}'.format(md['msgMeaning'])
    elif md['msgType'] == '0x1c':
        dStr = loopPrefix + '{:s}'.format(md['msgMeaning'])
    elif md['msgType'] == '0x1e':
        dStr = loopPrefix + '0x1e message, request code {:s}'.format(
            md['msgMeaning'])
    elif md['msgType'][0:4] == '0x1f':
        dStr = loopPrefix + md['msgMeaning']

    # Sent by pod back to Loop
    elif md['msgType'] == '0x0115':
        dStr = podPrefix + 'Assign Address Accepted; gain {:d}, rssi {:d}, ' \
            'Lot {:d}, TID {:d}, PI: {:s}, pod address {:s}'.format(
                md['recvGain'], md['rssiValue'], md['lot'], md['tid'],
                md['piVersion'], md['podAddr'])
    elif md['msgType'] == '0x011b':
        dStr = podPrefix + \
            '{:s}; Lot {:d}, TID {:d}, PI: {:s}, pod address {:s}'.format(
                md['msgMeaning'], md['lot'], md['tid'], md['piVersion'],
                md['podAddr'])
    elif md['msgType'] == '0x1d':
        basalStr = ''
        bolusStr = ''
        if md['temp_basal_active']:
            basalStr = ' TmpBasal running, {:.2f} u/hr'.format(reqTB)
        elif md['basal_active']:
            basalStr = ' SchBasal running'
        else:
            basalStr = ' Basal suspended'
        if md['immediate_bolus_active']:
            bolusStr = '; Bolus accepted, {:.2f} u not yet delivered'.format(
                md['insulin_not_delivered'])
        elif md['insulin_not_delivered'] > 0:
            bolusStr = '; Bolus cancelled,  {:.2f} u not delivered'.format(
                md['insulin_not_delivered'])
        dStr = podPrefix + basalStr + bolusStr
    elif md['msgType'][0:4] == '0x02':
        dStr = podPrefix + md['msgMeaning']
    elif md['msgType'] == 'ACK':
        dStr = podPrefix + 'ACK (I heard you but I did not understand)'
    elif md['msgType'] == '0x0614':
        dStr = podPrefix + '{:s}, fault_code {:s}, reseed_word {:x} '.format(
            md['msgMeaning'], md['fault_code'], md['nonce_reseed_word'])

    return dStr


def getNameFromMsgType(msgType):
    """
    return english name for a given msgType
    """
    msgName = {
        'ACK': 'ACK',
        '0x0115': 'PodRespAssignID',
        '0x011b': 'PodRespSetup',
        '0x02': 'PodResp02Status',
        '0x0201': 'PodRespAlerts',
        '0x0202': 'PodRespErrStatus',
        '0x0203': 'PodRespPulses ',
        '0x0205': 'PodRespTimes',
        '0x0250': 'PodRespPulse0',
        '0x0251': 'PodRespPulse1',
        '0x03': 'SetupPod',
        '0x06': 'PodRespError',
        '0x0614': 'PodRespBadNonce',
        '0x07': 'AssignID',
        '0x08': 'CnfgDelivFlg',
        '0x0e': 'StatusRequest',
        '0x11': 'AcknwlAlerts',
        '0x19': 'CnfgAlerts',
        '0x1a13': 'PrgBasalSch',
        '0x1a16': 'TempBasal',
        '0x1a17': 'Bolus',
        '0x1c': 'DeactivatePod',
        '0x1d': 'PodRespStatus',
        '0x1e': 'SetBeeps',
        '0x1f0': 'CnxNone',
        '0x1f1': 'CnxBasal',
        '0x1f2': 'CnxTmpBasal',
        '0x1f4': 'CnxBolus',
        '0x1f6': '0x1f6-look-up',
        '0x1f7': 'CnxAll'}

    return msgName[msgType]


# if appropriate:
#   add the PDM-style Ref Code to the msgDict
def getFaultMsg(msgDict):
    faultProcessedMsg = msgDict
    faultProcessedMsg['pdmRefCode'] = ''
    thisFault = faultProcessedMsg['logged_fault']
    # The following "logged_fault" strings are not Faults,
    #    so no PDM RefCode needed
    notAFault = {'0x1c', '0x18', '0x00'}
    if thisFault in {'0x31'}:
        faultProcessedMsg['pdmRefCode'] = \
            'Programming Error - report to developers'
    elif thisFault not in notAFault:
        # generate PDM RefCode
        #    pdmRefCode = 'TT-VVVHH-IIIRR-FFF'
        # ref: https://github.com/openaps/openomni/wiki/PDM-Ref-Codes
        if thisFault in {'0x14'}:
            TT = '17'
        else:
            TT = '19'
        VVV = '{0:#0{1}d}'.format(msgDict['byte_V'], 3)
        # next few are the integer parts
        hours = msgDict['fault_time_minutes_since_pod_activation']//60
        HH = '{0:#0{1}d}'.format(hours, 2)
        insulin = msgDict['total_pulses_delivered']//20
        III = '{0:#0{1}d}'.format(insulin, 3)
        reservoir = msgDict['word_R']//20
        RR = '{0:#0{1}d}'.format(reservoir, 2)
        faultProcessedMsg['pdmRefCode'] = TT + '-' + \
            VVV + HH + '-' + \
            III + RR + '-' + \
            msgDict['decimal_fault_string']

    return faultProcessedMsg
