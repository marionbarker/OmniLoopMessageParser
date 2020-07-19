# file: parse_06 - is a request of a nonce resync returned from the pod

from util.misc import combineByte


def parse_06(byteList, msgDict):
    # pod response - indicates a nonce resync is required
    """
    My example:
     msg = '060314217881e4'
        06 03 EE WWWW checksum
        06 03 14 2178 81e4

    A Pod 06 response typically indicates the PDM sent a bad nonce
     (PDM intentionally sends a fake nonce at each time it awakes).
    The PDM and Pod will both start a new nonce sequence to get back in sync
    and the PDM will try the request again with a new nonce.

    06 03 EE WWWW
    06 (1 byte): mtype of this response is 06
    03 (1 byte): mlen for this response is always 03
    EE (1 byte): error code, typically $14 for bad nonce;
                 other values indicate a fault event
    WWWW (2 bytes): interpretation depends on EE value
        if EE == $14: encoded value indicating offset for new nonce sequence
        if EE != $14: logged event byte followed by a Pod progress byte (0..$F)
        For EE == $14 case, WWWW is a word value encoded with formula:
            (LSB Word of FakeNonce + crc16_table[Message sequence number] +
            (LSB word)Lot + (LSB word)TID) ^ NewSeed

    NewSeed can be extracted knowing the other parameters
      (Lot, TID, MessageSeq, FakeNonce)
    """

    errorCode = byteList[2]
    wordCode = combineByte(byteList[3:5])

    msgDict['is_nonce_resync'] = errorCode == 0x14
    if msgDict['is_nonce_resync']:
        msgDict['nonce_reseed_word'] = wordCode
        msgDict['fault_code'] = 'nonceResync'
        msgDict['msgMeaning'] = 'ResyncNonceOK'
    else:
        msgDict['nonce_reseed_word'] = 0
        msgDict['fault_code'] = hex(errorCode)
        msgDict['msgMeaning'] = 'ResyncNonceNotOK'

    return msgDict
