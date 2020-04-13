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

# Some markdown headings don't start on their own line. This regular expression
# finds them so we can insert a newline. (Needed for some MessageLog files)
FIXME_RE = re.compile(r'(?!#).(##+.*)')

# Markdown headings we want to extract from the .md report
# Handle case where last line of messageLog is 'status: ##'
# Add new ## PodInfoFaultEvent markdown heading
# Add new ## Device Communication Log markdown heading - this replaces MessageLog
#  note it's either MessageLog or Device Communication Log
MARKDOWN_HEADINGS_TO_EXTRACT = ['OmnipodPumpManager', 'MessageLog', 'PodState', 'PodInfoFaultEvent', 'Device Communication Log']

def _parse_filehandle(filehandle):
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

def splitFullMsg(full_msg):
    address = full_msg[:8]
    B9 = full_msg[8:10] # B9 is string
    byteMsg = bytearray.fromhex(B9) # convert to list of bytes
    byteList = list(byteMsg)
    B9_b = combineByte(byteList)
    seq_num = (B9_b & 0x3C)>>2
    BLEN = full_msg[10:12]
    msg_plus_crc = full_msg[12:]
    # The CRC-16 is at the end of the raw_value
    thisLength = len(msg_plus_crc)
    CRC16 = msg_plus_crc[-4:]
    msg_body = msg_plus_crc[:thisLength-4]
    return address, seq_num, BLEN, msg_body, CRC16

## orginal version for MessageLog format
"""
    MessageLog format:
        * 2020-02-06 06:01:23 +0000 send 1f036f631c030e01008043
        * 2020-02-06 06:01:26 +0000 receive 1f036f63200a1d18002e2800000073ff8388
"""
def _message_dict(data):
    timestamp, action, full_msg = data.rsplit(' ', 2)
    address, seq_num, BLEN, msg_body, CRC16 = splitFullMsg(full_msg)
    podMessagesDict = dict(
        time=timestamp,
        address=address, type=action, seq_num=seq_num,
        msg_body=msg_body, CRC16=CRC16 )
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
def _device_message_dict(data):
    # set default values in case they cannot be found or have wrong format
    device = 'unknown'
    address = 'unknown'
    action = 'unknown'
    seq_num = -1
    msg_body = 'empty'
    CRC16    = 'unknown'

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
    # note that address is what Loop thinks the address is
    device, address, action, restOfLine = stringToUnpack.split(' ',3)
    if device=="Omnipod":
        # addressPod is what pod thinks address is
        addressPod, seq_num, BLEN, msg_body, CRC16 = splitFullMsg(restOfLine)
        if (address.lower() != addressPod) and (addressPod != 'ffffffff'):
            print('\nThe two message numbers do not agree \n', address, addressPod)
            print(seq_num, BLEN, CRC16)
            print(msg_body)
            print(data)
        else:
            address = addressPod  # this returns what pod thinks is the address
    else:
        #device, address, action, full_msg = stringToUnpack.split(' ', 3)
        #dummy1, dummy2, dummy3, device, theRestOfLine = stringToUnpack.split(' ', 1)
        msg_body = restOfLine

    deviceMessagesDict = dict(
          time=timestamp, device=device,
          address=address, type=action, seq_num=seq_num,
          msg_body=msg_body, CRC16=CRC16 )
    if noisy:
        print('\n')
        printDict(deviceMessagesDict)
    return deviceMessagesDict

def _extract_pod_state(data):
    podStateDict = {}
    if 'PodState' in data:
        podStateDict = dict([[x.strip() for x in v.split(':', 1)]
                for v in data['PodState']])
    return podStateDict

def select_extra_message(msg_body):
    if msg_body[:2]=='1a':
        if msg_body[32:34] not in ['16','17']:
            return 13
        else:
            return msg_body[32:34]

def generate_table(df, radio_on_time):
    # convert to a pandas dataframe
    # now done in persist_message - already a DataFrame
    #       df = pd.DataFrame(pod_messages)
    df['time'] = pd.to_datetime(df['time'])
    df['message'] = df['msg_body'].str[:2].astype(str)+df['msg_body'].apply(select_extra_message).fillna('').astype(str)
    df['time_delta'] = (df['time']-df['time'].shift()).dt.seconds.fillna(0).astype(float)
    df['time_asleep'] = df['time_delta'].loc[df['time_delta'] > radio_on_time] - radio_on_time  # radio_on_time seconds the radio stays awake
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
    #print(thisFullName)
    # trim off some characters
    thisDate = thisFullName[10:18] + '_' + thisFullName[18:20]
    #print(thisDate)

    #thisDate = last_timestamp.dt.strftime('%Y%m%d_%r')
    #print(thisDate)
    #thisDate = last_timestamp

    #thisDate = last_timestamp.replace('-','') # remove hyphens
    #thisDate = thisDate.replace(' ','_') # replace space before hour with underscore
    #thisDate = thisDate[0:12] # capture yyyymmdd_hh

    return thisPerson, thisDate

# parse the information in the filename
def parse_info_from_filename(filename):
    val = '^.*/'
    thisPerson = re.findall(val, filename)
    if not thisPerson:
        thisPerson = 'Unknown'
    else:
        thisPerson = thisPerson[0] [0:-1]

    finishValues = {'0x12', '0x14', '0x31', '0x34', '0x3d', '0x40', '0x42', '0x80', 'Nominal', '0x18', '0x1c', 'Unknown','WIP'}
    antennaValues = {'origAnt', 'adHocAnt'}

    for val in finishValues:
        thisFinish = re.findall(val,filename)
        if thisFinish:
            break

    for val in antennaValues:
        thisAntenna = re.findall(val,filename)
        if thisAntenna:
            break

    if not thisFinish:
        thisFinish = ['Nominal']

    if not thisAntenna:
        thisAntenna = ['433MHz']

    return (thisPerson, thisFinish[0], thisAntenna[0])

"""
  Add new versions of code, use prefix persist_ to indicate this was added to
  handle either MessageLog or Device Communication Log
  Break into more modular chunks
"""
def persist_read_file(filename):
    fileType = "unknown"
    file = open(filename, "r", encoding='UTF8')
    parsed_content = _parse_filehandle(file)
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
      pod_dict = _extract_pod_state(parsed_content)
    return pod_dict

def persist_fault_report(parsed_content):
    # set up default
    fault_report = []
    if parsed_content.get('OmnipodPumpManager'):
      pod_dict = _extract_pod_state(parsed_content)
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
        pod_messages = [_message_dict(m) for m in parsed_content['MessageLog']]
    elif fileType == "deviceLog":
        messages = [_device_message_dict(m) for m in parsed_content['Device Communication Log']]
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
