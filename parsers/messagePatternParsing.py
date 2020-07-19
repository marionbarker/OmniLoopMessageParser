# file: messagePatternParsing
from util.misc import combineByte

from parsers.parse_01 import parse_01
from parsers.parse_02 import parse_02
from parsers.parse_03 import parse_03
from parsers.parse_06 import parse_06
from parsers.parse_08 import parse_08
from parsers.parse_0e import parse_0e
from parsers.parse_1a13 import parse_1a13
from parsers.parse_1a16 import parse_1a16
from parsers.parse_1a17 import parse_1a17
from parsers.parse_19 import parse_19
from parsers.parse_1c import parse_1c
from parsers.parse_1d import parse_1d
from parsers.parse_1f import parse_1f


def unparsedMsg(byteList, msgDict):
    # 0x07 is so simple, just parse it here
    if byteList[0] == 0x07:
        msgDict['msgMeaning'] = 'assignID'
        msgDict['useAddr'] = hex(combineByte(byteList[2:6]))
    else:
        msgDict['msgMeaning'] = 'checkWiki'
    return msgDict


def ackMsg(byteList, msgDict):
    # byteList not used, but have it to match all other calls
    msgDict['msgType'] = 'ACK'
    msgDict['mlen'] = 0
    msgDict['msgMeaning'] = 'ACK'
    # TODO if this is suitable format for ACK, replace seqNum with packetNum
    return msgDict


def parse_1a(byteList, msgDict):
    # extract information the indicator for type of 1a command
    xtype = byteList[2 + byteList[1]]
    xtypeStr = '{:x}'.format(xtype)
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
    0x03: parse_03,
    0x06: parse_06,
    0x08: parse_08,
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
    msgDict = {'msgType': '', 'msgMeaning': ''}
    byteList = list(bytearray.fromhex(msg))
    if len(byteList) < 3:
        thisMessage = ackMsg(byteList, msgDict)
        # print(thisMessage)
    else:
        msgDict['msgType'] = '{0:#0{1}x}'.format(byteList[0], 4)
        thisMessage = chooseMsgType.get(byteList[0],
                                        unparsedMsg)(byteList, msgDict)
    # add msg_body last cause it's long
    if 'mlen' not in msgDict:
        msgDict['mlen'] = byteList[1]
    msgDict['msg_body'] = msg
    return thisMessage
