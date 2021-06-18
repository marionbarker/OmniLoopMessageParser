"""
messageLogs_functions.py

Parse either old messageLog format or new deviceCommunication format (*.md)
Add capability to extract messages from FAPSX log file (*.txt)
    new function for dealing with strings for the .txt files

Updates: changed name to message instead of command, in some places

Examples:
    MessageLog format:
    * 2020-02-06 06:01:23 +0000 send 1f036f631c030e01008043
    * 2020-02-06 06:01:26 +0000 receive 1f036f63200a1d18002e2800000073ff8388

    Device Communication Log format:
    * 2020-04-01 02:15:01 +0000 DexG6Transmitter 81H33P connection Connected
    * 2020-04-01 02:15:02 +0000 DexG6Transmitter 81H33P receive \
                                New reading: 2020-04-01 02:14:56 +0000
    * 2020-04-01 02:15:05 +0000 Omnipod 1F0910C8 send 1f0910c810030e0100835b
    * 2020-04-01 02:15:06 +0000 Omnipod 1F0910C8 receive \
                                1f0910c8140a1d18022700000016b3ff01e0
"""

# import time
import re
import pandas as pd
# import os
import markdown
from bs4 import BeautifulSoup, NavigableString, Tag
from util.misc import combineByte
from util.misc import printDict, printList
from parsers.messagePatternParsing import processMsg
# add for FAPSX files
import time
import os
from collections import Counter
import numpy as np


# Some markdown headings don't start on their own line. This regular expression
# finds them so we can insert a newline. (Needed for some MessageLog files)
FIXME_RE = re.compile(r'(?!#).(##+.*)')

# Markdown headings we want to extract from the .md report
# Handle case where last line of messageLog is 'status: ##'
# Add new ## PodInfoFaultEvent markdown heading
# Add new ## Device Communication Log markdown heading:
#  note it's either MessageLog or Device Communication Log
MARKDOWN_HEADINGS_TO_EXTRACT = ['OmnipodPumpManager', 'MessageLog',
                                'PodState', 'PodInfoFaultEvent',
                                'Device Communication Log', 'LoopVersion']


# this is only called for files that end in ".md"
def parse_filehandle(filehandle):
    """Given a filehandle, extract the content from below markdown headings.

    Args:
       filehandle: a python file object
    Returns:
       A dict of markdown heading -> list of text from that heading
    """
    # read content from file
    content = filehandle.read()

    # saved first lines in case LoopVersion not found
    maxChars = 1000
    firstChars = content[0:maxChars]

    # remove << which breaks one line into two (in the soup section later)
    content = content.replace('<<', '')

    # make sure each Header is properly format for soup use
    for fixme in re.findall(FIXME_RE, content):
        content = content.replace(fixme, '\n' + fixme, 1)
    html = markdown.markdown(content)
    soup = BeautifulSoup(html, features='html.parser')
    data = {}
    for header in soup.find_all(['h2', 'h3'],
                                text=MARKDOWN_HEADINGS_TO_EXTRACT):
        nextNode = header
        data.setdefault(header.text, [])
        while True:
            nextNode = nextNode.nextSibling
            if nextNode is None:
                break
            elif isinstance(nextNode, NavigableString):
                data[header.text].append(nextNode.strip()) \
                    if nextNode.strip() else None
            elif isinstance(nextNode, Tag):
                if nextNode.name in ['h2', 'h3']:
                    break
                data[header.text].extend(
                                         [text for text in
                                          nextNode.stripped_strings])
    return data, firstChars


def splitFullMsg(hexToParse):
    """
        splitFullMsg splits the hexToParse from Loop report into components

        See:
          https://github.com/openaps/openomni/wiki/Message-Structure

        An ACK hexToParse has 2 historical formats, both with empty message
            ## MessageLog <= 10 bytes with no CRC
            ## Device Communication  has address, packetNumber and CRC

        Because all messages (except ACK) have seqNum,
             reuse seqNum key for the ACK packet number in msgDict

    """
    address = hexToParse[:8]
    thisLen = len(hexToParse)
    # Handle older ## message log format for ACK
    if thisLen <= 10:
        byte89 = 0
        # processMsg below returns ACK from an empty msg_body
        msg_body = ''
        CRC = '0000'  # indicates no CRC provided
    else:
        byte89 = combineByte(list(bytearray.fromhex(hexToParse[8:10])))
        msg_body = hexToParse[12:-4]
        CRC = hexToParse[-4:]
    msgDict = processMsg(msg_body)
    # for ACK, extract packet number (if available) - request from Joe
    #    use seqNum key for storage
    if msgDict['msgType'] == 'ACK':
        packetNumber = (byte89 & 0x1F)
        msgDict['seqNum'] = packetNumber
    else:
        msgDict['seqNum'] = (byte89 & 0x3C) >> 2
    msgDict['rawHex'] = hexToParse
    msgDict['CRC'] = '0x' + CRC
    if msgDict['msgType'] == '0x0202':
        print(f' ** {msgDict["msgMeaning"]}, gain: {msgDict["recvGain"]}, \
                rssi: {msgDict["rssiValue"]}')
    return address, msgDict


def message_dict(data):
    timestamp = data[0:19]
    # skip the UTC time delta characters ( +0000 ), logs are always in UTC
    stringToUnpack = data[26:]

    action, hexToParse = stringToUnpack.rsplit(' ', 1)
    address, msgDict = splitFullMsg(hexToParse)
    podMessagesDict = dict(
        time=timestamp,
        address=address, type=action,
        msgDict=msgDict)
    return podMessagesDict

def fapsx_message_dict(data):
    # extract dateTtime from beginning of line
    timestamp = data[0:10] + ' ' + data[11:19]
    # skip the verbose stuff before the raw hex message
    hexToParse = data[166:]
    # the send/receive is not supplied for FAPSX_Files
    action = "unknown"
    address, msgDict = splitFullMsg(hexToParse)
    podMessagesDict = dict(
        time=timestamp,
        address=address, type=action,
        msgDict=msgDict)
    return podMessagesDict


def device_message_dict(data):
    # set default values in case they cannot be found or have wrong format
    device = 'unknown'
    address = 'unknown'
    logAddr = 'unknown'
    action = 'unknown'
    msgDict = {}
    msg_body = 'unknown'

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

    # extract common information, parse Omnipod, other devices ignored for now
    # note that address is ffffffff until Loop and Pod finish some init steps
    device, logAddr, action, restOfLine = stringToUnpack.split(' ', 3)
    if device == "Omnipod":
        # address is what pod thinks address is
        address, msgDict = splitFullMsg(restOfLine)
        if (logAddr.lower() != address) and (address != 'ffffffff'):
            print('\nThe two message numbers do not agree \n',
                  logAddr, address)
            print(msg_body)
            print(data)
    else:
        msg_body = restOfLine

    deviceMessagesDict = dict(
          time=timestamp, device=device,
          logAddr=logAddr, address=address, type=action,
          msgDict=msgDict)
    if noisy:
        print('\n')
        printDict(deviceMessagesDict)
    return deviceMessagesDict


def extract_pod_manager(data):
    # set up default
    podMgrDict = {}
    if data.get('OmnipodPumpManager'):
        try:
            podMgrDict = dict([[x.strip() for x in v.split(':', 1)]
                              for v in data['PodState']])
        except ValueError:
            print('Information Only: PodState not defined in log file')
            # ab = 4 # non op
    return podMgrDict


def extract_fault_info(data):
    faultInfoDict = {}
    if 'PodInfoFaultEvent' in data:
        faultInfoDict = dict([[x.strip() for x in v.split(':', 1)]
                             for v in data['PodInfoFaultEvent']])
    return faultInfoDict


def extract_loop_version(data, firstChars):
    # set up default
    loopVersionDict = {}
    if 'LoopVersion' in data:
        loopVersionDict = dict([[x.strip() for x in v.split(':', 1)]
                               for v in data['LoopVersion']])

    """
    else:
        print(firstChars)
        # break this at \n
        versionLines = []
        idx = 0
        foundIt = 0
        for line in firstChars.strip().split("\n"):
            versionLines[idx] = line
            print(idx, versionLines[idx])
            if versionLines[idx][3:9] == "gitRev":
                foundIt = idx
            idx += 1

        print('FoundIt = ', foundIt)
        print(versionLines)
        # search for keywords in versionLines, try to extract loopVersionDict
        if foundIt > 0:
            idx = 0
            loopVersionDict['Version'] = versionLines[foundIt + idx]
            while idx < 6:
                idx += 1
                v = versionLines[foundIt + idx]
                #loopVersionDict = dict([[x.strip() for x in v.split(':', 1)]
    """

    return loopVersionDict


def generate_table(podFrame, radio_on_time):
    # add columns to the DataFrame - valid only when a single pod is included
    # radio_on_time seconds the pod radio stays awake (higher power mode)
    rot = radio_on_time
    podFrame['timeAsleep'] = podFrame['deltaSec'].loc[
                                podFrame['deltaSec'] > rot] - rot
    return podFrame


# add check of filename ending string to split between Loop and FAPSX
def loop_read_file(filename):
    """
      Handles either MessageLog or Device Communication Log or FAPSX log
      Note - there were several version of having status being tacked
             on to the end of the MessageLog, handle these cases
      Break into more modular chunks
      returns a dictionary of items
    """
    fileType = "unknown"
    parsed_content = {}
    # define empty dataframe, if fapsx, fill with determine basal info from log
    determBasalDF = pd.DataFrame({})
    # decide if this is an md file or a txt file.
    last3 = filename[-3:]
    file = open(filename, "r", encoding='UTF8')
    if (last3==".md"):
        parsed_content, firstChars = parse_filehandle(file)
    else:
        raw_content = file.read()
    if parsed_content.get('MessageLog'):
        fileType = "messageLog"
        # handle various versions of status: being tacked onto end
        tmp = parsed_content['MessageLog'][-1]
        tmpEnd = tmp[len(tmp)-7:]
        # Handle case where last line of messageLog is 'status: ##'
        if tmpEnd == 'status:':
            # print(' *** Last Message:\n', parsed_content['MessageLog'][-1])
            if len(tmp) == 7:
                # print('  length of last message was {:d}'.format(len(tmp)))
                parsed_content['MessageLog'] = \
                                   parsed_content['MessageLog'][:-1]
            else:
                # print('  length of last message was {:d}
                #        (not 7)'.format(len(tmp)))
                parsed_content['MessageLog'][-1] = tmp[:len(tmp)-8]
            # print('  ',parsed_content['MessageLog'][-1], '\n ***\n')
    if parsed_content.get('Device Communication Log'):
        fileType = "deviceLog"
    # For FAPSX, use extract_raw to parse, create new dataframe from FAPSX
    #   enable tracking of IOB, COB and BG
    # For Loop return dataframe from entire log, podDict, fault_report separately
    if fileType == 'unknown':
        logDF, determBasalDF = extract_raw(raw_content)
        # print('check logDF')
        if logDF.empty:
            fileType = "not FAPSX"
            # print(logDF)
        else:
            fileType = "FAPSX"
            # print(logDF)
        faultInfoDict = {}
        loopVersionDict = {}
    else:
        logDF = extract_messages(fileType, parsed_content)
        faultInfoDict = extract_fault_info(parsed_content)
        loopVersionDict = extract_loop_version(parsed_content, firstChars)
    if 'PodState' in parsed_content:
        podMgrDict = extract_pod_manager(parsed_content)
    else:
        podMgrDict = {}

    loopReadDict = {'fileType': fileType,
                    'logDF': logDF,
                    'podMgrDict': podMgrDict,
                    'faultInfoDict': faultInfoDict,
                    'loopVersionDict': loopVersionDict,
                    'determBasalDF': determBasalDF}

    # ensure file is closed
    file.close()
    return loopReadDict


def omnipodP(message):
    return message['device'] == "Omnipod"


def otherP(message):
    # later can add other devices, for now, just not Omnipod
    return message['device'] != "Omnipod"

def extract_raw(raw_content):
    logDF = pd.DataFrame({})
    determBasalDF = pd.DataFrame({})
    verbose_flag = 0
    if verbose_flag:
        print(">>>   call to extract_raw placeholder")
        print("first 256 characters")
        print(raw_content[:256])
        print("last 256 characters")
        print(raw_content[-256:])

    # extract content (between /n) with this string:
    #    "318 - DEV: Device message:"
    lines_raw = raw_content.splitlines()
    if verbose_flag:
        print('first line\n', lines_raw[0])
        print('last line\n', lines_raw[-1])

    pod_patt = "318 - DEV: Device message:"
    pod_messages = [x for x in lines_raw if x.find(pod_patt)>-1]
    if verbose_flag:
        print('first pod line\n', pod_messages[0][0:19], ' ', pod_messages[0][166:])
        print('last pod line\n', pod_messages[-1][0:19], ' ', pod_messages[-1][166:])
        num_lines = len(pod_messages)
        print('Found ', num_lines)
    # brute force for now - get time and hex code
#   012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789
#   2021-06-06T00:03:53-0700 [DeviceManager] DeviceDataManager.swift - deviceManager(_:logEventForDeviceIdentifier:type:message:completion:) - 318 - DEV: Device message: 1f091a4634030e010003e8
    messages = [fapsx_message_dict(m) for m in pod_messages]

    verbose_flag = 0
    if verbose_flag:
        print('first messages line\n', messages[0])
        print('last messages line\n', messages[-1])
        print('number of messages is ', len(messages))
    logDF = pd.DataFrame(messages)
    logDF['time'] = pd.to_datetime(logDF['time'])
    #logDF['time_delta'] = (logDF['time'] - \
    #        logDF['time'].shift()).dt.seconds.fillna(0).astype(float)
    logDF['deltaSec'] = (logDF['time'] - \
            logDF['time'].shift()).dt.seconds.fillna(0).astype(float)

    # now extract the determine basal message
    db_patt = "68 - DEV: SUGGESTED:"
    #db_messages = [x for x in lines_raw if x.find(db_patt)>-1]
    idx = 0
    numLines = len(lines_raw)
    line_array = []
    timestamp_array = []
    bg_array = []
    cob_array = []
    iob_array = []
    print("numLines = ", numLines)
    while idx<numLines-1:
        thisLine = lines_raw[idx]
        if thisLine.find(db_patt)>-1:
            # extract dateTime from beginning of line
            timestamp = thisLine[0:10] + ' ' + thisLine[11:19]
            line_in_file = idx
            # find first "IOB" (predBGIOB) and extract first BG value
            while thisLine.find("IOB")==-1 and idx<numLines-1:
                idx = idx+1
                thisLine = lines_raw[idx]
            idx = idx+1
            thisLine = lines_raw[idx]
            bg_current = thisLine[-6:]
            # find first "reason"
            while thisLine.find("reason")==-1 and idx<numLines-1:
                idx = idx+1
                thisLine = lines_raw[idx]
            # back up 2 lines
            cob = lines_raw[idx-2][10:]
            iob = lines_raw[idx-1][10:]
            # print(idx, timestamp, cob, iob)
            line_array.append(line_in_file)
            timestamp_array.append(timestamp)
            bg_array.append(bg_current)
            cob_array.append(cob)
            iob_array.append(iob)
        else:
            idx = idx+1
            thisLine = lines_raw[idx]

        d = {'line#': line_array, 'time': timestamp_array,
             'bg': bg_array, 'cob': cob_array, 'iob': iob_array}
        determBasalDF = pd.DataFrame(d)

    return logDF, determBasalDF

def extract_messages(fileType, parsed_content):
    # set up default
    noisy = 1
    pod_messages = ['nil']
    if fileType == "messageLog":
        # only pod messages are found in this section of the Loop Report
        pod_messages = [message_dict(m) for m in parsed_content['MessageLog']]
    elif fileType == "deviceLog":
        # pod messages interleaved with CGM messages in this Loop Report
        messages = [device_message_dict(m)
                    for m in parsed_content['Device Communication Log']]
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
    else:
        print('Filetype is not messageLog or DeviceLog')
        print('Will parse the raw_content')
        print(raw_content[0:80])
    # logDF all pod messages in Report (can be across multiple pods)
    logDF = pd.DataFrame(pod_messages)
    logDF['time'] = pd.to_datetime(logDF['time'])
    logDF['deltaSec'] = (logDF['time'] -
                         logDF['time'].shift()
                         ).dt.seconds.fillna(0).astype(float)

    return logDF
