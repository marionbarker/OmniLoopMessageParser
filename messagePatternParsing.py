# file: messagePatternParsing
import numpy as np
from utils import *

from parse_01 import *
from parse_02 import *
from parse_06 import *
from parse_0e import *
from parse_1a13 import *
from parse_1a16 import *
from parse_1a17 import *
from parse_19 import *
from parse_1c import *
from parse_1d import *
from parse_1f import *

def unparsedMsg(msg):
    msgDict = {}
    byteMsg = bytearray.fromhex(msg)
    mtype = byteMsg[0]
    msgDict['mtype'] = mtype
    #msgDict['msg_type'] = hex(byteMsg[0])
    msgDict['msg_type'] = '{0:#0{1}x}'.format(mtype,4)
    if mtype == 0x07:
        msgDict['msgMeaning'] = 'assignID'
    elif mtype == 0x03:
        msgDict['msgMeaning'] = 'setupPod'
    elif mtype == 0x08:
        msgDict['msgMeaning'] = 'cnfgDelivFlags'
    else:
        msgDict['msgMeaning'] = 'checkWiki'
    return msgDict

def ackMsg(msg):
    msgDict = {}
    msgDict['mtype'] = 'ACK'
    msgDict['msg_type'] = 'ACK'
    msgDict['msgMeaning'] = 'ACK'
    return msgDict

def parse_1a(msg):
    # extract information the indicator for type of 1a command
    byteMsg = bytearray.fromhex(msg)
    byteList = list(byteMsg)
    mlen = byteList[1]
    xtype = byteList[2+mlen]
    if xtype == 0x16:
        msgDict = parse_1a16(msg)
    elif xtype == 0x17:
        msgDict = parse_1a17(msg)
    else:
        msgDict = parse_1a13(msg)

    return msgDict

chooseMsgType = {
    0x01: parse_01,
    0x02: parse_02,
    0x06: parse_06,
    0x0e: parse_0e,
    0x19: parse_19,
    0x1a: parse_1a,
    0x1c: parse_1c,
    0x1d: parse_1d,
    0x1f: parse_1f
}

# decide how to handle message based on msg string
# special case for empty msg aka ACK
def processMsg(msg):
    if msg == '':
        # format before Loop 2.2
        thisMessage = ackMsg(msg)
    else:
        # format with Loop 2.2
        byteMsg = bytearray.fromhex(msg)
        if len(byteMsg)<3:
            thisMessage = ackMsg(msg)
        else:
            thisMessage = chooseMsgType.get(byteMsg[0],unparsedMsg)(msg)
    return thisMessage
