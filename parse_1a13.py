# file: parse_1a13 - does the parsing for basal commond to set scheduled rates
from utils import *
from decimal import Decimal

def parse_1a13(msg):
    # extract information from the 1a13 basal command
    """
    This is the combination of two messages
    But because the basal schedule probably pretty complicated, will cheat

    First Half: 1a LL NNNNNNNN 00 CCCC HH SSSS PPPP napp napp napp [napp...]  13...
        1a (1 byte): Mtype value of $1a specifies a generic insulin schedule command
        LL (1 byte): Length of following bytes
        NNNNNNNN (4 bytes): Nonce, the 32-bit validator (random looking numbers)
        00 (1 byte): TableNum of $00 specifies this is a basal schedule command
        CCCC (2 bytes): CheckSum, is the sum of the bytes in the following 3
            fields along with the bytes
            in the generated insulin schedule table
        HH (1 byte): Current Half Hour of the day (0 to 47)
        SSSS (2 bytes): SecsX8Left until end of hour hour (max $3840)(=14,400 dec = 30 x 60 x 8) for fixed rates
        PPPP (2 bytes): Pulses, # of pulses to deliver in this half hour
        napp napp napp etc: 2 bytes per napp element of the basal table
          n+1 half hour entries
          a   adds extra pulse alternate half hours
          pp  number of pulses in the schedule
    Second half:  13 LL RR MM NNNN XXXXXXXX YYYY ZZZZZZZZ [YYYY ZZZZZZZZ ...]
        13 mtype
        LL length of message in bytes
        RR Reminder bits acrrrrrr
            a Acknowledgement beep
            c Confidence Reminder beeps
            rrrrrr # of minutes ($3c = 60 minutes) between Program Reminder beeps
        MM  Number of schedule entries
        NNNN Remaining 1/10th of a 0.05u pulse of insulin to deliver
            for first entry (i.e., # of pulses x 10).
            NNNN must be <= the first YYYY value, for fixed rate temp basal
            it will be same as the only YYYY value.
        XXXXXXXX (4 bytes): Delay until next 1/10th of a 0.05u pulse,
            expressed in microseconds. XXXXXXXX must be <= the first ZZZZZZZZ value
        YYYY (2 bytes): Total 1/10th of a 0.05u pulses of insulin for this
            schedule entry (i.e., # of pulses x 10).
        ZZZZZZZZ (4 bytes): Delay between 1/10th of a 0.05u pulse, expressed in
            microseconds. Example: 1.0 U/hr = 20 pulses per hour = 3 min
            (180 secs) between pulses = 18 secs for 1/10th of a pulse =
            18,000,000 uS = 0x112a880

    The XXXXXXXX and ZZZZZZZZ values have a minimum value of 0x30d40
    (=200,000 decimal, i.e., 2 seconds between pulses) and a maximum value
    of 0x6b49d200 (=1,800,000,000 decimal, i.e., 5 hours between pulses).
    """
    #              0  1  2        6  7    9  10   12   14   15 ... to mlen
    #First half:   1a LL NNNNNNNN 00 CCCC HH SSSS PPPP napp napp  13...
    byteMsg = bytearray.fromhex(msg)
    byteList = list(byteMsg)
    mtype = byteList[0]
    mlen = byteList[1]
    nonce = combineByte(byteList[2:6])
    TableNum = byteList[6]
    chsum   = combineByte(byteList[7:9])
    currentHH = byteList[9]
    secsX8Left = combineByte(byteList[10:12])
    hhpulses = combineByte(byteList[12:14])
    nappArray = combineByte(byteList[14:mlen])

    #
    #Second half:  13 LL RR MM NNNN XXXXXXXX YYYY ZZZZZZZZ [YYYY ZZZZZZZZ ...]
    xtype = byteList[mlen+2]
    xlen = byteList[mlen+3]
    reminders = byteList[mlen+4]
    scheduleEntryIndex = byteList[mlen+5]

    msgDict = { }
    msgDict['msg_type'] = '1a13'
    msgDict['msg_body']    = msg
    msgDict['mtype'] = mtype
    msgDict['mlen'] = mlen
    msgDict['nonce'] = nonce
    msgDict['TableNum'] = TableNum
    msgDict['chsum'] = chsum
    msgDict['currentHH'] = currentHH
    msgDict['secsX8Left'] = secsX8Left
    msgDict['hhpulses'] = hhpulses
    msgDict['nappArray'] = hex(nappArray)

    msgDict['xtype'] = xtype
    msgDict['xlen'] = xlen
    msgDict['reminders'] = reminders
    msgDict['scheduleEntryIndex'] = scheduleEntryIndex

    return msgDict
