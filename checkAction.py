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

    # initial thought was to remove the Fault, nonce and init lines from frame
    #  but that messes up the adjacency check when going through the actionDict
    #  The only lines that should be removed are the successful action ones

    # first identify fault, if present
    frFault = frame[frame.message_type==fault]
    faultIdx = frFault.index.to_list()

    # search for nonce rows
    nonceFrame = frame[frame.message_type==nonce]
    nonceIdx = np.array(nonceFrame.index.to_list())

    # determine initIdx from pod_progress value
    podInit = frame[frame.pod_progress < 8]
    # get list of indices for initializing the pod
    initIdx = np.array(podInit.index.to_list())
    # need to add the next row too - but need to protect that it wasn't removed with nonce drop
    checkIdx = initIdx[-1]+1
    initIdx = np.append(initIdx, checkIdx)

    # prepare to search by actions
    frameBalance = frame

    # now search the frame for actions:
    #    actionName from actionDic
    #    list of lists of the completedList for that action,
    #             e.g., (34, 35, 36, 37), (60, 61, 62, 63)
    #    responseTime calculated by taking timeCumSec at end - timeCumSec at end
    #    SchBasal is the scheduled basal state at the beginning of the action
    # if all the expected messages are found in the correct order, then the
    #     indices for all the messages are removed from frameBalance before
    #     searching for the next actionDict item
    successColumnNames = ('actionName', 'msgPerAction', 'cumStartSec', \
      'responseTime' , 'SchBasalState', 'incompleteList','completedList' )

    actionList = []


    for keys,values in actionDict.items():
        badIdx = []         # accumulate action identifier indices that don't have all their messages
        incompleteList = [] # list of badIdx lists by action
        thisAction = keys
        thisID = values[0]           # used to index into matchList, identifier for Action
        matchList = values[1]
        msgPerAction = len(matchList)  # always 2 or 4
        thisFrame = frameBalance[frameBalance.message_type == matchList[thisID]]
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
            badFrame = checkFrame[checkFrame.message_type != matchList[ii+thisID]]
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

        print('Status: ', thisAction, 'Complete: ', len(idx), 'Incomplete: ', len(badIdx))

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
        actionList.append(( thisAction, msgPerAction, t0, \
          responseTime, SchBasalState, incompleteList, thisList))

        # remove these indices from the frameBalance, reset and keep going
        frameBalance = frameBalance.drop(thisList)

    actionFrame = pd.DataFrame(actionList, columns=successColumnNames)
    return actionFrame, initIdx, nonceIdx, faultIdx


def printActionFrame(actionFrame):
    if len(actionFrame) == 0:
        return
    actionSummary = []
    totalCompletedMessages = 0
    print('\n  Action Summary with sequential 4 or 2 message sequences with action response times in sec')
    #print('      Action        : #Success,  mean, [  min,  max  ]  : #Incomplete  : SchBasalRunning(beforeTB), #<30Sec Long ')
    print('      Action        : #Success,  mean, [  min,  max  ] : #Incomplete : SchBasalRunning(beforeTB)')
    for index, row in actionFrame.iterrows():
        respTime = row['responseTime']
        totalCompletedMessages += len(row['completedList'])
        numGood = len(row['completedList'])/row['msgPerAction']
        if row['actionName'] == 'TB':
            startTime = row['cumStartSec']
            deltaTime = startTime[1:-1]-startTime[0:-2]
            # not too sure of numShortTB calc - so don't put in report yet
            # it can go in spreadsheet, so calculate it - come back later
            numShortTB = np.sum(deltaTime<30)
            numSchBasalbeforeTB = np.sum(row['SchBasalState'])
            actionSummary.append((row['actionName'], (numGood, numSchBasalbeforeTB, numShortTB)))
            if False:
                print('    {:14s}  :  {:5.0f},  {:5.0f},  [{:5.0f}, {:5.0f} ] : {:5d}    :  {:5d}, {:5d}'.format( \
                  row['actionName'], numGood, \
                  np.mean(respTime), np.min(respTime), np.max(respTime), \
                  len(row['incompleteList']), numSchBasalbeforeTB, numShortTB))
            else:
                print('    {:14s}  :  {:5.0f},  {:5.0f},  [{:5.0f}, {:5.0f} ] : {:5d}       :  {:5d}'.format( \
                  row['actionName'], numGood, \
                  np.mean(respTime), np.min(respTime), np.max(respTime), \
                  len(row['incompleteList']), numSchBasalbeforeTB))
        else:
            actionSummary.append((row['actionName'], (numGood)))
            print('    {:14s}  :  {:5.0f},  {:5.0f},  [{:5.0f}, {:5.0f} ] : {:5d}'.format( \
              row['actionName'], numGood, \
              np.mean(respTime), np.min(respTime), np.max(respTime), \
              len(row['incompleteList'])))

    return actionSummary, totalCompletedMessages
