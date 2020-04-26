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
MARKDOWN_HEADINGS_TO_EXTRACT = ['OmnipodPumpManager', 'MessageLog', 'PodState', 'PodInfoFaultEvent', 'Device Communication Log']

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
    splitFullMsg takes the Loop packet and splits it into components
      note - except for ACK this is not the full packet between PDM and Pod

    An ACK packet has a different format than a send/recv packet
    so check for ACK status first

    An ACK packet consists of the
        4-byte pod_address_1,
        1-byte packet seq (NOT pod seq_num)
            TTTSSSSS byte (with TTT = 010 and SSSSS = a 5-bit packet seq #)
        4 byte ACK address
        CRC-8 (packet checksum) byte

    and this is what is now apparently being displayed for these ACK packets
    which is now completely differently than the message based format for all
    the other pod communication logging that formerly had empty messages for
    ACK’s (which was OK for me).

    However, for all other messages, the old code works fine.
"""

def splitFullMsg(full_msg):
    print(len(full_msg), full_msg)
    address = full_msg[:8]
    B9 = full_msg[8:10] # B9 is string
    # convert string to list of bytes
    B9list = list(bytearray.fromhex(B9))
    # make a short from the byte list
    B9_b = combineByte(B9list)
    seq_num = (B9_b & 0x3C)>>2
    # An ACK is always 10 long (and all other messages are longer)
    if len(full_msg) == 28:
        BLEN = 0;
        CRC = full_msg[6:10]
        # an empty msg_body is treated as an ACK
        msg_body = ''
    # this is a full message to or from the pod
    else:
        BLEN = full_msg[10:12]
        msg_plus_crc = full_msg[12:]
        # The CRC is at the end of the raw_value
        thisLength = len(msg_plus_crc)
        CRC = msg_plus_crc[-4:]
        msg_body = msg_plus_crc[:thisLength-4]
    CRC = 'hex ' + CRC
    return address, seq_num, BLEN, msg_body, CRC

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

    action, full_msg = stringToUnpack.rsplit(' ', 1)
    address, seq_num, BLEN, msg_body, CRC = splitFullMsg(full_msg)
    podMessagesDict = dict(
        time=timestamp,
        address=address, type=action, seq_num=seq_num,
        msg_body=msg_body, CRC=CRC )
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
    seq_num = -1
    msg_body = ''
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
        address, seq_num, BLEN, msg_body, CRC = splitFullMsg(restOfLine)
        if (logAddr.lower() != address) and (address != 'ffffffff'):
            print('\nThe two message numbers do not agree \n', logAddr, address)
            print(msg_body)
            print(data)
    else:
        msg_body = restOfLine

    deviceMessagesDict = dict(
          time=timestamp, device=device,
          logAddr=logAddr, address=address, type=action, seq_num=seq_num,
          msg_body=msg_body, CRC=CRC )
    if noisy:
        print('\n')
        printDict(deviceMessagesDict)
    return deviceMessagesDict

def extract_pod_state(data):
    podStateDict = {}
    if 'PodState' in data:
        podStateDict = dict([[x.strip() for x in v.split(':', 1)]
                for v in data['PodState']])
    return podStateDict

# This is a bit of a hack.  It works for Loop because the extra message always
# has a fixed length for a 1a16 message (refer to parse_1a16.py)
# Add the 1f here too
def select_extra_message(msg_body):
    if msg_body[:2]=='1a':
        if msg_body[32:34] not in ['16','17']:
            return 13
        else:
            return msg_body[32:34]

def getMsgType(msg_body):
    pmsg = processMsg(msg_body)
    return pmsg['msg_type']

def getMsgMeaning(msg_body):
    pmsg = processMsg(msg_body)
    return pmsg['msgMeaning']

def generate_table(df, radio_on_time):
    # add columns to the DataFrame
    df['time'] = pd.to_datetime(df['time'])
    #df['message'] = df['msg_body'].str[:2].astype(str)+df['msg_body'].apply(select_extra_message).fillna('').astype(str)
    df['time_delta'] = (df['time']-df['time'].shift()).dt.seconds.fillna(0).astype(float)
    df['time_asleep'] = df['time_delta'].loc[df['time_delta'] > radio_on_time] - radio_on_time  # radio_on_time seconds the radio stays awake
    df['msg_type'] = df['msg_body'].apply(getMsgType)
    df['msgMeaning'] = df['msg_body'].apply(getMsgMeaning)
    return df

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
  Add new versions of code, use prefix persist_ to indicate this was added to
  handle either MessageLog or Device Communication Log
  Break into more modular chunks
"""
def persist_read_file(filename):
    fileType = "unknown"
    file = open(filename, "r", encoding='UTF8')
    parsed_content = parse_filehandle(file)
    if parsed_content.get('MessageLog'):
        fileType = "messageLog"
        # Handle case where last line of messageLog is 'status: ##'
        tmp = parsed_content['MessageLog'][-1]
        if tmp=='status:':
            parsed_content['MessageLog'] = parsed_content['MessageLog'][:-1]
    if parsed_content.get('Device Communication Log'):
        fileType = "deviceLog"
    # now extract pod_messages, podDict, fault_report separately
    pod_messages = persist_message(fileType, parsed_content)
    pod_dict = persist_pod_dict(parsed_content)
    fault_report = persist_fault_report(parsed_content)
    return fileType, pod_messages, pod_dict, fault_report

def persist_pod_dict(parsed_content):
    # set up default
    pod_dict = ['nil']
    if parsed_content.get('OmnipodPumpManager'):
      pod_dict = extract_pod_state(parsed_content)
    return pod_dict

def persist_fault_report(parsed_content):
    # set up default
    fault_report = []
    if parsed_content.get('OmnipodPumpManager'):
      pod_dict = extract_pod_state(parsed_content)
    return fault_report

def omnipodP(message):
    return message['device'] == "Omnipod"

# later can put what ever device in as a specifc check, for now, just not Omnipod
def otherP(message):
    return message['device'] != "Omnipod"

def persist_message(fileType, parsed_content):
    # set up default
    noisy = 0
    pod_messages = ['nil']
    if fileType == "messageLog":
        pod_messages = [message_dict(m) for m in parsed_content['MessageLog']]
    elif fileType == "deviceLog":
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
    podFrame = pd.DataFrame(pod_messages)
    return podFrame
