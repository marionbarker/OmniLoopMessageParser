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
# from util.misc import combineByte
from util.misc import printDict, printList
# from parsers.messagePatternParsing import processMsg
from parsers.fx_extract_raw_functions import extract_raw_pod
from parsers.fx_extract_raw_functions import extract_raw_determBasal
from parsers.fx_extract_raw_functions import extract_raw_determTdd
from parsers.fx_extract_raw_functions import extract_raw_TDD
# add for FAPSX files
import os
import subprocess
import numpy as np
import json
import tempfile
## as part of reorg

from parsers.splitFullMsg import splitFullMsg


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
    # remove < which breaks one line into two (in the soup section later)
    content = content.replace('<', '')

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
    return data



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
    #   2022-04-12 21:43:00 +0000 Omnipod-Dash 171EFBEA connection Pod \
    #         connected 6B0595EC-B6B6-E8D6-FF0E-2B2E75C2876D

    timestamp = data[0:19]
    # skip the UTC time delta characters ( +0000 ), logs are always in UTC
    stringToUnpack = data[26:]

    # extract common information, parse Omnipod, other devices ignored for now
    # note that address is ffffffff until Loop and Pod finish some init steps
    device, logAddr, action, restOfLine = stringToUnpack.split(' ', 3)
    # ensure Omnipod and either send or receive (ignore other keywords for now)
    podCommsMessage = (device[0:7] == "Omnipod" and
                       (action == "send" or action == "receive"))
    if podCommsMessage:
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
    determTddDF_old = pd.DataFrame({})
    determTddDF_tcd = pd.DataFrame({})
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
                    'determBasalDF': determBasalDF,
                    'determTddDF_old': determTddDF_old,
                    'determTddDF_tcd': determTddDF_tcd}

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
        # read version from old version and evaluate new versionq
        determTddDF_old = extract_raw_determTdd(raw_content)
        determTddDF_tcd = extract_raw_TDD(raw_content)

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
                    'determBasalDF': determBasalDF,
                    'determTddDF_old': determTddDF_old,
                    'determTddDF_tcd': determTddDF_tcd}

    return loopReadDict


def omnipodP(message):
    thisIsAPodCommsMessage = message['device'][0:7] == "Omnipod" and \
        (message['type'] == "send" or message['type'] == "receive")
    return thisIsAPodCommsMessage


def otherP(message):
    thisIsAPodCommsMessage = message['device'][0:7] == "Omnipod" and \
        ((message['type'] == "send") or (message['type'] == "receive"))
    return not thisIsAPodCommsMessage


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
        # and in April 2022, the omnipod messages need more filtering
        # search for address then send and seceive explicitly.
        #   address connection has been added already.
        #   Pete warns more keywords may be coming.
        messages = [device_message_dict(m)
                    for m in parsed_content['Device Communication Log']]
        pod_messages = list(filter(omnipodP, messages))
        if noisy:
            print('\n Pod Comm Messages')
            printList(pod_messages[1:5])
            printList(pod_messages[-5:-1])

        # this works - use it later if desired
        if noisy:
            print('\n Not Pod Comm Messages')
            cgm_messages = list(filter(otherP, messages))
            printList(cgm_messages[1:5])
            printList(cgm_messages[-5:-1])
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
