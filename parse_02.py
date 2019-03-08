# file: parse_02 - does the parsing for the 0x02 message returned from the pod
#      NOTE - only parsing the Fault returned version Type 2

from byteUtils import *
from utils import *
import numpy as np

def parse_02(msg):
    # extract information from the 02 response and return as a dictionary
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
    QQQQ (2 bytes) [$B:$C]: fault event time in minutes since Pod activation or $ffff if unknown due to an unexpected MCU reset
    RRRR (2 bytes) [$D:$E]: # of 0.05U pulses remaining if <= 50U or $3ff if > 50U
    SSSS (2 bytes) [$F:$10]: minutes since Pod activation
    TT (1 byte) [$11]: bit mask of the active, unacknowledged alerts (1 << alert #) from the $19 Command, this bit mask is the same as the aaaaaaaaa bits in the $1D Response
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

    byteMsg = bytearray.fromhex(msg)
    byteList = list(byteMsg)
    byte_0 = byteList[0]
    byte_1 = byteList[1]
    byte_2 = byteList[2]
    byte_3 = byteList[3]
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
    cksm   = combineByte(byteList[24:26])

    msgDict = { }
    msgDict['message_type'] = '02'
    msgDict['raw_value']    = msg
    msgDict['mtype'] = byte_0
    msgDict['fault_type'] = byte_2
    if msgDict['fault_type'] != 2:
        msgDict['fault_type'] = 'Not fault type 02, not parsed'
        return msgDict

    msgDict['pod_progress_value']   = byte_3

    msgDict['extended_bolus_active']   = (byte_4 & 0x8) != 0
    msgDict['immediate_bolus_active']  = (byte_4 & 0x4) != 0
    msgDict['temp_basal_active']       = (byte_4 & 0x2) != 0
    msgDict['basal_active']            = (byte_4 & 0x1) != 0

    msgDict['pulses_not_delivered'] = word_L
    msgDict['insulin_not_delivered'] = getUnitsFromPulses(word_L)

    msgDict['seq_byte_M']  = byte_M

    msgDict['total_pulses_delivered'] = word_N
    msgDict['total_insulin_delivered'] = getUnitsFromPulses(word_N)

    msgDict['logged_fault'] = f'0x%X'%(byte_P)

    msgDict['fault_time_minutes_since_pod_activation']  = word_Q
    pulses = word_R & 0x3FF
    if pulses == 0x3FF:
        msgDict['reservoir_remaining'] = '>50 u'
    else:
        msgDict['reservoir_remaining'] = getUnitsFromPulses(pulses)

    msgDict['pod_active_minutes'] = word_S
    msgDict['alerts_bit_mask'] = byte_T
    msgDict['table_fault'] = (byte_U == 2)
    msgDict['byte_V'] = byte_V
    msgDict['byte_W'] = byte_W
    msgDict['pod_progress_at_fault'] = byte_X
    msgDict['word_Y'] = word_Y

    # but if logged_fault is 0x34, many registers are reset
    if msgDict['logged_fault'] == '0x34':
        msgDict['pulses_not_delivered'] = np.nan
        msgDict['total_pulses_delivered'] = np.nan
        msgDict['fault_time_minutes_since_pod_activation'] = np.nan
        msgDict['pod_active_minutes'] = np.nan
        msgDict['pulses_not_delivered'] = np.nan

    return msgDict
