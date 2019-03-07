# file: messagePatternParsing
import numpy as np
from byteUtils import *
from utils import *

from parse_02 import *
from parse_06 import *
from parse_1d import *
from parse_1a16 import *

def ignoreMsg(msg):
    msgDict = {}
    msgDict['message_type'] = 'Not Parsed Yet'
    msgDict['raw_value']    = msg
    msgDict['total_insulin_delivered']    = np.nan
    msgDict['insulin_not_delivered']      = np.nan
    return msgDict

def parse_1a(msg):
    # extract information the indicator for type of 1a command
    byteMsg = bytearray.fromhex(msg)
    byteList = list(byteMsg)
    xtype = byteList[16]
    if xtype == 0x16:
        msgDict = parse_1a16(msg)
    else:
        msgDict = ignoreMsg(msg)

    return msgDict

chooseMsgType = {
    0x02: parse_02,
    0x06: parse_06,
    0x1a: parse_1a,
    0x1d: parse_1d
}

def processMsg(rawMsg):
    byteMsg = bytearray.fromhex(rawMsg)
    return chooseMsgType.get(byteMsg[0],ignoreMsg)(rawMsg)
