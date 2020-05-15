"""
messageLogs_functions.py

Parse either old messageLog format or new deviceCommunication format

Updates: changed name to message instead of command, in some places

Examples:
        MessageLog format:
        * 2020-02-06 06:01:23 +0000 send 1f036f631c030e01008043
        * 2020-02-06 06:01:26 +0000 receive 1f036f63200a1d18002e2800000073ff8388

        Device Communication Log format:
        * 2020-04-01 02:15:01 +0000 DexG6Transmitter 81H33P connection Connected
        * 2020-04-01 02:15:02 +0000 DexG6Transmitter 81H33P receive New reading: 2020-04-01 02:14:56 +0000
        * 2020-04-01 02:15:05 +0000 Omnipod 1F0910C8 send 1f0910c810030e0100835b
        * 2020-04-01 02:15:06 +0000 Omnipod 1F0910C8 receive 1f0910c8140a1d18022700000016b3ff01e0


"""

import time
import re
import pandas as pd
import os
import markdown
from bs4 import BeautifulSoup, NavigableString, Tag
from utils import *
from messagePatternParsing import *

# Some markdown headings don't start on their own line. This regular expression
# finds them so we can insert a newline. (Needed for some MessageLog files)
FIXME_RE = re.compile(r'(?!#).(##+.*)')

# Markdown headings we want to extract from the .md report
# Handle case where last line of messageLog is 'status: ##'
# Add new ## PodInfoFaultEvent markdown heading
# Add new ## Device Communication Log markdown heading - this replaces MessageLog
#  note it's either MessageLog or Device Communication Log
MARKDOWN_HEADINGS_TO_EXTRACT = ['OmnipodPumpManager', 'MessageLog', 'PodState', \
  'PodInfoFaultEvent', 'Device Communication Log', 'LoopVersion']

def parse_filehandle(filehandle):
    """Given a filehandle, extract the content from below markdown headings.

    Args:
       filehandle: a python file object
    Returns:
       A dict of markdown heading -> list of text from that heading
    """
    # read content from file
    content = filehandle.read()

    # remove << which breaks one line into two (in the soup section later)
    content = content.replace('<<', '')

    # make sure each Header is properly format for soup use
    for fixme in re.findall(FIXME_RE, content):
        content = content.replace(fixme, '\n' + fixme, 1)
    html = markdown.markdown(content)
    soup = BeautifulSoup(html, features='html.parser')
    data = {}
    for header in soup.find_all(['h2', 'h3'], text=MARKDOWN_HEADINGS_TO_EXTRACT):
        nextNode = header
        data.setdefault(header.text, [])
        while True:
            nextNode = nextNode.nextSibling
            if nextNode is None:
                break
            elif isinstance(nextNode, NavigableString):
                data[header.text].append(nextNode.strip()) if nextNode.strip() else None
            elif isinstance(nextNode, Tag):
                if nextNode.name in ['h2', 'h3']:
                    break
                data[header.text].extend([text for text in nextNode.stripped_strings])
    return data

"""
    splitFullMsg splits the hexToParse from Loop report into components

    Use: https://github.com/openaps/openomni/wiki/Message-Structure information

    An ACK packet has a different format
        different for MessageLog, which had empty msg_body
        and Device Communication Log, which has CRC at msg_body loc

"""

def splitFullMsg(hexToParse):
    # print(len(hexToParse), hexToParse)
    address = hexToParse[:8]
    thisLen = len(hexToParse)
    if thisLen <= 10:
        # "old-style" ACK
        print( '\n *** ', len(hexToParse), hexToParse, '\n')
        BLEN = 0
        CRC = '0000' # indicates no CRC provided
        # an empty msg_body is treated as an ACK
        msg_body = ''
        seqNum = -1
    else:
        # new-style ACK is handled properly here (msg_body is empty)
        B9_b = combineByte(list(bytearray.fromhex(hexToParse[8:10])))
        seqNum = (B9_b & 0x3C)>>2
        BLEN = hexToParse[10:12]
        msg_body = hexToParse[12:-4]
        CRC = hexToParse[-4:]
    msgDict = processMsg(msg_body)
    CRC = '0x'+CRC
    return address, seqNum, BLEN, msgDict, CRC

## orginal version for MessageLog format
"""
    MessageLog format:
        * 2020-02-06 06:01:23 +0000 send 1f036f631c030e01008043
        * 2020-02-06 06:01:26 +0000 receive 1f036f63200a1d18002e2800000073ff8388
"""
def message_dict(data):
    timestamp = data[0:19]
    # skip the UTC time delta characters ( +0000 ), logs are always in UTC
    stringToUnpack = data[26:]

    action, hexToParse = stringToUnpack.rsplit(' ', 1)
    address, seqNum, BLEN, msgDict, CRC = splitFullMsg(hexToParse)
    podMessagesDict = dict(
        time=timestamp,
        address=address, type=action, seqNum=seqNum,
        msgDict=msgDict, CRC=CRC )
    return podMessagesDict

## new version for Device Communication Log format
#  needs work
"""
    Device Communication Log format:
        * 2020-04-01 02:15:01 +0000 DexG6Transmitter 81H33P connection Connected
        * 2020-04-01 02:15:02 +0000 DexG6Transmitter 81H33P receive New reading: 2020-04-01 02:14:56 +0000
        * 2020-04-01 02:15:05 +0000 Omnipod 1F0910C8 send 1f0910c810030e0100835b
        * 2020-04-01 02:15:06 +0000 Omnipod 1F0910C8 receive 1f0910c8140a1d18022700000016b3ff01e0

"""
def device_message_dict(data):
    # set default values in case they cannot be found or have wrong format
    device = 'unknown'
    address = 'unknown'
    logAddr = 'unknown'
    action = 'unknown'
    seqNum = -1
    msgDict = {}
    CRC    = 'unknown'

    noisy = 0    # ONLY set noisy to 1 when using short test.md file
    if noisy:
        print("\n")
        print(data)

    # data format examples:
    #   0123456789012345678901234567890123456789012345678901234567890123456789
    #   2020-04-11 09:45:51 +0000 Omnipod 1F02029E send 1f02029e3c030e0100813c
    #   2020-04-01 22:39:59 +0000 DexG6Transmitter 81H33P connection Connected

    timestamp = data[0:19]
    # skip the UTC time delta characters ( +0000 ), logs are always in UTC
    stringToUnpack = data[26:]

    # extract common information, parse Omnipod, leave other devices alone for now
    # note that address is ffffffff until Loop and Pod finish some init steps
    device, logAddr, action, restOfLine = stringToUnpack.split(' ',3)
    if device=="Omnipod":
        # address is what pod thinks address is
        address, seqNum, BLEN, msgDict, CRC = splitFullMsg(restOfLine)
        if (logAddr.lower() != address) and (address != 'ffffffff'):
            print('\nThe two message numbers do not agree \n', logAddr, address)
            print(msg_body)
            print(data)
    else:
        msg_body = restOfLine

    deviceMessagesDict = dict(
          time=timestamp, device=device,
          logAddr=logAddr, address=address, type=action, seqNum=seqNum,
          msgDict=msgDict, CRC=CRC )
    if noisy:
        print('\n')
        printDict(deviceMessagesDict)
    return deviceMessagesDict

def extract_pod_manager(data):
    # set up default
    podMgrDict = {}
    if data.get('OmnipodPumpManager'):
        podMgrDict = dict([[x.strip() for x in v.split(':', 1)]
                for v in data['PodState']])
    return podMgrDict

def extract_fault_info(data):
    faultInfoDict = {}
    if 'PodInfoFaultEvent' in data:
        faultInfoDict = dict([[x.strip() for x in v.split(':', 1)]
                for v in data['PodInfoFaultEvent']])
    return faultInfoDict

def extract_loop_version(data):
    # set up default
    loopVersionDict = {}
    if 'LoopVersion' in data:
        loopVersionDict = dict([[x.strip() for x in v.split(':', 1)]
                for v in data['LoopVersion']])
    return loopVersionDict

def generate_table(podFrame, radio_on_time):
    # add columns to the DataFrame - valid only when a single pod is included
    podFrame['time'] = pd.to_datetime(podFrame['time'])
    podFrame['deltaSec'] = (podFrame['time']-podFrame['time'].shift()).dt.seconds.fillna(0).astype(float)
    podFrame['timeAsleep'] = podFrame['deltaSec'].loc[podFrame['deltaSec'] > radio_on_time] - radio_on_time  # radio_on_time seconds the radio stays awake
    return podFrame

# parse the person in the filename
def getPersonFromFilename(filename, last_timestamp):
    val = '^.*/'
    thisPerson = re.findall(val, filename)
    if not thisPerson:
        thisPerson = 'Unknown'
    else:
        thisPerson = thisPerson[0] [0:-1]

    val = '/.*$'
    thisFullName = re.findall(val, filename)
    #print(thisFullName)
    thisFullName = thisFullName[0]
    #print(thisFullName)
    thisFullName = thisFullName[1:]
    #print(thisFullName)
    thisFullName = thisFullName.replace(' ','') # remove spaces
    thisFullName = thisFullName.replace('-','') # remove hypens
    thisFullName = thisFullName.replace('_','') # remove underscores
    # trim off some characters
    thisDate = thisFullName[10:18] + '_' + thisFullName[18:22]

    return thisPerson, thisDate

"""
  Handles either MessageLog or Device Communication Log
  Note - there were several version of having status being tacked
         on to the end of the MessageLog, handle these cases
  Break into more modular chunks
"""
def loop_read_file(filename):
    fileType = "unknown"
    file = open(filename, "r", encoding='UTF8')
    parsed_content = parse_filehandle(file)
    if parsed_content.get('MessageLog'):
        fileType = "messageLog"
        # handle various versions of status: being tacked onto end
        tmp = parsed_content['MessageLog'][-1]
        tmpEnd = tmp[len(tmp)-7:]
        # Handle case where last line of messageLog is 'status: ##'
        if tmpEnd=='status:':
            # print(' *** Last Message:\n', parsed_content['MessageLog'][-1])
            if len(tmp) == 7:
                # print('  length of last message was {:d}'.format(len(tmp)))
                parsed_content['MessageLog'] = parsed_content['MessageLog'][:-1]
            else:
                # print('  length of last message was {:d} (not 7)'.format(len(tmp)))
                parsed_content['MessageLog'][-1] = tmp[:len(tmp)-8]
            # print('  ',parsed_content['MessageLog'][-1], '\n ***\n')
    if parsed_content.get('Device Communication Log'):
        fileType = "deviceLog"
    # now return dataframe from entire log, podDict, fault_report separately
    logDF = extract_messages(fileType, parsed_content)
    podMgrDict = extract_pod_manager(parsed_content)
    faultInfoDict = extract_fault_info(parsed_content)
    loopVersionDict = extract_loop_version(parsed_content)
    return fileType, logDF, podMgrDict, faultInfoDict, loopVersionDict

def omnipodP(message):
    return message['device'] == "Omnipod"

# later can put what ever device in as a specifc check, for now, just not Omnipod
def otherP(message):
    return message['device'] != "Omnipod"

def extract_messages(fileType, parsed_content):
    # set up default
    noisy = 0
    pod_messages = ['nil']
    if fileType == "messageLog":
        # only pod messages are found in this section of the Loop Report
        pod_messages = [message_dict(m) for m in parsed_content['MessageLog']]
    elif fileType == "deviceLog":
        # pod messages interleaved with CGM messages in this Loop Report
        messages = [device_message_dict(m) for m in parsed_content['Device Communication Log']]
        pod_messages = list(filter(omnipodP, messages))
        if noisy:
            print('\n Pod Messages')
            printList(pod_messages[1:5])
            printList(pod_messages[-2:-1])

        # this works - use it later if desired
        if noisy:
            print('\n CGM Messages')
            cgm_messages = list(filter(otherP, messages))
            printList(cgm_messages[1:5])
            printList(cgm_messages[-2:-1])
    # logDF all pod messages in Report (can be across multiple pods)
    logDF = pd.DataFrame(pod_messages)
    return logDF
