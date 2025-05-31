# splitFullMsg.py

from util.misc import combineByte
from parsers.pod_msg.messagePatternParsing import processMsg


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

        Must put protection here for FAX (Trio/iAPS) log files

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

