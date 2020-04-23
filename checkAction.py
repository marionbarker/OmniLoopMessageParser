from utils import *
from utils_pd import *
from utils_pod import *
import numpy as np

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
        Steps:
            # - identify the indices associated with initilizing the pod
                (use pod_progress < 8) plus next 0x1d messages
            # - build up actionFrame
                (note that incompleteList remain in frameBalance)
                frameBalance = frame
                for each item in actionDict
                    * find prime-indices for action, e.g., for 'TB' find all '1a16'
                    * check adjacent indices for correct message types
                    * incorrect adjacency => prime-index into incompleteList
                    * the completedList includes prime + adjacent msg indices
                    * fill in the actionFrame row for these column headers
                    ['actionName', 'msgPerAction', 'cumStartSec', 'responseTime', \
                        'SchBasalState', 'incompleteList', 'completedList']
                    frameBalance = frame.drop(completedList)
    """

    actionDict = getActionDict()

    actionColumnNames = ('actionName', 'msgPerAction', 'cumStartSec', \
      'responseTime' , 'SchBasalState', 'incompleteList','completedList' )

    # determine initIdx from pod_progress value
    podInit = frame[frame.pod_progress < 8]
    # get list of indices for initializing the pod
    # note when first message is a send, no pod_progress state is set
    initIdx = np.array(podInit.index.to_list())
    if initIdx[-1] == 0:
        initIdx = [];
    else:
        # need to add the next row too - but keep going until it is a '0x1d'
        checkIdx = initIdx[-1]
        while checkIdx<len(frame) and (frame.loc[checkIdx,'msg_type']) != '0x1d':
            checkIdx += 1
            initIdx = np.append(initIdx, checkIdx)

    if len(initIdx) > len(frame):
        print('Pod never reached pod_progress of 8')
        #print('len(initIdx):', len(initIdx))
        #print('len(frame):', len(frame))
        initIdx = initIdx[0:len(frame)]
        #print('len(initIdx):', len(initIdx))
        actionFrame = pd.DataFrame([], columns=actionColumnNames)
        return actionFrame, initIdx

    # prepare to search by actions
    frameBalance = frame.copy()

    # now search the frame for actions:
    #    actionName from actionDic
    #    list of lists of the completedList for that action,
    #             e.g., (34, 35, 36, 37), (60, 61, 62, 63)
    #    responseTime calculated by taking timeCumSec at end - timeCumSec at end
    #    SchBasal is the scheduled basal state at the beginning of the action
    # if all the expected messages are found in the correct order, then the
    #     indices for all the messages are removed from frameBalance before
    #     searching for the next actionDict item

    actionList = []

    for keys,values in actionDict.items():
        badIdx = []         # accumulate action identifier indices that don't have all their messages
        incompleteList = [] # list of badIdx lists by action
        thisAction = keys
        thisID = values[0]           # used to index into matchList, identifier for Action
        matchList = values[1]
        msgPerAction = len(matchList)  # always 2 or 4
        thisFrame = frameBalance[frameBalance.msg_type == matchList[thisID]]
        if len(thisFrame) == 0:
            continue
        thisIdx = np.array(thisFrame.index.to_list())
        # go thru adjacent messages to ensure they match the matchList
        for ii in range (-thisID, msgPerAction-thisID):
            if ii == thisID:
                # we already know it matches the ID for this action
                continue
            thisList = thisIdx+ii
            # to avoid missing indices already removed from frameBalance, use frame here
            checkFrame=frame.loc[thisList,:]
            # identify any mismatches with respect to action message
            badFrame = checkFrame[checkFrame.msg_type != matchList[ii+thisID]]
            if len(badFrame) > 0:
                thisBad = np.array(badFrame.index.to_list())
                thisBad = thisBad-ii
                badIdx  = np.append(badIdx, thisBad)

        # all required messages in the action have now been checked
        if len(badIdx):
            # need to remove the "bad" aka incomplete action indices from thisIdx
            badIdx = np.unique(badIdx)
            incompleteList = thisFrame.loc[badIdx,'df_idx'].to_list()
            # use thisFrame to transfer completed indices in next step
            thisFrame = thisFrame.drop(badIdx)

        # now work on success
        idx = np.array(thisFrame.index.to_list())
        if len(idx) == 0:
            continue

        #print('Status: ', thisAction, 'Complete: ', len(idx), 'Incomplete: ', len(badIdx))

        if msgPerAction == 4:
            thisList = np.unique(flatten([idx-2, idx-1, idx, idx+1 ]))
            t0 = np.array(frame.loc[idx-2,'timeCumSec'].to_list())
            t1 = np.array(frame.loc[idx+1,'timeCumSec'].to_list())
            responseTime = t1-t0
            SchBasalState = frame.loc[idx-2,'SchBasal'].to_list()
        else:
            thisList = np.unique(flatten([idx, idx+1]))
            t0 = np.array(frame.loc[idx,'timeCumSec'].to_list())
            t1 = np.array(frame.loc[idx+1,'timeCumSec'].to_list())
            responseTime = t1-t0
            SchBasalState = frame.loc[idx,'SchBasal'].to_list()

        # append this action to the list
        # go from np.array to list as appropriate
        actionList.append(( thisAction, msgPerAction, t0, \
          responseTime, SchBasalState, incompleteList, thisList))

        # remove these indices from the frameBalance, reset and keep going
        frameBalance = frameBalance.drop(thisList)

    actionFrame = pd.DataFrame(actionList, columns=actionColumnNames)
    return actionFrame, initIdx

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
        subDict = { \
          'msgPerAction': row['msgPerAction'], \
          'countCompleted': numCompleted, \
          'countIncomplete': numIncomplete, \
          'meanResponseTime': np.mean(respTime), \
          'minResponseTime':  np.min(respTime), \
          'maxResponseTime': np.max(respTime) }
        # for Temp Basal, add a few more items to the subDict
        if thisName == 'CnxSetTmpBasal':
            startTime = row['cumStartSec']
            deltaTime = np.diff(startTime)
            deltaTime = list(deltaTime)
            # insert 399 as the first index result for timeSinceLastTB
            deltaTime[:0] = [399]
            timeSinceLastTB = np.array(deltaTime)
            numShortTB = np.sum(timeSinceLastTB<30)
            numSchBasalbeforeTB = np.sum(row['SchBasalState'])
            SchBasalState = row['SchBasalState']
            completedList = row['completedList']
            # find TB that are enacted while SchBasalState is false
            # with initial TB and final TB the same value
            priorIdx   = list(range(0,len(completedList), 4)) # current status before cancel
            postIdx    = list(range(2, len(completedList), 4)) # req TB
            priorReqTB = np.array(podState.loc[completedList[priorIdx]]['reqTB'])
            postReqTB  = np.array(podState.loc[completedList[postIdx]]['reqTB'])
            deltaReqTB = postReqTB - priorReqTB
                # by definition, prior and post TB are same, so only need to include one value along with time
            repeatedTB = [x[2:6] for x in zip(SchBasalState, deltaReqTB, startTime, priorReqTB, completedList[postIdx], timeSinceLastTB) if (not x[0] and x[1]==0)]
            subDict['numShortTB'] = numShortTB
            subDict['numSchBasalbeforeTB'] = numSchBasalbeforeTB
            subDict['numRepeatedTB'] = len(repeatedTB)
            subDict['repeatedTB'] = repeatedTB
            repeatedShortTB = [x[2:6] for x in zip(SchBasalState, deltaReqTB, startTime, priorReqTB, completedList[postIdx], timeSinceLastTB) if (not x[0] and x[1]==0 and x[5]<30)]
            subDict['numRepeatedShortTB'] = len(repeatedShortTB)
            subDict['repeatedShortTB'] = repeatedShortTB
            # in practice - there were many repeated TB that were just under 20 min, so change to 19 min
            repeated19MinTB = [x[2:6] for x in zip(SchBasalState, deltaReqTB, startTime, priorReqTB, completedList[postIdx], timeSinceLastTB) if (not x[0] and x[1]==0 and (x[5]>=30 and x[5]<1140))]
            subDict['numrepeated19MinTB'] = len(repeated19MinTB)
            subDict['repeated19MinTB'] = repeated19MinTB
            ## new dictionary items start here - don't change any old ones
            # Each of these is cummulative, e.g., lt30 - lt10 yield # between 10 and 30s
            repeatedTBlt10s = [x[2:6] for x in zip(SchBasalState, deltaReqTB, startTime, priorReqTB, completedList[postIdx], timeSinceLastTB) if (not x[0] and x[1]==0 and x[5]<10)]
            subDict['numrepTBlt10s'] = len(repeatedTBlt10s)
            repeatedTBlt20s = [x[2:6] for x in zip(SchBasalState, deltaReqTB, startTime, priorReqTB, completedList[postIdx], timeSinceLastTB) if (not x[0] and x[1]==0 and(x[5]>=10 and x[5]<20))]
            subDict['numrepTBlt20s'] = len(repeatedTBlt20s)
            repeatedTBlt30s = [x[2:6] for x in zip(SchBasalState, deltaReqTB, startTime, priorReqTB, completedList[postIdx], timeSinceLastTB) if (not x[0] and x[1]==0 and (x[5]>=20 and x[5]<30))]
            subDict['numrepTBlt30s'] = len(repeatedTBlt30s)
            repeatedTBlt05m = [x[2:6] for x in zip(SchBasalState, deltaReqTB, startTime, priorReqTB, completedList[postIdx], timeSinceLastTB) if (not x[0] and x[1]==0 and (x[5]>=30 and x[5]<300))]
            subDict['numrepTBlt05m'] = len(repeatedTBlt05m)
            repeatedTBlt10m = [x[2:6] for x in zip(SchBasalState, deltaReqTB, startTime, priorReqTB, completedList[postIdx], timeSinceLastTB) if (not x[0] and x[1]==0 and (x[5]>=300 and x[5]<600))]
            subDict['numrepTBlt10m'] = len(repeatedTBlt10m)
            repeatedTBlt15m = [x[2:6] for x in zip(SchBasalState, deltaReqTB, startTime, priorReqTB, completedList[postIdx], timeSinceLastTB) if (not x[0] and x[1]==0 and (x[5]>=600 and x[5]<900))]
            subDict['numrepTBlt15m'] = len(repeatedTBlt15m)
            repeatedTBlt20m = [x[2:6] for x in zip(SchBasalState, deltaReqTB, startTime, priorReqTB, completedList[postIdx], timeSinceLastTB) if (not x[0] and x[1]==0 and (x[5]>=900 and x[5]<1200))]
            subDict['numrepTBlt20m'] = len(repeatedTBlt20m)
            repeatedTBlt30m = [x[2:6] for x in zip(SchBasalState, deltaReqTB, startTime, priorReqTB, completedList[postIdx], timeSinceLastTB) if (not x[0] and x[1]==0 and (x[5]>=1200 and x[5]<1800))]
            subDict['numrepTBlt30m'] = len(repeatedTBlt30m)

        actionSummary[thisName] = subDict

    return actionSummary, totalCompletedMessages
