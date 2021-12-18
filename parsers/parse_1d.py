# file: parse_1d - does the parsing for the 1d message returned from the pod
from util.misc import combineByte
from util.pod import getUnitsFromPulses, getPodProgressMeaning


def parse_1d(byteList, msgDict):
    # extract information from the 1d response and return as a dictionary
    """
    The $1D status response is sent from the Pod to provide information on its
    internal state, including insulin delivery, unacknowledged alerts,
    Pod active time, reservoir level, etc. as the normal response to
    non-specialized commands. This page explains how the different values are
    packed into the $1D status response.

    It is the only command without an mlen value
     - always fixed length of 12 bytes

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
        ssss 4 bits, message sequence # of last processed programming command
        nnn nnnn nnnn 11 bits, 0.05U Insulin pulses not delivered
                                     if cancelled by user
    # byte 6:9 = AATTTTRR
        AATTTTRR dword = faaa aaaa attt tttt tttt ttrr rrrr rrrr
        f 1 bit, 0 or 1 if the Pod has encountered fault event $14
        aaaaaaaa 8 bits, bit mask of the active, unacknowledged
                 alerts (1 << alert #) from the Command 19 Configure Alerts;
                 this bit mask is the same as the TT byte in the
                 02 Error Response Type 2
        ttttttttttttt 13 bits, Pod active time in minutes
        rrrrrrrrrr 10 bits, Reservoir 0.05U pulses remaining (if <= 50U)
                            or $3ff (if > 50U left)
    """

    msgDict['msgMeaning'] = 'PodStatus'
    # only fixed length message where byte_1 has a different meaning
    byte_1 = byteList[1]
    msgDict['pod_progress'] = byte_1 & 0xF

    dword_3 = combineByte(byteList[2:6])
    dword_4 = combineByte(byteList[6:10])

    msgDict['podOnTime'] = (dword_4 >> 10) & 0x1FFF
    msgDict['reservoir'] = ''  # placeholder for desired order

    # get pulses and units of insulin delivered
    # dword_3: 0PPPSNNN = 0000 pppp pppp pppp psss snnn nnnn nnnn
    pulsesDelivered = (dword_3 >> 15) & 0x1FFF
    insulinDelivered = getUnitsFromPulses(pulsesDelivered)
    msgDict['pulsesTotal'] = pulsesDelivered
    msgDict['insulinDelivered'] = insulinDelivered
    msgDict['cmdSeqNum'] = (dword_3 >> 11) & 0xF

    msgDict['extended_bolus_active'] = (byte_1 >> 4 & 0x8) != 0
    msgDict['immediate_bolus_active'] = (byte_1 >> 4 & 0x4) != 0
    msgDict['temp_basal_active'] = (byte_1 >> 4 & 0x2) != 0
    msgDict['basal_active'] = (byte_1 >> 4 & 0x1) != 0

    msgDict['pod_progress_meaning'] = getPodProgressMeaning(byte_1 & 0xF)

    # get pulses and units of insulin NOT delivered
    # fixed mask was 0x007f instead of 0x07ff
    pulsesNot = dword_3 & 0x07FF
    insulinNot = getUnitsFromPulses(pulsesNot)
    msgDict['pulses_not_delivered'] = pulsesNot
    msgDict['insulin_not_delivered'] = insulinNot

    msgDict['fault_bit'] = (dword_4 >> 31)
    msgDict['alerts_bit_mask'] = (dword_4 >> 23) & 0xFF

    if (dword_4 & 0x3FF) == 0x3FF:
        msgDict['reservoir'] = '>50 u'
    else:
        pulses = dword_4 & 0x3FF
        insulin = getUnitsFromPulses(pulses)
        msgDict['reservoir'] = insulin

    msgDict['mlen'] = 12
    # msgDict['checkSum'] = cksm

    return msgDict
