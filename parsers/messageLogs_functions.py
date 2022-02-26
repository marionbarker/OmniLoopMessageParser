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
import os
import subprocess
import numpy as np
import json
import tempfile


# Some markdown headings don't start on their own line. This regular expression
# finds them so we can insert a newline. (Needed for some MessageLog files)
FIXME_RE = re.compile(r'(?!#).(##+.*)')

# Markdown headings we want to extract from the .md report
# Handle case where last line of messageLog is 'status: ##'
# Add new ## PodInfoFaultEvent markdown heading
# Add new ## Device Communication Log markdown heading:
#  note it's either MessageLog or Device Communication Log
MARKDOWN_HEADINGS_TO_EXTRACT = ['OmnipodPumpManager', 'OmniBLEPumpManager',
                                'MessageLog', 'Device Communication Log',
                                'PodState', 'PodInfoFaultEvent',
                                'LoopVersion', 'Version', 'Build Details',
                                ]


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
        print(nextNode)
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
    return data


def splitFullMsg(hexToParse):
    """
        splitFullMsg splits the hexToParse from Loop report into components

        See:
          https://github.com/openaps/openomni/wiki/Message-Structure

        An ACK hexToParse has 2 historical formats, both with empty message
            ## MessageLog <= 10 hex characters with no CRC
            ## Device Communication  has address, packetNumber and CRC

        Because all messages (except ACK) have seqNum,
             reuse seqNum key for the ACK packet number in msgDict

    """
    address = hexToParse[:8]
    thisLen = len(hexToParse)
    # Handle older ## message log format for ACK
    if thisLen <= 10:
        B9 = 0  # match label in wiki
        # processMsg below returns ACK from an empty msg_body
        msg_body = ''
        CRC = '0000'  # indicates no CRC provided
    else:
        B9 = combineByte(list(bytearray.fromhex(hexToParse[8:10])))
        msg_body = hexToParse[12:-4]
        CRC = hexToParse[-4:]
    msgDict = processMsg(msg_body)
    # for ACK, extract packet number (if available) - request from Joe
    #    use seqNum key for storage
    if msgDict['msgType'] == 'ACK':
        packetNumber = (B9 & 0x1F)
        msgDict['seqNum'] = packetNumber
    else:
        msgDict['seqNum'] = (B9 & 0x3C) >> 2
    msgDict['rawHex'] = hexToParse
    msgDict['CRC'] = '0x' + CRC
    # noisy = 0
    # if noisy and msgDict['msgType'] == '0x0202':
    #    print(f' ** {msgDict["msgMeaning"]}, gain: {msgDict["recvGain"]}, \
    #            rssi: {msgDict["rssiValue"]}')
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
    if device[0:7] == "Omnipod":
        # address is what pod thinks address is
        address, msgDict = splitFullMsg(restOfLine)
        if noisy and (logAddr.lower() != address) and (address != 'ffffffff'):
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
    elif data.get('OmniBLEPumpManager'):
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


def extract_loop_version(data):
    # set up default
    loopVersionDict = {}
    if 'Build Details' in data:
        loopVersionDict = dict([[x.strip() for x in v.split(':', 1)]
                               for v in data['Build Details']])
    elif 'LoopVersion' in data:
        loopVersionDict = dict([[x.strip() for x in v.split(':', 1)]
                               for v in data['LoopVersion']])
    elif 'Version' in data:
        loopVersionDict = dict([[x.strip() for x in v.split(':', 1)]
                               for v in data['Version']])

    return loopVersionDict


def generate_table(podFrame, radio_on_time):
    # add columns to the DataFrame - valid only when a single pod is included
    # radio_on_time seconds the pod radio stays awake (higher power mode)
    rot = radio_on_time
    podFrame['timeAsleep'] = podFrame['deltaSec'].loc[
                                podFrame['deltaSec'] > rot] - rot
    return podFrame


# pass in fileDict instead of filename
def loop_read_file(fileDict):
    """
      Handles either MessageLog or Device Communication Log or FAPSX log
      Note - there were several version of having status being tacked
             on to the end of the MessageLog, handle these cases
      Break into more modular chunks
      returns a dictionary of items
    """
    fileDict['recordType'] = "unknown"
    parsed_content = {}
    # define empty dataframes
    logDF = pd.DataFrame({})
    determBasalDF = pd.DataFrame({})
    podMgrDict = {}
    loopVersionDict = {}
    faultInfoDict = {}
    noisy = 0

    # prepare default return dictonary, note that fileDict might be modified
    loopReadDict = {'fileDict': fileDict,
                    'logDF': logDF,
                    'podMgrDict': podMgrDict,
                    'faultInfoDict': faultInfoDict,
                    'loopVersionDict': loopVersionDict,
                    'determBasalDF': determBasalDF}

    # check loopType and act accordingly
    filename = fileDict['filename']
    if fileDict['loopType'].lower() == "loop":
        file = open(filename, "r", encoding='UTF8')
        parsed_content = parse_filehandle(file)
        # ensure file is closed
        file.close()
        if parsed_content.get('MessageLog'):
            fileDict['recordType'] = "messageLog"
            # handle various versions of status: being tacked onto end
            tmp = parsed_content['MessageLog'][-1]
            tmpEnd = tmp[len(tmp)-7:]
            # Handle case where last line of messageLog is 'status: ##'
            if tmpEnd == 'status:':
                if noisy:
                    print(' *** Last Message:\n',
                          parsed_content['MessageLog'][-1])
                if len(tmp) == 7:
                    if noisy:
                        print('  length of last message was {:d}'.
                              format(len(tmp)))
                    parsed_content['MessageLog'] = \
                        parsed_content['MessageLog'][:-1]
                else:
                    if noisy:
                        print('  length of last message was {:d} (not 7)'.
                              format(len(tmp)))
                    parsed_content['MessageLog'][-1] = tmp[:len(tmp)-8]
                    if noisy:
                        print('  ',
                              parsed_content['MessageLog'][-1], '\n ***\n')
        if parsed_content.get('Device Communication Log'):
            fileDict['recordType'] = "deviceLog"

        logDF = extract_messages(fileDict['recordType'], parsed_content)
        faultInfoDict = extract_fault_info(parsed_content)
        loopVersionDict = extract_loop_version(parsed_content)
        if 'PodState' in parsed_content:
            podMgrDict = extract_pod_manager(parsed_content)
        else:
            podMgrDict = {}

    elif fileDict['loopType'].lower() == "fx":
        """
            read the raw content then parse for pods / fx separately
        """
        fp = open(filename, "r", encoding='UTF8')
        raw_content = fp.read()
        fp.close()

        logDF = extract_raw_pod(raw_content)
        determBasalDF = extract_raw_determBasal(raw_content)

        fileDict['recordType'] = "FAPSX"  # overwrite if both DF are empty
        if determBasalDF.empty and logDF.empty:
            fileDict['recordType'] = "not_FAPSX"
            fileDict['date'] = fileDict['recordType']
        elif logDF.empty:
            thisDate = pd.to_datetime(determBasalDF.loc[0,
                                      'date_time'])
            fileDict['date'] = thisDate.strftime('%Y%m%d')
        else:
            thisDate = logDF.loc[0, 'time']
            fileDict['date'] = thisDate.strftime('%Y%m%d')
        faultInfoDict = {}
        loopVersionDict = {}
    else:
        print('loopType is not recognized')
        return loopReadDict

    # There are some items that are useful to have in fileDict that are
    # sometimes found in loopVersionDict and sometimes with different id
    # This field has had various names over the versions of Loop, collect them
    # fill those in with values or empty strings before returning.
    fileDict['appNameAndVersion'] = ''
    fileDict['buildDateString'] = ''
    fileDict['gitRevision'] = ''
    fileDict['gitBranch'] = ''
    fileDict['workspaceGitRevision'] = ''
    fileDict['workspaceGitBranch'] = ''
    if 'appNameAndVersion' in loopVersionDict:
        fileDict['appNameAndVersion'] = loopVersionDict['appNameAndVersion']
    if 'codeVersion' in loopVersionDict:
        fileDict['appNameAndVersion'] = loopVersionDict['codeVersion']
        loopVersionDict['appNameAndVersion'] = loopVersionDict['codeVersion']
    if 'Version' in loopVersionDict:
        fileDict['appNameAndVersion'] = loopVersionDict['Version']
        loopVersionDict['appNameAndVersion'] = loopVersionDict['Version']
    if 'buildDateString' in loopVersionDict:
        fileDict['buildDateString'] = loopVersionDict['buildDateString']
    if 'gitRevision' in loopVersionDict:
        fileDict['gitRevision'] = loopVersionDict['gitRevision']
    if 'gitBranch' in loopVersionDict:
        fileDict['gitBranch'] = loopVersionDict['gitBranch']
    if 'workspaceGitRevision' in loopVersionDict:
        fileDict['workspaceGitRevision'] = \
            loopVersionDict['workspaceGitRevision']
    if 'workspaceGitBranch' in loopVersionDict:
        fileDict['workspaceGitBranch'] = loopVersionDict['workspaceGitBranch']
    loopReadDict = {'fileDict': fileDict,
                    'logDF': logDF,
                    'podMgrDict': podMgrDict,
                    'faultInfoDict': faultInfoDict,
                    'loopVersionDict': loopVersionDict,
                    'determBasalDF': determBasalDF}

    return loopReadDict


def omnipodP(message):
    thisIsAPod = message['device'][0:7] == "Omnipod"
    return thisIsAPod


def otherP(message):
    thisIsAPod = message['device'][0:7] == "Omnipod"
    return not thisIsAPod


def extract_raw_pod(raw_content):
    logDF = pd.DataFrame({})
    noisy = 0
    if noisy:
        print(">>>   call to extract_raw_pod")
        print("first 256 characters : ", raw_content[:256])
        print("last  256 characters : ", raw_content[-256:])

    # split by newline:
    lines_raw = raw_content.splitlines()
    numLines = len(lines_raw)

    if numLines == 0:
        print("numLines = ", numLines, " in extract_raw_pod")
        return logDF
    elif noisy:
        print("numLines = ", numLines, " in extract_raw_pod")

    if noisy:
        print('first line\n', lines_raw[0])
        print('last line\n', lines_raw[-1])

    # Note, there are some 318 - DEV: lines that don't send pod message
    # Need to come back and fix this, but skip them to avoid problems
    #  when splitting logDF into separate pods later
    # At some point in time, FAX started using a different pattern
    pod_patt = "318 - DEV: Device message:"
    pod_messages = [x for x in lines_raw if x.find(pod_patt) > -1]
    if len(pod_messages) == 0:
        pod_patt = "385 - DEV: Device message:"
        pod_messages = [x for x in lines_raw if x.find(pod_patt) > -1]
        if len(pod_messages) == 0:
            pod_patt = "417 - DEV: Device message:"
            pod_messages = [x for x in lines_raw if x.find(pod_patt) > -1]
            if len(pod_messages) == 0:
                return logDF
    if noisy:
        print('first pod line\n', pod_messages[0][0:19], ' ',
              pod_messages[0][166:])
        print('last pod line\n', pod_messages[-1][0:19], ' ',
              pod_messages[-1][166:])
        num_lines = len(pod_messages)
        print('Found ', num_lines)
    messages = [fapsx_message_dict(m) for m in pod_messages]

    noisy = 0
    if noisy:
        print('first messages line\n', messages[0])
        print('last messages line\n', messages[-1])
        print('number of messages is ', len(messages))
    logDF = pd.DataFrame(messages)
    logDF['time'] = pd.to_datetime(logDF['time'])
    logDF['deltaSec'] = (
        logDF['time'] -
        logDF['time'].shift()).dt.seconds.fillna(0).astype(float)

    return logDF


def extract_raw_determBasal(raw_content):

    determBasalDF = pd.DataFrame({})
    date_patt = raw_content[:8]
    # number of lines after json string starts to search for TB/SMB success
    max_lines = 400

    noisy = 0
    if noisy:
        print(">>>   call to extract_raw_determBasal")
        print("first 256 characters : ", raw_content[:256])
        print("last  256 characters : ", raw_content[-256:])
        print("date_patt is ", date_patt)

    # split by newline:
    lines_raw = raw_content.splitlines()

    # now extract the determine basal message
    # use the time pattern from messages to id end of json strings
    determBasal_patt = " 68 - DEV:"
    pump_events = "239 - DEV: New pump events:"
    pe_num = 4  # number of lines to search for Bolus or TempBasal

    idx = 0
    numLines = len(lines_raw)

    if numLines == 0:
        print("numLines = ", numLines, " in extract_raw_determBasal")
        return determBasalDF
    elif noisy:
        print("numLines = ", numLines, " in extract_raw_determBasal")

    """
     items in json, choose the ones we want:
        "temp": "absolute",
        "bg": 79,
        "tick": "+0",
        "eventualBG": 111,
        "insulinReq": -0.25,
        "reservoir": 75.6,
        "deliverAt": "2021-06-28T04:02:55.250Z",
        "sensitivityRatio": 1,
        "predBGs": { numbers here for one or more predictions}
        "COB": 18,
        "IOB": 0.69,
        "reason": "COB: 18, Dev: 16, BGI: -3, ISF: 56, CR: 13.15,
                   Target: 82, minPredBG 68, minGuardBG 62, IOBpredBG 54,
                   COBpredBG 111, UAMpredBG 59; Eventual BG 111 >= 82,
                   insulinReq -0.25; setting 60m low temp of 0U/h. ",
        "rate": tbr,
        "duration": 60
        or
        "units": 0.075,
        "duration": 30,
        "rate": tbr
        or
        nothing - if Skip neutral temps is not selected
                    and scheduled basal is suggested
    """

    idx = 0
    numLines = len(lines_raw)
    line_array = []
    timestamp_array = []
    json_length_array = []
    bg_array = []
    sens_array = []
    cob_array = []
    iob_array = []
    rate_array = []
    bolus_array = []
    tb_success_array = []
    smb_success_array = []
    while idx < numLines-1:
        thisLine = lines_raw[idx]
        if determBasal_patt in thisLine:
            line_0 = idx
            # extract dateTime from beginning of line
            timestamp = thisLine[0:10] + ' ' + thisLine[11:19]
            # json string begins at the { at end of this line and ends before
            #   beginning of the next line which start with date_patt,
            #   white space is ignored outside of quotes
            jdx = idx
            json_message = "{"
            while (jdx < numLines-1) and (jdx < (line_0+max_lines-1)):
                jdx += 1
                if lines_raw[jdx][:8] == date_patt:
                    break
                json_message += lines_raw[jdx]

            try:
                json_dict = json.loads(json_message)
            except Exception as e:
                print("Failure parsing at line number", idx)
                print(e)
                # skip over broken part
                idx += 1
                continue

            # check configuration of json_dict
            if "bg" in json_dict:

                # print(idx, timestamp, cob, iob)
                line_array.append(idx)
                timestamp_array.append(timestamp)
                bg_array.append(json_dict['bg'])
                if "sensitivityRatio" in json_dict:
                    sens_array.append(json_dict['sensitivityRatio'])
                else:
                    sens_array.append(np.nan)
                cob_array.append(float(json_dict['COB']))
                iob_array.append(float(json_dict['IOB']))
                if "rate" in json_dict:
                    rate_array.append(json_dict['rate'])
                else:
                    rate_array.append(np.nan)
                if "units" in json_dict:
                    bolus_array.append(json_dict['units'])
                else:
                    bolus_array.append(np.nan)
                json_length_array.append(jdx - idx)
                # continue searching for enact success iff rate or units found
                tb_success_array.append(np.nan)
                smb_success_array.append(np.nan)
                if "rate" in json_dict:
                    # assume failure, search for success
                    tb_success_array[-1] = 0
                if "units" in json_dict:
                    # assume failure, search for success
                    smb_success_array[-1] = 0
                if "rate" in json_dict or "units" in json_dict:
                    # search for pump_events: "239 - DEV: New pump events:"
                    while (jdx < numLines-2) and (jdx < (line_0+max_lines-2)):
                        jdx += 1
                        # if the next json string happens before New pump event
                        # break out of loop
                        if determBasal_patt in lines_raw[jdx]:
                            idx = jdx
                            break
                        if lines_raw[jdx].find(pump_events) > -1:
                            mdx = jdx
                            while mdx-jdx < pe_num:
                                # Medtronic Format:
                                if lines_raw[mdx][:11] == "Bolus units":
                                    smb_success_array[-1] = 1
                                    # print("SMB mdx, lines_raw: ", mdx, ", ",
                                    #      lines_raw[mdx])
                                # Omnipod Format:
                                if lines_raw[mdx][:6] == "Bolus:":
                                    smb_success_array[-1] = 1
                                    # print("SMB mdx, lines_raw: ", mdx, ", ",
                                    #      lines_raw[mdx])
                                if lines_raw[mdx][:9] == "TempBasal":
                                    tb_success_array[-1] = 1
                                    # print(" TB mdx, lines_raw: ", mdx, ", ",
                                    #      lines_raw[mdx])
                                mdx += 1
                            break
            else:
                # print("json_dict missing bg, skipping")
                printDict(json_dict)
            idx = jdx
        else:
            idx = idx+1
            thisLine = lines_raw[idx]

    # finished the entire lines_raw list, create the data frame
    d = {'date_time': timestamp_array, 'line#': line_array,
         'BG': bg_array, 'COB': cob_array, 'IOB': iob_array,
         'Bolus': bolus_array, 'Basal': rate_array,
         'SensRatio': sens_array, 'num_json_lines': json_length_array,
         'TB_Success': tb_success_array, 'SMB_Success': smb_success_array}
    determBasalDF = pd.DataFrame(d)
    # split the time into a new column, use for plots 0 to 24 hour
    time_array = pd.to_datetime(determBasalDF['date_time']).dt.time
    determBasalDF['time'] = time_array

    return determBasalDF


def extract_messages(recordType, parsed_content):
    # set up default
    logDF = pd.DataFrame({})
    noisy = 0
    pod_messages = ['nil']
    if recordType == "messageLog":
        # only pod messages are found in this section of the Loop Report
        pod_messages = [message_dict(m) for m in parsed_content['MessageLog']]
    elif recordType == "deviceLog":
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
        return logDF

    # logDF all pod messages in Report (can be across multiple pods)
    logDF = pd.DataFrame(pod_messages)
    logDF['time'] = pd.to_datetime(logDF['time'])
    logDF['deltaSec'] = (logDF['time'] -
                         logDF['time'].shift()
                         ).dt.seconds.fillna(0).astype(float)

    return logDF
