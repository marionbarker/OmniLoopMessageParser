# file: parse_08 - is a request to configure delivery flags for the pod
#  wiki: https://github.com/openaps/openomni/wiki/Command-08-Configure-Delivery-Flags

from util.misc import combineByte

def parse_08(byteList, msgDict):
    """
    Command 08 is a special command that can be used at Pod startup to
    configure a couple of internal delivery flags.
    This command is has not been seen to be used by the PDM.

    The 08 Configure Delivery Flags command has the following format:

        OFF 1  2 3 4 5  6  7
        08 06 NNNNNNNN JJ KK

    08 (1 byte) [0]: mtype value of 08 is the Configure Delivery Flags command
    06 (1 byte) [1]: mlen for this command is always 06
    NNNNNNNN (4 bytes) [2:5]: the Nonce, the 32-bit validator (random looking numbers)
    JJ (1 byte) [6]: new Tab5[0x16] value, must be 0 or 1; Pod default value is 1
    KK (1 byte) [7]: new Tab5[0x17] value, must be 0 or 1; Pod default value is 0

    The JJ byte should be set to 00 to override the default Tab5[0x16]
    value of 1 which will disable the default handling for the
        $5A, $60, $61, $62, $66, $67, $68, $69, $6A
    pump conditions during a pulse delivery, so that they will not generate a
    Pod fault if this condition isn't found to be cleared in a subsequent
    pulse delivery in the next 30 minutes. (Happened a lot in early Loop testing)

    The KK byte should be set to 00 to keep Tab5[0x17] at its default value of zero.
    If this value is set to 01, the Pod will make a number of adjustments to
    various internal variables and a countdown timer which are used during
    the delivery of an immediate bolus.
    """
    msgDict['msgMeaning'] = 'cnfgDelivFlags'
    msgDict['nonce'] = hex(combineByte(byteList[2:6]))
    msgDict['JJ(1)'] = byteList[6]
    msgDict['KK(0)'] = byteList[7]

    return msgDict
