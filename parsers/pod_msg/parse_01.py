from util.misc import combineByte
from util.misc import versionString


def parse_01(byteList, msgDict):
    # pod response to 0x07 or 0x03
    """
    My example:
        # 0x07 response:
        msg = '011502090002090002010000aecb0006df6ea61f0747ca037c'
        # 0x03 response:
        msg = '011b13881008340a5002090002090002030000aecb0006df6e1f0747ca0208'

    Response 01 message with mlen $15 is returned from 07 Command Assign ID:

        OFF 1  2 3 4  5 6 7  8  9 10111213 14151617 18 19202122
        01 15 MXMYMZ IXIYIZ ID 0J LLLLLLLL TTTTTTTT GS IIIIIIII

        01 (1 byte) [0]: mtype value of 01 specifies Version Response command
        15 (1 byte) [1]: mlen of $15 is this format (the 07 Command response)
        MXMYMZ (3 bytes) [2:4]: PM MX.MY.MZ
        IXIYIZ (3 bytes) [5:7]: PI IX.IY.IZ
        ID (1 byte) : always 2 for Eros
                    : always 4 for Dash
        0J (1 byte) [9]: Pod Progress State, typically 02, but possibly 01
        LLLLLLLL (4 bytes) [$A:$D]: Pod Lot
        TTTTTTTT (4 bytes) [$E:$11]: Pod TID
        GS (1 byte) [$12]: ggssssss where
                 gg = two bits of receiver gain, ssssss = 6 bits of rssi value
        IIIIIIII (4 bytes) [$13:$16]: ID (Pod address) as given by 07 Command

    Response 01 message with mlen $1b is returned from 03 Command Setup Pod:

        OFF 1  2 3 4 5 6 7 8  91011 121314 15 16 17181920 21222324 25262728
        01 1b 13881008340A50 MXMYMZ IXIYIZ ID 0J LLLLLLLL TTTTTTTT IIIIIIII

        01 (1 byte) [0]: mtype value of 01 specifies Version Response command
        1b (1 byte) [1]: mlen of $1b is this format (the 03 Command response)
        13881008340A50 (7 bytes) [2:8]: fixed byte sequence of unknown meaning
        MXMYMZ (3 bytes) [9:$B]: PM MX.MY.MZ
        IXIYIZ (3 bytes) [$C:$E]: PI IX.IY.IZ
        ID (1 byte) : always 2 for Eros
                    : always 4 for Dash
        0J (1 byte) [9]: Pod Progress State, should be 03 for this response
        LLLLLLLL (4 bytes) [$11:$14]: Pod Lot
        TTTTTTTT (4 bytes) [$15:$18]: Pod TID
        IIIIIIII (4 bytes) [$19:$1C]: Connection ID (Pod address)
    """

    # put place holders for msgDict values I want near beginning
    msgDict['pod_progress'] = -1  # will be overwritten
    msgDict['podAddr'] = 'tbd'  # will be overwritten

    if byteList[1] == 0x15:
        msgDict['msgMeaning'] = 'IdAssigned'
        pmVer = byteList[2:5]
        piVer = byteList[5:8]
        podType = byteList[8]
        pprog = byteList[9]
        podLot = combineByte(byteList[10:14])
        podTid = combineByte(byteList[14:18])
        gS = byteList[18]
        podAddr = combineByte(byteList[19:23])
        # mask gS
        gg = gS & 0xC0 >> 6
        ss = gS & 0x3F
        msgDict['msgType'] = '0x0115'
        msgDict['recvGain'] = gg
        msgDict['rssiValue'] = ss
    elif byteList[1] == 0x1b:
        msgDict['msgMeaning'] = 'PodSetupOK'
        fixedWord = byteList[2:9]
        pmVer = byteList[9:12]
        piVer = byteList[12:15]
        podType = byteList[15]
        pprog = byteList[16]
        podLot = combineByte(byteList[17:21])
        podTid = combineByte(byteList[21:25])
        podAddr = combineByte(byteList[25:29])
        msgDict['msgType'] = '0x011b'
        msgDict['fixedWord'] = fixedWord

    # fill in rest of common msgDict
    msgDict['podType'] = podType
    msgDict['pmVersion'] = versionString(pmVer)
    msgDict['piVersion'] = versionString(piVer)
    msgDict['pod_progress'] = pprog
    msgDict['lot'] = podLot
    msgDict['tid'] = podTid
    msgDict['podAddr'] = hex(podAddr)

    return msgDict
