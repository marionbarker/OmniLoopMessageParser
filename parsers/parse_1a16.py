# file: parse_1a16 - does the parsing a temporary basal commond
from util.misc import combineByte
from decimal import Decimal


def parse_1a16(byteList, msgDict):
    # extract information from the 1a16 temporary basal command
    """
    This is the combination of two messages
    Note that for parsing the TB from Loop - we only need to do one fixed-rate,
        half-hour segment.  So OK to cheat here
    Treat it as one master list
      Example:
        1a0e726545dd0100a301384000150015160e000000d7007fbf7d00d7007fbf7d02bc
      First:  1a 0e 726545dd 01 00a3 01 3840 0015 0015
      Second: 16 0e 00 00 00d7 007fbf7d 00d7 007fbf7d  checksum: 02bc
    First half:   1a LL NNNNNNNN 01 CCCC HH SSSS PPPP napp [napp...]  16...
        1a (1 byte): Mtype value of $1a specifies insulin schedule command
        LL (1 byte): Length of following bytes
        NNNNNNNN (4 bytes): Nonce, the 32-bit validator
        01 (1 byte): TableNum of $01 specifies this is a temp basal command
        CCCC (2 bytes): CheckSum, is the sum of the bytes in the following 3
            fields along with the bytes
            in the generated insulin schedule table
        HH (1 byte): Duration, # of resulting Half Hour entries in resulting
            temp basal insulin schedule table
        SSSS (2 bytes): SecsX8Left,
                        $3840 (=14,400 dec = 30 x 60 x 8) for fixed rates
        PPPP (2 bytes): Pulses, # of pulses to deliver in the first
                        half hour segment
            napp [napp...] (2 bytes per element):
                One or more InsulinScheduleElements describe temp basal rates
    Second half:  16 LL RR MM NNNN XXXXXXXX YYYY ZZZZZZZZ [YYYY ZZZZZZZZ...]
        16 mtype
        LL length of message in bytes
        RR Reminder bits acrrrrrr
            a Acknowledgement beep
            c Confidence Reminder beeps
            rrrrrr # of minutes ($3c = 60 minutes) between Reminder beeps
        MM  Always 0
        NNNN Remaining 1/10th of a 0.05u pulse of insulin to deliver
            for first entry (i.e., # of pulses x 10).
            NNNN must be <= the first YYYY value, for fixed rate temp basal
            it will be same as the only YYYY value.
        XXXXXXXX (4 bytes): Delay until next 1/10th of a 0.05u pulse,
            expressed in microseconds.
            XXXXXXXX must be <= the first ZZZZZZZZ value
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
    #              0  1  2        6  7    9  10   12   14
    # First half:   1a LL NNNNNNNN 01 CCCC HH SSSS PPPP napp [napp...]  16...

    msgDict['msgMeaning'] = 'SetTempBasal'
    mlen = byteList[1]
    # use mlen to determine when the 16 follow on command starts
    # two values are 14 (0x0e) or 16 (0x10)
    msgDict['nonce'] = hex(combineByte(byteList[2:6]))
    TableNum = byteList[6]
    chsum = hex(combineByte(byteList[7:9]))
    hhEntries = byteList[9]  # number of half hr entries, max is 24 = 12 hrs
    secsX8Left = combineByte(byteList[10:12])  # always 0x3840 for a 1/2 hr temp basal
    pulsesPerHhr = combineByte(byteList[12:14])   # pulses per half hr segment
    # TODO - fix this section
    # if mlen == 0x0e:
    #    numHalfHrSegs = 1  # all we expect with Loop
    #    # ignore first napp - always indicate 1 half hour segment
    # elif mlen == 0x10:
    #    napp1 = combineByte(byteList[14:16])
    #    napp2 = combineByte(byteList[16:18])
    #    numHalfHrSegs = 10 # place holder, get from masking napp1 + napp2
    # else:
    #    print('mlen is not valid in msg')
    #    print(msg)
    #    return msgDict

    # count below is true iff mlen is 0x0e
    #              16 17 18 19 20   22       26   28
    # Second half:  16 LL RR MM NNNN XXXXXXXX YYYY ZZZZZZZZ [YYYY ZZZZZZZZ...]
    xtype = byteList[2+mlen]
    xlen = byteList[3+mlen]
    reminders = byteList[4+mlen]
    MM = byteList[5+mlen]   # Always 0
    firstEntryX10pulses = combineByte(byteList[(6+mlen):(8+mlen)])
    firstDelayMicroSec = combineByte(byteList[(8+mlen):(12+mlen)])
    totalEntryX10pulses = combineByte(byteList[(12+mlen):(14+mlen)])
    delayMicroSec = combineByte(byteList[(14+mlen):(18+mlen)])

    # These values are always the same from the PDM
    # if firstEntryX10pulses != totalEntryX10pulses:
    #    print('Warning - temp basal not properly configured, # pulses')
    #
    # if firstDelayMicroSec != delayMicroSec:
    #    print('Warning - temp basal not properly configured, # microsec')

    msgDict['TableNum'] = TableNum
    msgDict['chsum'] = chsum
    msgDict['hhEntries'] = hhEntries
    msgDict['secsX8Left'] = secsX8Left
    msgDict['pulsesPerHhr'] = pulsesPerHhr
    msgDict['pulsesPerHhr'] = pulsesPerHhr

    msgDict['xtype'] = xtype
    msgDict['xlen'] = xlen
    msgDict['reminders'] = reminders
    msgDict['always0'] = MM
    msgDict['firstEntryX10pulses'] = firstEntryX10pulses
    msgDict['firstDelayMicroSec'] = firstDelayMicroSec
    msgDict['totalEntryX10pulses'] = totalEntryX10pulses
    msgDict['delayMicroSec'] = delayMicroSec

    msgDict['pulses_in_TB_halfHr'] = 0.1 * totalEntryX10pulses
    # u per pulse * half hours per hour * number of pulses = rate u/hr
    basalRate = Decimal(0.05 * 2 * 0.1 * totalEntryX10pulses)
    x = round(basalRate, 2)
    msgDict['temp_basal_rate_u_per_hr'] = float(x)

    return msgDict
