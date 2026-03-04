from util.pd import findBreakPoints
from analysis.analyzePodMessages import analyzePodMessages
import numpy as np
import pandas as pd

"""
analyzePodConnectionTime
    parses the connectDF to report statistics on time between pod disconnect
    and pod reconnect
"""


def analyzePodConnectionTime(fileDict, connectDF, outFlag, vFlag):
    """
        Purpose: analyze the connectDF which list times for pod connect and disconnect messages

        Input:
            fileDict - pass through to next function
            connectDF dataFrame with these columns
                time
                pod_address
                pod_connect: value is 0 for a disconnect and 1 for a connect
            outFlag used to route output (if needed)
            vFlag pass through selection for verbosity
    """

    reconnectDF = pd.DataFrame({})

    # git deltaTime between every message
    connectDF['time'] = pd.to_datetime(connectDF['time'])
    # calculate all the delta times, them apply condition to get just the time
    # from disconnect to reconnect
    connectDF['reconnectTime'] = (connectDF['time'] -
                         connectDF['time'].shift()
                         ).dt.seconds.fillna(0).astype(float)

    # limit the condition to time from disconnect (0) to next connect (1)
    condition = (connectDF['pod_connect'] == 1) & \
                (connectDF['pod_connect'].shift(1) == 0) & \
                (connectDF['pod_address'] == connectDF['pod_address'].shift(1))
    
    df = connectDF[condition]
    reconnectDF = df.iloc[1:]

    # TODO: separate by pod address
    uniq_pod_address = connectDF['pod_address'].unique()
    numberOfPods = len(uniq_pod_address)
    # define an empty dict in case there are no reconnects for a given pod address
    reconnectStatsDict = []
    emptyPodDict = {
            'pod_address': 'n/a'
            , 'numberConnections': 0
            , 'sec_median': -1
            , 'sec_min_05_95_max': [ -1, -1, -1, -1]
    }
        
    for idx in range(numberOfPods):
        # time is in integer seconds
        # analyze reconnect time for each pod address
        thisAddress = (reconnectDF['pod_address'] == uniq_pod_address[idx])
        dfTmp = pd.DataFrame({})
        dfTmp = reconnectDF[thisAddress]
        if len(dfTmp) > 1:
            pod_stats = {
                'pod_address': uniq_pod_address[idx]
                , 'numberConnections': len(dfTmp)
                , 'sec_median': dfTmp['reconnectTime'].median()
                , 'sec_min_05_95_max': [
                    int(dfTmp['reconnectTime'].min())
                    , int(dfTmp['reconnectTime'].quantile(0.05))
                    , int(dfTmp['reconnectTime'].quantile(0.95))
                    , int(dfTmp['reconnectTime'].max())
                ]
                }
            reconnectStatsDict.append(pod_stats)
        else:
            reconnectStatsDict.append(emptyPodDict)

    return reconnectDF, reconnectStatsDict
