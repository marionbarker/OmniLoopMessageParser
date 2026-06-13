"""
fapsx_message_dict.py
"""

from datetime import datetime, timezone
from parsers.pod_msg.splitFullMsg import splitFullMsg


def fapsx_message_dict(data):
    # extract dateTtime from beginning of line and convert to UTC
    # Trio format: 2026-06-07T00:00:24-0500 (24 chars with timezone offset)
    try:
        dt = datetime.strptime(data[:24], '%Y-%m-%dT%H:%M:%S%z')
        timestamp = dt.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, IndexError):
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