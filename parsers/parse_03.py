# file: parse_03 - setup pod, follows successful 07 (assignID) and 0x0115 response
#  wiki: https://github.com/openaps/openomni/wiki/Command-03-Setup-Pod

from utils import *

def parse_03(byteList, msgDict):
    # Command to pod to finish initialization of address, TID, Lot
    """
    My example:
        # 0x03 setup pod from Loop:
        msg = '03131f09f876140404011401290000b0c100077c0e'

        O  1  2 3 4 5  6  7  8 910 1112 [13141516 17181920]
        03 LL IIIIIIII NU TO MMDDYY HHMM [LLLLLLLL TTTTTTTT]

    03 (1 byte) [0]: mtype value of 03 specifies Setup Pod command
    LL (1 byte) [1]: mlen $13 for typical case or $0b
    IIIIIIII (4 bytes) [2:5]: Pod ID as given in the 07 Command
    NU (1 byte) [6]: Not Used
    TO (1 byte) [7]: Packet Timeout Limit (max 50, 0 sets the default value of 4)
    MMDDYY (3 bytes) [8:$A]: MM: month (1-12), DD: day (1-31), YY: years since 2000
    HHMM (2 bytes) [$B:$C]: HH: hour (0-23), MM minutes (0-59)
    LLLLLLLL (4 bytes) [$D:$10]: Lot (long format only)
    TTTTTTTT (4 bytes) [$11:$14]: TID (long format only)
    """

    msgDict['msgMeaning'] = 'setupPod'

    if byteList[1] != 0x13:
        print('Unexpected length of 0x03 command for Loop')
        return msgDict

    podAddr = combineByte(byteList[2:6])
    timeOut = byteList[7]
    MM = byteList[8]
    DD = byteList[9]
    YY = byteList[10]
    hh = byteList[11]
    mm = byteList[12]
    podLot = combineByte(byteList[13:17])
    podTid = combineByte(byteList[17:21])

    msgDict['podAddr']  = hex(podAddr)
    msgDict['timeOut']  = timeOut
    msgDict['dateStamp']  = '{0:#0{1}d}'.format(MM,2) + '/' + \
                            '{0:#0{1}d}'.format(DD,2) + '/' + \
                            '20{0:#0{1}d}'.format(YY,2) + ' ' + \
                            '{0:#0{1}d}'.format(hh,2) + ':' + \
                            '{0:#0{1}d}'.format(mm,2)
    msgDict['lot']  = podLot
    msgDict['tid']  = podTid

    return msgDict
