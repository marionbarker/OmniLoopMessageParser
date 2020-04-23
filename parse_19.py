# file: parse_19 - is a request to configure alerts for the pod
#  wiki: https://github.com/openaps/openomni/wiki/Command-19-Configure-Alerts

from utils import *

def parse_19(msg):
    """
    Command $19 can used to configure a number of different alerts.
    This command is used multiple times during initial setup and for
    various other configuration situations like changing the Low Reservoir
    or Replace Pod Soon alerts and for Confidence Reminders.
    The $19 command can also follow a Command 1F Cancel-Request,
    when the user issues a suspend.

    19 LL NNNNNNNN IVXX YYYY 0J0K [IVXX YYYY 0J0K]...

        19 (1 byte): Mtype of $19 specifies a Configure Alerts Command
        LL (1 byte): Length of command (typically $0a, $10 or $16)
        NNNNNNNN (4 bytes): Nonce, the 32-bit validator (random looking numbers)
        IVXX (2 bytes): bit format 0iiiabcx xxxxxxxx as follows:
            0iii is the 3-bit alert #. In the $1D Status Response aaaaaaaa bits and
                 in the TT byte of the $02 Pod Information Response Type 2,
                 active, unacknowledged alerts are returned as a bit mask (1 << alert #).
            The a ($0800) bit being set indicates that this alert is active.
            The b ($0400) bit being set indicates that this alert is for setting
                a low reservoir alert and a not time based alert.
            The c ($0200) bit being set indicates that this alert is for the Auto-Off function.
            x xxxxxxxx is a 9-bit value for the alert duration in minutes
        YYYY (2 bytes): 14-bit alert value
            If b bit is 0, YYYY is the number of minutes from now before
                alerting, maximum value 4,800 (i.e., 80 hours).
            If b bit is 1, YYYY is the number of units for low reservoir
                alert x 10 (i.e., the # of 0.05U pulses / 2),
                maximum value 500 (i.e., 50U x 10).
        0J0K (2 bytes): 12-bit beep word consisting of two bytes 0J and 0K.
            The J nibble is a beep repeat pattern value:
                0 - Beep once
                1 - Beep every minute for 3 minutes and repeat every 60 minutes
                2 - Beep every minute for 15 minutes
                3 - Beep every minute for 3 minutes and repeat every 15 minutes
                4 - Beep at 2, 5, 8, 11, ... 53, 56, 59 minutes
                5 - Beep every 60 minutes
                6 - Beep every 15 minutes
                7 - Beep at 14, 29, 44 and 59 minutes
                8 - Beep every 5 minutes
            The K nibble is a beep type value from 0 (silent) to 8 as given in Beep types:
                0 - No Sound
                1 - BeepBeepBeepBeep
                2 - BipBeep BipBeep BipBeep BipBeep
                3 - BipBip
                4 - Beep
                5 - BeepBeepBeep
                6 - Beeeeeep
                7 - BipBipBip BipBipBip
                8 - BeeepBeeep
    The three-word entries can be repeated an arbitrary number of times for
        setting multiple alerts with the same $19 command.
        The command length LL for a single alert $19 command is $0a,
        for a double alert $19 command is $10, and
        for a triple alert $19 command is $16.
    """

    byteMsg = bytearray.fromhex(msg)
    byteList = list(byteMsg)
    mtype = byteList[0]
    mlen = byteList[1]
    nonce = combineByte(byteList[2:6])

    msgDict = { }
    msgDict['msg_type'] = '{0:#0{1}x}'.format(mtype,4)
    msgDict['msg_body']    = msg
    msgDict['mtype'] = mtype
    msgDict['mlen'] = mlen
    msgDict['nonce'] = nonce
    msgDict['msgMeaning'] = 'cnfgAlerts'

    return msgDict
