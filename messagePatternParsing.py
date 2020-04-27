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

def unparsedMsg(byteList, msgDict):
    # byteList not used, but have it to match all other calls
    if byteList[0] == 0x07:
        msgDict['msgMeaning'] = 'assignID'
    elif byteList[0] == 0x03:
        msgDict['msgMeaning'] = 'setupPod'
    elif byteList[0] == 0x08:
        msgDict['msgMeaning'] = 'cnfgDelivFlags'
    else:
        msgDict['msgMeaning'] = 'checkWiki'
    return msgDict

def ackMsg(byteList, msgDict):
    # byteList not used, but have it to match all other calls
    msgDict['msgType'] = 'ACK'
    msgDict['mlen'] = 0
    msgDict['msgMeaning'] = 'ACK'
    return msgDict

def parse_1a(byteList, msgDict):
    # extract information the indicator for type of 1a command
    xtype = byteList[2+msgDict['mlen']]
    xtypeStr = '{0:x}'.format(xtype,2)
    msgDict['msgType'] = msgDict['msgType']+xtypeStr
    if xtype == 0x16:
        msgDict = parse_1a16(byteList, msgDict)
    elif xtype == 0x17:
        msgDict = parse_1a17(byteList, msgDict)
    else:
        msgDict = parse_1a13(byteList, msgDict)

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
# this section contains msgDict elements for all messages
#   special case for empty msg aka ACK
def processMsg(msg):
    # want msgType and msgMeaning to show up first
    # will be overwritten later
    msgDict = {'msgType':'', 'msgMeaning':''}
    byteList = list(bytearray.fromhex(msg))
    if len(byteList)<3:
        thisMessage = ackMsg(byteList, msgDict)
        # print(thisMessage)
    else:
        msgDict['mlen'] = byteList[1]
        msgDict['msgType'] = '{0:#0{1}x}'.format(byteList[0],4)
        thisMessage = chooseMsgType.get(byteList[0],unparsedMsg)(byteList, msgDict)
    # add msg_body last cause it's long
    msgDict['msg_body'] = msg
    return thisMessage
