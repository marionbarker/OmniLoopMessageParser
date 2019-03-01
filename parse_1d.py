# file: parse_1d - does the parsing for the 1d message returned from the pod
from byteUtils import *

def parse_1d(msg):
    # extract information from the 1d response and return as a dictionary
    """
    The $1D status response is sent from the Pod to provide information on its
    internal state, including insulin delivery, unacknowledged alerts,
    Pod active time, reservoir level, etc. as the normal response to
    non-specialized commands. This page explains how the different values are
    packed into the $1D status response.

    The $1D status response has the following form:
        00 01 02030405 06070809
        1d SS 0PPPSNNN AATTTTRR

    # byte 0 - 1d
    # byte 1 - nibble 1a, nibble 1b
      nibble 1a
      a 8: Extended bolus active, exclusive of 4 bit
      b 4: Immediate bolus active, exclusive of 8 bit
      c 2: Temp basal active, exclusive of 1 bit
      d 1: Basal active, exclusive of 2 bit
      nibble 1b sequence number 0 to F
    # byte 2:5 = 0PPPSNNN
        0PPPSNNN dword = 0000 pppp pppp pppp psss snnn nnnn nnnn
        0000 4 zero bits
        ppppppppppppp 13 bits, Total 0.05U insulin pulses
        ssss 4 bits, message sequence number (saved B9>>2)
        nnn nnnn nnnn 11 bits, 0.05U Insulin pulses not delivered if cancelled by user
    # byte 6:9 = AATTTTRR
        AATTTTRR dword = faaa aaaa attt tttt tttt ttrr rrrr rrrr
        f 1 bit, 0 or 1 if the Pod has encountered fault event $14
        aaaaaaaa 8 bits, bit mask of the active, unacknowledged alerts (1 << alert #) from the Command 19 Configure Alerts; this bit mask is the same as the TT byte in the 02 Error Response Type 2
        ttttttttttttt 13 bits, Pod active time in minutes
        rrrrrrrrrr 10 bits, Reservoir 0.05U pulses remaining (if <= 50U) or $3ff (if > 50U left)
    """

    byteMsg = bytearray.fromhex(msg)
    byteList = list(byteMsg)
    byte_0 = byteList[0]
    byte_1 = byteList[1]
    # replace combineByte with unpack
    dword_3 = combineByte(byteList[2:6])
    dword_4 = combineByte(byteList[6:10])
    cksm   = combineByte(byteList[10:12])

    #print(msg)
    #print('0x{:x}'.format(combineByte(byte0)))
    #print('0x{:x}'.format(combineByte(byte1)))
    #print('0x{:x}'.format(combineByte(dword0)))
    #print('0x{:x}'.format(combineByte(dword1)))
    #print(combineByte(dword0) >> 15 & 0x1FFF)

    msgDict = { }
    msgDict['message_type'] = '1d'
    msgDict['raw_value']    = msg

    msgDict['extended_bolus_active']   = (byte_1 >> 4 & 0x8) != 0
    msgDict['immediate_bolus_active']  = (byte_1 >> 4 & 0x4) != 0
    msgDict['temp_basal_active']       = (byte_1 >> 4 & 0x2) != 0
    msgDict['basal_active']            = (byte_1 >> 4 & 0x1) != 0

    msgDict['seq_byte_1']  = byte_1 & 0xF

    msgDict['total_pulses_delivered'] = (dword_3 >> 15) & 0x1FFF
    msgDict['total_insulin_delivered']  = int(msgDict['total_pulses_delivered']) * 0.05
    msgDict['seq_dword_0']  = (dword_3 >> 11) & 0xF
    msgDict['pulses_not_delivered'] = dword_3 & 0x007F
    msgDict['insulin_not_delivered'] = int(msgDict['pulses_not_delivered'])*0.05

    msgDict['fault_bit'] = (dword_4 >> 31)
    msgDict['alerts_bit_mask'] = (dword_4 >> 23) & 0xFF
    msgDict['pod_active_minutes'] = (dword_4 >> 10) & 0x1FFF

    if (dword_4 & 0x3FF) == 0x3FF:
        msgDict['reservoir_remaining'] = '>50 u'
    else:
        msgDict['reservoir_remaining'] = '%.2f u remaining'%(int(dword_4 & 0x3FF) * 0.05)

    return msgDict
