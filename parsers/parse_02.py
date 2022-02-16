# file: parse_02 - does the parsing for the 0x02 message returned from the pod
from util.misc import combineByte
from util.pod import getUnitsFromPulses
import numpy as np


def parse_02(byteList, msgDict):
    # extract information from the 02 response and return as a dictionary
    # first check the Type and then call that subfunction

    typeInfo = byteList[2]
    msgDict['type_of_0x02_message'] = '{0:#0{1}x}'.format(typeInfo, 4)
    # print('typeInfo is ', msgDict['type_of_0x02_message'])
    if typeInfo == 0x01:
        msgDict = parse_0201(byteList, msgDict)
    elif typeInfo == 0x02:
        msgDict = parse_0202(byteList, msgDict)
    elif typeInfo == 0x03:
        msgDict = parse_0203(byteList, msgDict)
    elif typeInfo == 0x05:
        msgDict = parse_0205(byteList, msgDict)
    elif typeInfo == 0x50:
        msgDict = parse_0250(byteList, msgDict)
    elif typeInfo == 0x51:
        msgDict = parse_0251(byteList, msgDict)
    else:
        print('Type,', msgDict['type_of_0x02_message'],
              ', not recognized for 0x02 response')

    return msgDict


def parse_0201(byteList, msgDict):
    # print('Type, 0x01, is WIP for 0x02 response')
    msgDict['msgType'] = '0x0201'
    msgDict['msgMeaning'] = 'Response to ConfigAlerts Request'

    return msgDict


def parse_0202(byteList, msgDict):
    # extract information from the 02 response, type 2, return as a dictionary
    """
    My example:
     msg = '0216020d00001b0d0a5b40108d03ff108f0000189708030d8010'
        OFF 1  2  3  4  5 6  7  8 9 10 1112 1314 1516 17 18 19 20 21 2223
        02 16 02 0d 00 001b 0d 0a5b 40 108d 03ff 108f 00 00 18 97 08 030d 8010
    The type 2 response provides information on a fault event.
        OFF 1  2  3  4  5 6  7  8 9 10 1112 1314 1516 17 18 19 20 21 2223
        02 16 02 0J 0K LLLL MM NNNN PP QQQQ RRRR SSSS TT UU VV WW 0X YYYY

    02 (1 byte) [$0]: mtype value of 02 specifies status information
    16 (1 byte) [$1]: mlen of a type 2 response is always $16
    02 (1 byte) [$2]: type of this status format is 2
    0J (1 byte) [$3]: Current Pod Progress value (00 thru 0F)
    0K (1 byte) [$4]: bit mask for active insulin delivery
    1: Basal active, exclusive of 2 bit
    2: Temp basal active, exclusive of 1 bit
    4: Immediate bolus active, exclusive of 8 bit
    8: Extended bolus active, exclusive of 4 bit
    LLLL (2 bytes) [$5:$6]: 0.05U insulin pulses not delivered
    MM (1 byte) [$7]: message sequence number (saved B9>>2)
    NNNN (1 bytes) [$8:$9]: total # of pulses delivered
    PP (1 byte) [$A]: original logged fault event, if any
    QQQQ (2 bytes) [$B:$C]: fault event time in minutes since Pod activation
        or $ffff if unknown due to an unexpected MCU reset
    RRRR (2 bytes) [$D:$E]: # of 0.05U pulses remaining if
                    <= 50U or $3ff if > 50U
    SSSS (2 bytes) [$F:$10]: minutes since Pod activation
    TT (1 byte) [$11]: bit mask of the active, unacknowledged alerts
        (1 << alert #) from the $19 Command, this bit mask is the same as the
        aaaaaaaaa bits in the $1D Response
    UU (1 byte) [$12]: 2 if there is a fault accessing tables
    VV (1 byte) [$13]: bits abbcdddd with information about logged fault event
    a: insulin state table corruption found during error logging
    bb: internal 2-bit variable set and manipulated in main loop routines
    c: immediate bolus in progress during error
    dddd: Pod progress at time of first logged fault event (same as 0X value)
    WW (1 byte): [$14] bits aabbbbbb
    aa: receiver low gain
    bbbbbb: radio RSSI
    0X (1 byte): [$15] Pod progress at time of first logged fault event
    YYYY (2 bytes): [$16:$17] unknown
    """

    mlen = byteList[1]
    if mlen != 0x16:
        msgDict['msgMeaning'] = '0x0202, unexpected size'
        return msgDict

    pod_progress = byteList[3]
    byte_4 = byteList[4]
    word_L = combineByte(byteList[5:7])
    byte_M = byteList[7]
    word_N = combineByte(byteList[8:10])
    byte_P = byteList[10]
    word_Q = combineByte(byteList[11:13])
    word_R = combineByte(byteList[13:15])
    word_S = combineByte(byteList[15:17])
    byte_T = byteList[17]
    byte_U = byteList[18]
    byte_V = byteList[19]
    byte_W = byteList[20]
    byte_X = byteList[21]
    word_Y = combineByte(byteList[22:24])
    cksm = combineByte(byteList[24:26])

    #  can extract gain and rssi from the byte_W
    #  WW (1 byte): [$14] bits aabbbbbb
    #    aa: receiver low gain
    #    bbbbbb: radio RSSI
    gg = byte_W & 0xC0 >> 6
    ss = byte_W & 0x3F
    msgDict['recvGain'] = gg
    msgDict['rssiValue'] = ss

    if pod_progress <= 9:
        msgDict['msgMeaning'] = 'DetailedStatus'
    else:
        msgDict['msgMeaning'] = 'FaultEvent'

    # Since byte_2 was 2, update msgType
    msgDict['msgType'] = '0x0202'

    msgDict['pod_progress'] = pod_progress

    msgDict['extended_bolus_active'] = (byte_4 & 0x8) != 0
    msgDict['immediate_bolus_active'] = (byte_4 & 0x4) != 0
    msgDict['temp_basal_active'] = (byte_4 & 0x2) != 0
    msgDict['basal_active'] = (byte_4 & 0x1) != 0

    msgDict['pulses_not_delivered'] = word_L
    msgDict['insulin_not_delivered'] = getUnitsFromPulses(word_L)

    msgDict['seq_byte_M'] = byte_M

    msgDict['total_pulses_delivered'] = word_N
    msgDict['insulinDelivered'] = getUnitsFromPulses(word_N)

    msgDict['logged_fault'] = '{:#04x}'.format(byte_P)
    msgDict['decimal_fault_string'] = '{0:#0{1}d}'.format(byte_P, 3)
    # msgDict['logged_fault'] = f'{byte_P: 0x%X}'

    msgDict['fault_time_minutes_since_pod_activation'] = word_Q
    resLevel = word_R & 0x3FF
    if resLevel == 0x3FF:
        msgDict['reservoir'] = '>50 u'
    else:
        msgDict['reservoir'] = getUnitsFromPulses(resLevel)

    msgDict['podOnTime'] = word_S
    msgDict['alerts_bit_mask'] = byte_T
    msgDict['table_fault'] = (byte_U == 2)
    msgDict['word_R'] = word_R
    msgDict['byte_V'] = byte_V
    msgDict['byte_W'] = byte_W
    msgDict['pod_progress_at_fault'] = byte_X
    msgDict['word_Y'] = word_Y
    msgDict['checkSum'] = cksm

    # but if logged_fault is 0x34, many registers are reset
    if msgDict['logged_fault'] == '0x34':
        msgDict['pulses_not_delivered'] = np.nan
        msgDict['pulsesTotal'] = np.nan
        msgDict['fault_time_minutes_since_pod_activation'] = np.nan
        msgDict['podOnTime'] = np.nan
        msgDict['pulses_not_delivered'] = np.nan

    return msgDict


def parse_0203(byteList, msgDict):
    # print('Type, 0x03, is WIP for 0x02 response')
    # Note - this has 60 pulse log entries "Plus" some other sturr
    msgDict['msgType'] = '0x0203'
    msgDict['msgMeaning'] = 'PodInfoPulseLogPlus'

    return msgDict


def parse_0205(byteList, msgDict):
    # print('Type, 0x05, is WIP for 0x02 response')
    msgDict['msgType'] = '0x0205'
    msgDict['msgMeaning'] = 'PodInfoActivationTime'

    return msgDict


def parse_0250(byteList, msgDict):
    # print('Type, 0x50, is WIP for 0x02 response')
    msgDict['msgType'] = '0x0250'
    msgDict['msgMeaning'] = 'PodInfoPulseLog'

    return msgDict


def parse_0251(byteList, msgDict):
    # print('Type, 0x51, is WIP for 0x02 response')
    msgDict['msgType'] = '0x0251'
    msgDict['msgMeaning'] = 'PodInfoPulseLogPrevious'

    return msgDict
