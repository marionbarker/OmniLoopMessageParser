# file: parse_1f - does the parsing for cancel commond
from utils import *
from decimal import Decimal

def parse_1f(msg):
    # extract information from the 1f cancel command
    """
    Command $1F is the Cancel command. It has the following format:

        OFF 1  2 3 4 5  6
        1f 05 NNNNNNNN AX
        1f 05 22c1cf8c 02 80f7

    1f (1 byte): Mtype value of $1f specifies a cancel command
    05 (1 byte): The cancel command always has a fixed length of 05
    NNNNNNNN (4 bytes): Nonce, the 32-bit validator (random looking numbers)
    AX (1 byte): Command byte of the form aaaa0bcd:
        The aaaa (A) nibble in the range of (0..8) and is the type of the Pod alarm/beep type to sound.
            An aaaa value = 0 is no alarm
                          = 2 two quick beeps
                          = 6 one longer beep
            Values of A larger than 8 are out of range and can lock up a Pod with a constant beep.
        The b ($04) bit being set will cancel any ongoing bolus and will turn off the RR reminder variables set from the $17 Bolus Extra command.
        The c ($02) bit being set will cancel any ongoing temporary basal and will turn off the RR reminder variables set from the $16 Temp Basal command.
        The d ($01) bit being set will cancel the basal program and will turn off the RR reminder variables set from the $13 Basal Schedule command.
    The Pod responds to the $1F command with a $1D status message.
    """

    msgDict = { }
    msgDict['msg_type'] = '1f'
    msgDict['msg_body']    = msg

    byteMsg = bytearray.fromhex(msg)
    byteList = list(byteMsg)
    mtype = byteList[0]
    mlen = byteList[1]
    nonce = combineByte(byteList[2:6])
    cancelByte = byteList[6]
    alertValue = (cancelByte >> 4) & 0xF
    cancelBolus = (cancelByte & 0x04) != 0
    cancelTB    = (cancelByte & 0x02) != 0
    suspend     = (cancelByte & 0x01) != 0

    msgDict = { }
    msgDict['msg_type'] = '1f'
    msgDict['msg_body']    = msg
    msgDict['mtype'] = mtype
    msgDict['mlen'] = mlen
    msgDict['nonce'] = nonce
    msgDict['cancelByte'] = cancelByte
    msgDict['alertValue'] = alertValue
    msgDict['cancelBolus'] = cancelBolus
    msgDict['cancelTB'] = cancelTB
    msgDict['suspend'] = suspend

    return msgDict
