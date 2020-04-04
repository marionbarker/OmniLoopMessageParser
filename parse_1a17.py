# file: parse_1a17 - does the parsing for bolus commond
from utils import *
from utils_pod import *
from decimal import Decimal

def parse_1a17(msg):
    # extract information from the 1a13 basal command << to be updated - this is a copy of 1a16
    """
    This is the combination of two messages
    Note that for parsing the TB from Loop - we only need to do one fixed-rate,
        half-hour segment.  So OK to cheat here
    Treat it as one master list
      Example: '1a0e1b8fd9f70201ab01089000890089170d00055a00030d400000000000008359'

         First:   1a 0e 1b8fd9f7 02 01ab 01 0890 0089 0089
        Second:   17 0d 00 055a00 030d4000 0000 0000008359

    First half:   1a LL NNNNNNNN 02 CCCC HH SSSS PPPP 0ppp [napp...]  17...
        1a (1 byte): Mtype value of $1a specifies a generic insulin schedule command
        LL (1 byte): Length, == $0e for normal bolus & >= $10 for extended bolus
        NNNNNNNN (4 bytes): Nonce, the 32-bit validator (random looking numbers)
        02 (1 byte): TableNum of $02 specifies this is a bolus command
        CCCC (2 bytes): CheckSum, is the sum of the bytes in the following 3
            fields along with the bytes
            in the generated insulin schedule table
        HH (1 byte): Duration, # of resulting Half Hour entries always 1 for Loop (no extended bolus)
        SSSS (2 bytes):PPPP times $10 (for a standard two seconds between
                       pulse immediate bolus) or times 8 (for an one second
                       between pulse bolus during Pod startup)
        PPPP (2 bytes): Pulses, # of pulses to deliver in the first half hour segment
            napp [napp...] (2 bytes per element)
    Second half:  17 LL RR NNNN XXXXXXXX YYYY ZZZZZZZZ
        The 0x17 command is the follow-on command for the Command 0x1A Table 2
        case to deliver either a normal and/or an extended bolus.
        This command always immediately follows the 0x1A command with Table 2
             (bolus case) in the same message.

        The generic format of the 0x17 bolus follow-on command for a command 1A Table 2 bolus is:

            17 LL RR NNNN XXXXXXXX YYYY ZZZZZZZZ

        17 (1 byte): Mtype value of $17 specifies bolus follow-on command for a 1A command Table 2. is the follow-on command for a 1A command Table 2 (bolus)
        LL (1 byte): Length of the following bytes for this command, always $0d
        RR (1 byte): Reminder bits acrrrrrr (typical PDM values $00, $3c, $40 and $7c):
          a bit ($80) for Acknowledgement beep (command received), not used by PDM
          c bit ($40) for Confidence Reminder beeps (start and end of delivery)
          rrrrrr (6 bits) # of minutes ($3c = 60 minutes) between Program Reminder beeps
        NNNN (2 bytes): # of 0.05U pulses x 10
        XXXXXXXX (4 bytes): delay in 100 kHz to start of delivery, minimum value of $30D40 = 200,000 (2 seconds) during normal Pod use and minimum value of $186A0 = 100,000 (1 second) during Pod startup.
        YYYY (2 bytes): # of 0.05U pulses x 10 to deliver for extended bolus interval
        ZZZZZZZZ (4 bytes): delay interval in 100 kHz between pulses for extended bolus interval
        NNNN will be 0 if there is no immediate bolus. YYYY and ZZZZZZZZ will both be 0 if there is no extended bolus. For an extended bolus, XXXXXXXX and ZZZZZZZZ values have a minimum value of 0x30d40 (=200,000 decimal, i.e., 2 seconds between pulses) and a maximum value of 0x6b49d200 (=1,800,000,000 decimal, i.e., 5 hours between pulses).

        The XXXXXXXX and ZZZZZZZZ values have a minimum value of 0x30d40
        (=200,000 decimal, i.e., 2 seconds between pulses) and a maximum value
        of 0x6b49d200 (=1,800,000,000 decimal, i.e., 5 hours between pulses).
    """
    #              0  1  2        6  7    9  10   12   14
    #First half:   1a LL NNNNNNNN 02 CCCC HH SSSS PPPP 0ppp [napp...]  17...
    msgDict = { }
    msgDict['message_type'] = '1a17'
    msgDict['raw_value']    = msg

    byteMsg = bytearray.fromhex(msg)
    byteList = list(byteMsg)
    mtype = byteList[0]
    mlen = byteList[1]
    nonce = combineByte(byteList[2:6])
    TableNum = byteList[6]
    chsum   = combineByte(byteList[7:9])
    hhsegments = byteList[9]
    secsX8Left = combineByte(byteList[10:12])
    hhpulses = combineByte(byteList[12:14])
    pulse0   = combineByte(byteList[14:16])
    # only immediate bolus used by Loop - so done with first half

    #              16 17 18 19   21       25   27
    #Second half:  17 LL RR NNNN XXXXXXXX YYYY ZZZZZZZZ
    xtype = byteList[16]
    xlen = byteList[17]
    reminders = byteList[18]
    promptTenthPulses = combineByte(byteList[19:21])
    promptDelay = combineByte(byteList[21:25])
    extendedTenthPulses = combineByte(byteList[25:27])
    extendedDelay = combineByte(byteList[27:31])

    if extendedTenthPulses != 0:
        print('Warning - bolus not properly configured, extended pulses not 0')

    msgDict = { }
    msgDict['message_type'] = '1a17'
    msgDict['raw_value']    = msg
    msgDict['mtype'] = mtype
    msgDict['mlen'] = mlen
    msgDict['nonce'] = nonce
    msgDict['TableNum'] = TableNum
    msgDict['chsum'] = chsum
    msgDict['hhsegments'] = hhsegments
    msgDict['secsX8Left'] = secsX8Left
    msgDict['hhpulses'] = hhpulses
    msgDict['pulse0'] = pulse0

    msgDict['xtype'] = xtype
    msgDict['xlen'] = xlen
    msgDict['reminders'] = reminders
    msgDict['promptTenthPulses'] = promptTenthPulses
    msgDict['promptDelay'] = promptDelay
    msgDict['extendedTenthPulses'] = extendedTenthPulses
    msgDict['extendedDelay'] = extendedDelay

    msgDict['prompt_bolus_u']  =  getUnitsFromPulses(hhpulses)

    return msgDict
