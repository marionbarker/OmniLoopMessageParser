def getPodInitCmdCount(initFrame):
    """
    Purpose: count commands in initialization attempt
             Return gain and rssi from pod 0x0115 if available
             along with other items in podInitCmdCount dictionary

    Input:
        initFrame: DataFrame limited to initialization messages

    Output:
       podInitCmdCount       message counts and other information
       podInitState         0 if pod_progress does not reach 8
                            1 if pod_progress reaches 8

    """
    # initialize values for podInitCmdCount and podInitState
    podInitState = 0
    podInitCmdCount = {
        'timeStamp': initFrame.loc[0]['timeStamp'],
        'deltaSec': initFrame.loc[0]['deltaSec'],
        'recvGain': -1,
        'rssiValue': -1,
        'podAddr': 'n/a',
        'podType': 0,
        'podStyle': 'Unkn',
        'pmVersion': 0,
        'piVersion': 0,
        'lot': 0,
        'tid': 0,
        'PP115': 0,
        'lastPP': 0,
        'numInitSteps': len(initFrame),
        'cnt07': 0,
        'cnt03': 0,
        'cnt08': 0,
        'cnt19': 0,
        'cnt1a17': 0,
        'cnt1a13': 0,
        'cnt0e': 0,
        'cntACK': 0,
        'cnt0115': 0,
        'cnt011b': 0,
        'cnt1d': 0}

    # keep track of number of each type of message expected during pod init
    # (ack is not desired, but does happen)
    # for certain messages, update other dictionary values

    # iterate through initFrame
    for index, row in initFrame.iterrows():
        # reset each time
        timeStamp = row['timeStamp']
        deltaSec = row['deltaSec']
        msgDict = row['msgDict']

        # now modify what happens based on msgType
        if msgDict['msgType'] == '0x07':
            podInitCmdCount['cnt07'] += 1

        elif msgDict['msgType'] == '0x0115':
            podInitCmdCount['cnt0115'] += 1
            podInitCmdCount['timeStamp'] = timeStamp
            podInitCmdCount['deltaSec'] = deltaSec
            podInitCmdCount['PP115'] = msgDict['pod_progress']
            podInitCmdCount['recvGain'] = msgDict['recvGain']
            podInitCmdCount['rssiValue'] = msgDict['rssiValue']
            podInitCmdCount['podType'] = msgDict['podType']
            if podInitCmdCount['podType'] == 2:
                podInitCmdCount['podStyle'] = 'Eros'
            elif podInitCmdCount['podType'] == 4:
                podInitCmdCount['podStyle'] = 'Dash'
            else:
                podInitCmdCount['podStyle'] = 'Unkn'
            podInitCmdCount['pmVersion'] = msgDict['pmVersion']
            podInitCmdCount['piVersion'] = msgDict['piVersion']
            podInitCmdCount['lot'] = msgDict['lot']
            podInitCmdCount['tid'] = msgDict['tid']
            podInitCmdCount['podAddr'] = msgDict['podAddr']

        elif msgDict['msgType'] == '0x03':
            podInitCmdCount['cnt03'] += 1
            podInitCmdCount['podAddr'] = msgDict['podAddr']

        elif msgDict['msgType'] == '0x011b':
            podInitCmdCount['cnt011b'] += 1
            podInitCmdCount['pmVersion'] = msgDict['pmVersion']
            podInitCmdCount['piVersion'] = msgDict['piVersion']
            podInitCmdCount['lot'] = msgDict['lot']
            podInitCmdCount['tid'] = msgDict['tid']
            podInitCmdCount['podAddr'] = msgDict['podAddr']

        elif msgDict['msgType'] == 'ACK':
            podInitCmdCount['cntACK'] += 1

        elif msgDict['msgType'] == '0x08':
            podInitCmdCount['cnt08'] += 1

        elif msgDict['msgType'] == '0x1d':
            podInitCmdCount['cnt1d'] += 1
            podInitCmdCount['lastPP'] = msgDict['pod_progress']

        elif msgDict['msgType'] == '0x19':
            podInitCmdCount['cnt19'] += 1

        elif msgDict['msgType'] == '0x1a17':
            podInitCmdCount['cnt1a17'] += 1

        elif msgDict['msgType'] == '0x1a13':
            podInitCmdCount['cnt1a13'] += 1

        elif msgDict['msgType'] == '0x0e':
            podInitCmdCount['cnt0e'] += 1

        # all possible initialzation messages have been counted
        if podInitCmdCount['lastPP'] == 8:
            podInitState = 1

    return podInitCmdCount, podInitState
