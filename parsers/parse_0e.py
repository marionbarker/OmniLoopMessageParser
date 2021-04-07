def parse_0e(byteList, msgDict):
    # request status from the pod
    """
    My examples:
     msg = '0e010002c6'
        0e 01 TT checksum
        0e 01 00 0079

    byte TT: request type
        $00 1D Status Response - Request standard status
        $01 02 Response, Type 1 - expired alert status
        $02 02 Response, Type 2 - fault event information
        $03 02 Response, Type 3 - contents of data log
        $05 02 Response, Type 5 - fault information with Pod init time
        $06 02 Response, Type 6 - hardcoded values
        $46 02 Response, Type 46 - flash variables including state,
                                   initialization time, any faults
        $50 02 Response, Type 50 - dumps up to 50 entries from the flash log
        $51 02 Response, Type 51 - like Type $50,  dumps entries before last 50
    """

    requestCode = byteList[2]

    msgDict['requestCode'] = '{0:#0{1}x}'.format(requestCode, 4)
    if requestCode == 0:
        msgDict['msgMeaning'] = 'RequestStatus'
    elif requestCode == 1:
        msgDict['msgMeaning'] = 'RequestAlert'
    elif requestCode == 2:
        msgDict['msgMeaning'] = 'RequestFault'
    else:
        msgDict['msgMeaning'] = 'requestCode' + msgDict['requestCode']

    return msgDict
