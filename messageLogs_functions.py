# file contains all the functions required to analyze the MessageLogs portion of the Loop Reports .md files
# import requests # not found on local machine python
import time
#import matplotlib.pyplot as plt
#import matplotlib.dates as dates
#from matplotlib.dates import DateFormatter
#from pandas.plotting import register_matplotlib_converters
import re
import pandas as pd
import os
import markdown
from bs4 import BeautifulSoup, NavigableString, Tag
import re

# Some markdown headings don't start on their own line. This regular expression
# finds them so we can insert a newline.
FIXME_RE = re.compile(r'(?!#).(##+.*)')

# Markdown headings we want to extract from the .md report
# Handle case where last line of messageLog is 'status: ##'
# Add new ## PodInfoFaultEvent markdown heading
# was:
#    MARKDOWN_HEADINGS_TO_EXTRACT = ['OmnipodPumpManager', 'MessageLog', 'PodState', 'PodInfoFaultEvent']
# is:
MARKDOWN_HEADINGS_TO_EXTRACT = ['OmnipodPumpManager', 'MessageLog', 'PodState', 'PodInfoFaultEvent', 'Device Communication Log']


def _parse_filehandle(filehandle):
    """Given a filehandle, extract the content from below markdown headings.

    Args:
       filehandle: a python file object
    Returns:
       A dict of markdown heading -> list of text from that heading
    """
    content = filehandle.read()
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

def _command_dict(data):
    timestamp, direction, value = data.rsplit(' ', 2)
    return dict(time=timestamp, type=direction, raw_value=value[12:])

def _device_command_dict(data):
    # split from left to determine if omnipod line
    date, timestamp, UTCDelta, device, theRestOfLine = data.split(' ', 4)
    if device=="Omnipod":
        timestamp, device, address, direction, value = data.rsplit(' ', 4)
        value = value[12:]  # strip off first 12 characters
    else:
        address = theRestOfLine[:6];
        direction = 'other';
        value = theRestOfLine[6:];
    return dict(time=timestamp, device=device, address=address, type=direction, raw_value=value)

def _extract_pod_state(data):
    return dict([[x.strip() for x in v.split(':', 1)]
            for v in data['PodState']])

def read_file(filename):
    # set up defaults while building new parser
    commands = ['testing']
    pod_dict = ['testing']
    fault_report = []
    file = open(filename, "r", encoding='UTF8')
    parsed_content = _parse_filehandle(file)
    # can use .get('name') or if 'name' in parsed_content
    if parsed_content.get('MessageLog'):
      print('The file has MessageLog, calling _command_dict')
      tmp = parsed_content['MessageLog'][-1]
      if tmp=='status:':
          parsed_content['MessageLog'] = parsed_content['MessageLog'][:-1]
      commands = [_command_dict(m) for m in parsed_content['MessageLog']]
    if parsed_content.get('OmnipodPumpManager'):
      print('The file has OmnipodPumpManager')
      pod_dict = _extract_pod_state(parsed_content)
    if parsed_content.get('Device Communication Log'):
      print('The file has Device Communication Log, calling _device_command_dict')
      commands = [_device_command_dict(m) for m in parsed_content['Device Communication Log']]
    if 'PodInfoFaultEvent' in parsed_content:
         fault_report = parsed_content['PodInfoFaultEvent']
    else:
         fault_report = []
    return commands, pod_dict, fault_report

def select_extra_command(raw_value):
    if raw_value[:2]=='1a':
        if raw_value[32:34] not in ['16','17']:
            return 13
        else:
            return raw_value[32:34]

def generate_table(commands, radio_on_time):
    # convert to a pandas dataframe
    dfAll = pd.DataFrame(commands)
    # remove any commands where type is "other" to handle the new Device Communication Log
    df = dfAll[dfAll.type != 'other']
    df['time'] = pd.to_datetime(df['time'])
    df['command'] = df['raw_value'].str[:2].astype(str)+df['raw_value'].apply(select_extra_command).fillna('').astype(str)
    df['time_delta'] = (df['time']-df['time'].shift()).dt.seconds.fillna(0).astype(float)
    df['time_asleep'] = df['time_delta'].loc[df['time_delta'] > radio_on_time] - radio_on_time  # radio_on_time seconds the radio stays awake
    return df

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
