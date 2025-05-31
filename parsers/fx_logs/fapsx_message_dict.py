"""
fapsx_message_dict.py
"""

from parsers.pod_msg.splitFullMsg import splitFullMsg


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