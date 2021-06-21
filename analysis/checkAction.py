from util.misc import flatten
from util.pod import getActionDict
import numpy as np
import pandas as pd


def checkAction(frame):
    """
    Purpose: Perform an improved check on the podState dataframe

    Input:
        frame       output from getPodState function

    Output:
        actionFrame  dataframe of processed analysis from podState (by action)
        initIdx      indices in podState to extract pod initilization

    Method:
        actionFrame is a dataframe with indices and times for every action
        Uses the actionDict for which send-recv patterns go with actions

        on 6/21/2020 - check for time before message for 4-msg sequences
                       and keep track of uncategorized items

        Steps:
            # - identify the indices associated with initilizing the pod
                (use pod_progress < 8) plus next 0x1d messages
            # - build up actionFrame
                (note that incompleteList remain in frameBalance)
                frameBalance = frame
                for each item in actionDict
                    * find prime-indices for action, e.g., 'TB' find  '1a16'
                    * check adjacent indices for correct message types
                    * incorrect adjacency => prime-index into incompleteList
                    * the completedList includes prime + adjacent msg indices
                    * fill in the actionFrame row for these column headers
                    ['actionName', 'msgPerAction', 'cumStartSec',
                        'responseTime', 'SchBasalState', 'incompleteList',
                        'completedList']
                    frameBalance = frame.drop(completedList)
    """

    actionDict = getActionDict()
    # initialize frameBalance
    frameBalance = frame

    actionColumnNames = ('actionName', 'msgPerAction', 'cumStartSec',
                         'responseTime', 'SchBasalState', 'incompleteList',
                         'completedList')

    # determine if a 4-message sequence should be grouped together
    maxDeltaInSeq = 10  # seconds - phone responds quicker than pod
    # determine initIdx from pod_progress value
    podInit = frame[frame.pod_progress < 8]
    # get list of indices for initializing the pod
    initIdx = np.array(podInit.index.to_list())
    if len(initIdx) == 0 or initIdx[-1] == 0:
        initIdx = []
    # note assumed pod_progress state is 0 until first recv message from pod
    elif len(initIdx) < len(frame) and \
            frame.loc[initIdx[-1], 'type'] == 'send' and \
            frame.loc[initIdx[-1], 'pod_progress'] == 0 and \
            frame.loc[initIdx[-1]+1, 'pod_progress'] >= 8:
        initIdx = []
    else:
        # need to add the next row too - but keep going until it is a '0x1d'
        checkIdx = initIdx[-1]
        while checkIdx < len(frame) and \
                (frame.loc[checkIdx, 'msgType']) != '0x1d':
            checkIdx += 1
            initIdx = np.append(initIdx, checkIdx)

    if len(initIdx) > len(frame):
        print('    *** Pod never reached pod_progress of 8')
        initIdx = initIdx[0:len(frame)]
        actionFrame = pd.DataFrame([], columns=actionColumnNames)
        return actionFrame, initIdx, frameBalance

    # prepare to search by actions
    frameBalance = frame.copy()

    # now search the frame for actions:
    #    actionName from actionDic
    #    list of lists of the completedList for that action,
    #             e.g., (34, 35, 36, 37), (60, 61, 62, 63)
    #    responseTime calculated by taking
    #        timeCumSec at end - timeCumSec at end
    #    SchBasal is the scheduled basal state at the beginning of the action
    #    if all the expected messages are found in the correct order,
    #     then the indices for all the messages are removed from frameBalance
    #     before searching for the next actionDict item
    #     for 4-step sequences, deltaTime for 3rd time in list <= maxDeltaInSeq
    #  Now that some of these 4-step sequences can be performed as 2-step
    #     sequences because upper-level logic can decide if it already knows
    #     knows the pod state. Must add a check for 0 as first value for any
    #     sequence where it's going to back up in array.

    actionList = []

    for keys, values in actionDict.items():
        # accumulate action identifier indices that don't have all messages
        badIdx = []
        incompleteList = []  # list of badIdx lists by action
        thisAction = keys
        thisID = values[0]   # index into matchList, identifier for Action
        matchList = values[1]
        msgPerAction = len(matchList)  # always 2 or 4
        if msgPerAction == 2:
            thisFrame = frameBalance[frameBalance.msgType == matchList[thisID]]
        else:
            # add time check for 4-msg sequences
            thisFrame = frameBalance[
                         (frameBalance.msgType == matchList[thisID]) &
                         (frameBalance.deltaSec <= maxDeltaInSeq)]
        if len(thisFrame) == 0:
            continue
        thisIdx = np.array(thisFrame.index.to_list())
        # extract the 4-msg sequences first,
        #   but some have same index command as 2-msg sequences
        #   protect against 0 index in matching command for those cases
        if ((thisIdx[0] < 2) and (thisID == 2)):
            thisIdx = np.delete(thisIdx, 0)
            badIdx = np.append(badIdx, 0)
        # go thru adjacent messages to ensure they match the matchList
        for ii in range(-thisID, msgPerAction-thisID):
            if ii == thisID:
                # we already know it matches the ID for this action
                continue
            thisList = thisIdx + ii
            # use frame here to avoid missing indices already removed
            checkFrame = frame.loc[thisList, :]
            # identify any mismatches with respect to action message
            badFrame = checkFrame[checkFrame.msgType != matchList[ii + thisID]]
            if len(badFrame) > 0:
                thisBad = np.array(badFrame.index.to_list())
                thisBad = thisBad - ii
                badIdx = np.append(badIdx, thisBad)

        # all required messages in the action have now been checked
        if len(badIdx):
            # remove the "bad" (incomplete) action indices from thisIdx
            badIdx = np.unique(badIdx)
            incompleteList = thisFrame.loc[badIdx, 'logIdx'].to_list()
            # use thisFrame to transfer completed indices in next step
            thisFrame = thisFrame.drop(badIdx)

        # now work on success
        idx = np.array(thisFrame.index.to_list())
        if len(idx) == 0:
            continue

        if msgPerAction == 4:
            thisList = np.unique(flatten([idx - 2, idx - 1, idx, idx + 1]))
            t0 = np.array(frame.loc[idx-2, 'timeCumSec'].to_list())
            t1 = np.array(frame.loc[idx+1, 'timeCumSec'].to_list())
            responseTime = t1 - t0
            SchBasalState = frame.loc[idx-2, 'SchBasal'].to_list()
        else:
            thisList = np.unique(flatten([idx, idx + 1]))
            t0 = np.array(frame.loc[idx, 'timeCumSec'].to_list())
            t1 = np.array(frame.loc[idx+1, 'timeCumSec'].to_list())
            responseTime = t1 - t0
            SchBasalState = frame.loc[idx, 'SchBasal'].to_list()

        # append this action to the list
        # go from np.array to list as appropriate
        actionList.append((thisAction, msgPerAction, t0, responseTime,
                           SchBasalState, incompleteList, thisList))

        # remove these indices from the frameBalance, reset and keep going
        frameBalance = frameBalance.drop(thisList)

    actionFrame = pd.DataFrame(actionList, columns=actionColumnNames)
    return actionFrame, initIdx, frameBalance


def processActionFrame(actionFrame, podState):
    """
       8/11/2019:
           For calling function Rev4, add more dictionary items
           This should not affect Rev3, which doesn't refer to new items
    """
    if len(actionFrame) == 0:
        return
    actionSummary = {}
    totalCompletedMessages = 0
    numShortTB = np.nan
    numSchBasalbeforeTB = np.nan
    for index, row in actionFrame.iterrows():
        respTime = row['responseTime']
        totalCompletedMessages += len(row['completedList'])
        numCompleted = len(row['completedList'])/row['msgPerAction']
        numIncomplete = len(row['incompleteList'])
        thisName = row['actionName']
        subDict = {
          'msgPerAction': row['msgPerAction'],
          'countCompleted': numCompleted,
          'countIncomplete': numIncomplete,
          'meanResponseTime': np.mean(respTime),
          'minResponseTime':  np.min(respTime),
          'maxResponseTime': np.max(respTime)}
        # for Temp Basal, add a few more items to the subDict
        if thisName == 'CnxSetTmpBasal':
            startTime = row['cumStartSec']
            deltaTime = np.diff(startTime)
            deltaTime = list(deltaTime)
            # insert 399 as the first index result for timeSinceLastTB
            deltaTime[:0] = [399]
            timeSinceLastTB = np.array(deltaTime)
            numShortTB = np.sum(timeSinceLastTB < 30)
            numSchBasalbeforeTB = np.sum(row['SchBasalState'])
            SchBasalState = row['SchBasalState']
            completedList = row['completedList']
            # find TB that are enacted while SchBasalState is false
            # with initial TB and final TB the same value
            # current status before cancel
            priorIdx = list(range(0, len(completedList), 4))
            # req TB
            postIdx = list(range(2, len(completedList), 4))
            priorReqTB = np.array(podState.loc[completedList
                                  [priorIdx]]['reqTB'])
            postReqTB = np.array(podState.loc[completedList[postIdx]]['reqTB'])
            deltaReqTB = postReqTB - priorReqTB
            # by definition, prior and post TB are same,
            # so only need to include one value along with time
            repeatedTB = [x[2:6]
                          for x in zip(SchBasalState, deltaReqTB, startTime,
                                       priorReqTB, completedList[postIdx],
                                       timeSinceLastTB)
                          if (not x[0] and x[1] == 0)]
            subDict['numShortTB'] = numShortTB
            subDict['numSchBasalbeforeTB'] = numSchBasalbeforeTB
            subDict['numRepeatedTB'] = len(repeatedTB)
            subDict['repeatedTB'] = repeatedTB
            repeatedShortTB = [x[2:6]
                               for x in zip(SchBasalState, deltaReqTB,
                                            startTime, priorReqTB,
                                            completedList[postIdx],
                                            timeSinceLastTB)
                               if (not x[0] and x[1] == 0 and x[5] < 30)]
            subDict['numRepeatedShortTB'] = len(repeatedShortTB)
            subDict['repeatedShortTB'] = repeatedShortTB
            # in practice - there were many repeated TB that were
            # code - has been fixed - this is archaic - may drop after reorg
            # just under 20 min, so change to 19 min
            repeated19MinTB = [x[2:6]
                               for x in zip(SchBasalState, deltaReqTB,
                                            startTime, priorReqTB,
                                            completedList[postIdx],
                                            timeSinceLastTB)
                               if (not x[0] and x[1] == 0 and
                                   (x[5] >= 30 and x[5] < 1140))]
            subDict['numrepeated19MinTB'] = len(repeated19MinTB)
            subDict['repeated19MinTB'] = repeated19MinTB
            # delete all the other time parses - Loop works now

        actionSummary[thisName] = subDict

    return actionSummary, totalCompletedMessages
