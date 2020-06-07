# file: parse_02 - does the parsing for the 0x02 message returned from the pod

from utils import *
from utils_pod import *
from parse_0202 import *

import numpy as np

def parse_02(byteList, msgDict):
    # extract information from the 02 response and return as a dictionary
    # first check the Type and then call that subfunction

    typeInfo = byteList[2]
    msgDict['type_of_0x02_message'] = '{0:#0{1}x}'.format(typeInfo,4)
    print('typeInfo is ',msgDict['type_of_0x02_message'])
    if typeInfo == 0x01:
        msgDict = parse_0201(byteList, msgDict)
    elif typeInfo == 0x02:
        msgDict = parse_0202(byteList, msgDict)
    elif typeInfo == 0x03:
        msgDict = parse_0203(byteList, msgDict)
    elif typeInfo == 0x05:
        msgDict = parse_0205(byteList, msgDict)
    elif typeInfo == 0x50:
        msgDict = parse_0250(byteList, msgDict)
    elif typeInfo == 0x51:
        msgDict = parse_0251(byteList, msgDict)
    else:
        print('Type,', msgDict['type_of_0x02_message'], ', not recognized for 0x02 response')

    return msgDict

def parse_0201(byteList, msgDict):
    print('Type, 0x01, is WIP for 0x02 response')
    msgDict['msgType'] = '0x0201'
    msgDict['msgMeaning'] = 'Response to ConfigAlerts Request'

    return msgDict

def parse_0203(byteList, msgDict):
    print('Type, 0x03, is WIP for 0x02 response')
    msgDict['msgType'] = '0x0203'
    msgDict['msgMeaning'] = 'Response to PulseEntryLog Request'

    return msgDict

def parse_0205(byteList, msgDict):
    print('Type, 0x05, is WIP for 0x02 response')
    msgDict['msgType'] = '0x0205'
    msgDict['msgMeaning'] = 'Fault Code & Time, Time since Pod Initialization'

    return msgDict

def parse_0250(byteList, msgDict):
    print('Type, 0x50, is WIP for 0x02 response')
    msgDict['msgType'] = '0x0250'
    msgDict['msgMeaning'] = 'Last 50 dwords in pulse log'

    return msgDict

def parse_0251(byteList, msgDict):
    print('Type, 0x51, is WIP for 0x02 response')
    msgDict['msgType'] = '0x0251'
    msgDict['msgMeaning'] = 'Earlier dwords in pulse log'

    return msgDict
