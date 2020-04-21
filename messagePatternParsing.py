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
from parse_1d import *
from parse_1f import *

# note - parsers not finished return a hex string for 'msg_type', e.g., '0x01'
#        whereas parsers that have been finished use '1a16' or '1d'
def ignoreMsg(msg):
    msgDict = {}
    byteMsg = bytearray.fromhex(msg)
    msgDict['mtype'] = byteMsg[0]
    msgDict['msg_type'] = hex(byteMsg[0])
    msgDict['msg_body'] = msg
    msgDict['msgMeaning'] = 'checkWiki'
    return msgDict

def badMsg(msg):
    msgDict = {}
    msgDict['mtype'] = '0xFF'
    msgDict['msg_type'] = '0xFF'
    msgDict['msg_body'] = msg
    msgDict['msgMeaning'] = 'Unknown'
    return msgDict

def emptyMsg(msg):
    msgDict = {}
    msgDict['mtype'] = '0x00'
    msgDict['msg_type'] = 'ACK'
    msgDict['msg_body'] = msg
    msgDict['msgMeaning'] = 'ack'
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
    0x1a: parse_1a,
    0x1d: parse_1d,
    0x1f: parse_1f
}

# decide how to handle message based on msg string
# special case for empty msg aka ACK
def processMsg(msg):
    if msg == '':
        thisMessage = emptyMsg(msg)
    else:
        byteMsg = bytearray.fromhex(msg)
        if len(byteMsg)<3:
            print('msg_body not understood: ', msg)
            thisMessage = badMsg(msg)
        else:
            thisMessage = chooseMsgType.get(byteMsg[0],ignoreMsg)(msg)
    return thisMessage
