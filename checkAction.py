from utils import *
from podUtils import *
import numpy as np

def checkAction(frame):
    """
    Purpose: Perform an improved check on the podState dataframe
             (will replace getPodSuccessfulActions)

    Input:
        frame: output from getPodState code

    Output:
        a series of podState frames segregated by action or error
        use the actionDict for which send-recv patterns go with actions

        First identify (and remove from frameBalance): Fault, Nonce, Empty messages
        Then go thru actionDict in order, identify indices that match pattern,
            then remove those from frameBalance and go onto next
    """
    actionDict, nonce, fault = getActionDict()

    # first identify fault, if present
    frFault = frame[frame.message_type==fault]
    faultIdx = frFault.index.to_list()

    # remove the fault for further analysis
    frameBalance = frame.drop(faultIdx)

    # search for nonce frames, then check for the prior message
    nonceFrame = frameBalance[frameBalance.message_type==nonce]
    nonceIdx = np.array(nonceFrame.index.to_list())
    # send-recv before and after the nonce replies
    nonceList = np.unique(flatten([nonceIdx, nonceIdx-1, nonceIdx+1]))
    nonceFrame = frame.loc[nonceList]
    # drop just the send/nonce values for next analysis
    nonceDropList = np.unique(flatten([nonceIdx, nonceIdx-1]))

    frameBalance = frameBalance.drop(nonceDropList)

    # select just the init sequences
    podInit = frameBalance[frameBalance.pod_progress < 8]
    # get list of indices for initializing the pod
    initIdx = podInit.index.to_list()
    # need to add the next row too - but need to protect that it wasn't removed with nonce drop
    checkIdx = initIdx[-1]+1
    while checkIdx in nonceDropList:
        checkIdx += 1
    initIdx.append(checkIdx)
    podInit = frame.iloc[initIdx,:]

    frameBalance = frameBalance.drop(initIdx)
    podRun = frameBalance

    # prepare to search by actions

    # now search the balance for actions:
    #    actionName from actionDic
    #    list of lists of the df_idx for that action,
    #             e.g., (34, 35, 36, 37), (60, 61, 62, 63)
    #    responseTime calculated by taking timeCumSec at end - timeCumSec at end
    #    SchBasal is the scheduled basal state at the beginning of the action
    # if all the expected messages are found in the correct order, then the
    #     indices for all the messages are removed from frameBalance before
    #     searching for the next actionDict item
    successColumnNames = ('actionName', 'msgPerAction', 'cumStartSec', 'responseTime' , 'SchBasalState', 'failureList','df_idx' )

    actionList = []

    for keys,values in actionDict.items():
        badIdx = []      # used for each message that is part of the action
        removeIdx = []   # used for the entire action
        failureList = [] # convert list to df_idx
        thisAction = keys
        thisID = values[0]           # used to index into matchList, identifier for Action
        matchList = values[1]
        msgPerAction = len(matchList)  # always 2 or 4
        thisFrame = frameBalance[frameBalance.message_type == matchList[thisID]]
        if len(thisFrame) == 0:
            continue
        idx = np.array(thisFrame.index.to_list())
        # go thru adjacent messages to ensure they match the matchList
        for ii in range (-thisID, msgPerAction-thisID):
            if ii == thisID:
                # we already know if matches the ID for this action
                continue
            thisList = idx+ii
            checkFrame=frameBalance.loc[thisList,:]
            # identify any mismatches with respect to action message
            badFrame = checkFrame[checkFrame.message_type != matchList[ii+thisID]]
            if len(badFrame) > 0:
                thisBad = badFrame.index.values
                thisBad = thisBad-ii
                badIdx.append(thisBad)

        # all required messages in the action have now been checked
        if len(badIdx):
            removeIdx = np.unique(flatten(badIdx))
            failureList = thisFrame.loc[removeIdx,'df_idx'].to_list()
            thisFrame = thisFrame.drop(removeIdx)

        # now work on success
        idx = np.array(thisFrame.index.to_list())
        if len(idx) == 0:
            continue

        # print('Status: ', thisAction, 'Success for ', len(idx), 'Failures for ', len(removeIdx))

        if msgPerAction == 4:
            thisList = np.unique(flatten([idx-2, idx-1, idx, idx+1 ]))
            t0 = np.array(frameBalance.loc[idx-2,'timeCumSec'].to_list())
            t1 = np.array(frameBalance.loc[idx+1,'timeCumSec'].to_list())
            responseTime = t1-t0
            SchBasalState = frameBalance.loc[idx-2,'SchBasal'].to_list()
        else:
            thisList = np.unique(flatten([idx, idx+1]))
            t0 = np.array(frameBalance.loc[idx,'timeCumSec'].to_list())
            t1 = np.array(frameBalance.loc[idx+1,'timeCumSec'].to_list())
            responseTime = t1-t0
            SchBasalState = frameBalance.loc[idx,'SchBasal'].to_list()
        # We need to return the df_idx index, not the reset values
        dfIdxList = frameBalance.loc[thisList,'df_idx'].to_list()

        # append this action to the list
        actionList.append(( thisAction, msgPerAction, t0, responseTime, SchBasalState, failureList, dfIdxList))

        # remove these indices from the frameBalance, reset and keep going
        frameBalance = frameBalance.drop(thisList)

    actionFrame = pd.DataFrame(actionList, columns=successColumnNames)
    return podRun, actionFrame, podInit, nonceFrame, frFault


def printActionFrame(actionFrame):
    if len(actionFrame) == 0:
        return
    print('\n  Action Summary with sequential 2 or 4 message sequences. Response times in sec')
    print('      Action         : #Success, mean, [ min, max ]   : #Failed  : SchBasalRunning(beforeTB), #<30Sec Long ')
    for index, row in actionFrame.iterrows():
        if row['actionName'] == 'TB':
            respTime = row['responseTime']
            startTime = row['cumStartSec']
            deltaTime = startTime[1:-1]-startTime[0:-2]
            numLT30secDelta = np.sum(deltaTime<30)
            print('    {:14s}   : {:5.0f}, {:5.1f}, [ {:5.1f}, {:5.1f} ] : {:5d}    :  {:5d}, {:5d}'.format( \
              row['actionName'], len(row['df_idx'])/row['msgPerAction'], \
              np.mean(respTime), np.min(respTime), np.max(respTime), \
              len(row['failureList']), np.sum(row['SchBasalState']), numLT30secDelta))
        else:
            respTime = row['responseTime']
            print('    {:14s}   : {:5.0f}, {:5.1f}, [ {:5.1f}, {:5.1f} ] : {:5d}'.format( \
              row['actionName'], len(row['df_idx'])/row['msgPerAction'], \
              np.mean(respTime), np.min(respTime), np.max(respTime), \
              len(row['failureList'])))

    return
