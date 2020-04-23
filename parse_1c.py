# file: parse_1c - is a request to deactivate the pod

from utils import *

def parse_1c(msg):
    """
    Example:
     msg = '1c041793f587'
        1c 04 NNNNNNNN
        1c 04 1793f587

    The $1C Deactivate Pod command is used to fully deactivate the current Pod.
    The deactivate Pod command has no arguments other than the nonce.

    1c (1 byte): mtype of this response is 06
    04 (1 byte): mlen for this response is always 04
    NN (4 byte): nonce
    """

    byteMsg = bytearray.fromhex(msg)
    byteList = list(byteMsg)
    mtype = byteList[0]
    mlen = byteList[1]
    nonce = combineByte(byteList[2:])

    msgDict = { }
    msgDict['msg_type'] = '{0:#0{1}x}'.format(mtype,4)
    msgDict['mtype'] = mtype
    msgDict['mlen'] = mlen
    msgDict['nonce'] = nonce
    msgDict['msgMeaning'] = 'DeactivatePod'

    return msgDict
