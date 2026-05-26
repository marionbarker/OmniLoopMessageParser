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

import re
import pandas as pd
import markdown
import numpy as np
from bs4 import BeautifulSoup, NavigableString, Tag
#
from parsers.fx_logs.extract_raw_pod import extract_raw_pod
from parsers.fx_logs.extract_raw_determBasal import extract_raw_determBasal
from parsers.fx_logs.extract_raw_determTdd import extract_raw_determTdd
from parsers.fx_logs.extract_raw_TDD import extract_raw_TDD
from parsers.pod_msg.splitFullMsg import splitFullMsg
from parsers.pod_connect.extract_pod_connect_time import extract_pod_connect_time
from util.misc import printDict
from util.misc import printList


# Some markdown headings don't start on their own line. This regular expression
# finds them so we can insert a newline. (Needed for some MessageLog files)
FIXME_RE = re.compile(r'(?!#).(##+.*)')

# Markdown headings we want to extract from the .md report
# Handle case where last line of messageLog is 'status: ##'
# Add new ## PodInfoFaultEvent markdown heading
# Add new ## Device Communication Log markdown heading:
#  note it's either MessageLog or Device Communication Log
MARKDOWN_HEADINGS_TO_EXTRACT = ['OmnipodPumpManager', 'OmniBLEPumpManager',
                                'OmniPumpManager',
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


def _is_valid_pod_hex(logAddr, hexData):
    """Return True if hexData is a valid omnipod message, not O5 BLE handshaking.

    Valid messages satisfy one of:
      - logAddr is 'noPod'         (initial pairing broadcast, hex is ffffffff)
      - hex starts with ffffffff   (address negotiation frames)
      - hex starts with the pod address  (normal pod messages)

    O5 BLE handshaking has hex that matches none of the above and must be excluded.
    """
    if logAddr == 'noPod':
        return True
    hexPrefix = hexData[:8].lower()
    if hexPrefix == 'ffffffff':
        return True
    if hexPrefix == logAddr.lower():
        return True
    return False


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
    # split(None, 3) handles variable whitespace, e.g. "noPod    send" alignment
    device, logAddr, action, restOfLine = stringToUnpack.split(None, 3)
    # ensure Omni and either send or receive (ignore other keywords for now)
    #   Omnipod (from OmniKit), Omnipod-DASH (from OmniBLE), Omni (from OmnipodKit)
    podCommsMessage = (device[0:4] == "Omni" and
                       (action == "send" or action == "receive") and
                       _is_valid_pod_hex(logAddr, restOfLine))
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
    # set up default (only Loop provides this)
    podMgrDict = {}
    # OmnipodPumpManger: reported by OmniKit
    if data.get('OmnipodPumpManager'):
        try:
            podMgrDict = dict([[x.strip() for x in v.split(':', 1)]
                              for v in data['PodState']])
        except ValueError:
            print('Information Only: PodState not defined in log file')
    # OmniBLEPumpManager: reported by OmniBLE
    elif data.get('OmniBLEPumpManager'):
        try:
            podMgrDict = dict([[x.strip() for x in v.split(':', 1)]
                              for v in data['PodState']])
        except ValueError:
            print('Information Only: PodState not defined in log file')
    # OmniPumpManager: reported by OmnipodKit
    elif data.get('OmniPumpManager'):
        try:
            podMgrDict = dict([[x.strip() for x in v.split(':', 1)]
                              for v in data['PodState']])
        except ValueError:
            print('Information Only: PodState not defined in log file')
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


def omnipodP(message):
    # msgDict is empty when _is_valid_pod_hex rejected the message (e.g. O5
    # BLE handshaking) — exclude those even though device/type look like Omni.
    thisIsAPodCommsMessage = message['device'][0:4] == "Omni" and \
        (message['type'] == "send" or message['type'] == "receive") and \
        bool(message['msgDict'])
    return thisIsAPodCommsMessage


def otherP(message):
    thisIsAPodCommsMessage = message['device'][0:4] == "Omni" and \
        ((message['type'] == "send") or (message['type'] == "receive"))
    return not thisIsAPodCommsMessage


def connectP(message):
    # note connection is associated with connected or disconnected message
    # error is found with special debug version used for iPhone 16 tests
    thisIsAPodConnectMessage = message['device'][0:4] == "Omni" and \
        ((message['type'] == "connection") or (message['type'] == "error"))
    return thisIsAPodConnectMessage

def extract_messages(recordType, parsed_content, raw_content):
    # set up default
    logDF = pd.DataFrame({})
    noisy = 0
    pod_messages = ['nil']
    pod_connect_messages = ['nil']

    if recordType == "messageLog":
        # only pod messages are found in this section of the Loop Report
        pod_messages = [message_dict(m) for m in parsed_content['MessageLog']]
    elif recordType == "deviceLog":
        # pod messages interleaved with CGM messages in this Loop Report
        # and in April 2022, the omnipod messages need more filtering
        # search for address then send and seceive explicitly.
        #   address connection has been added already.
        #   Pete warns more keywords may be coming.

        # in 2025 July - need to evaluate reconnect times with InPlay BLE pods
        # for this, we need raw_content (with current dumb search method)
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
