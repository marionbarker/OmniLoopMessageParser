from util.pd import findBreakPoints
from analysis.analyzePodMessages import analyzePodMessages
import numpy as np
import pandas as pd

"""
analyzePodConnectionTime
    parses the connectDF to report statistics on time between pod disconnect
    and pod reconnect, and on time a pod stays connected (connect to disconnect)
"""


def _compute_stats_per_pod(filtered_df, time_col, uniq_addresses):
    """
    Compute per-pod statistics for a given time column.
    Returns a list of stat dicts, one per unique pod address.
    """
    stats_list = []
    empty_dict = {
        'pod_address': 'n/a',
        'count': 0,
        'sec_median': -1,
        'sec_min_05_95_max': [-1, -1, -1, -1],
    }

    for addr in uniq_addresses:
        addr_df = filtered_df[filtered_df['pod_address'] == addr]
        if len(addr_df) > 1:
            stats_list.append({
                'pod_address': addr,
                'count': len(addr_df),
                'sec_median': addr_df[time_col].median(),
                'sec_min_05_95_max': [
                    int(addr_df[time_col].min()),
                    int(addr_df[time_col].quantile(0.05)),
                    int(addr_df[time_col].quantile(0.95)),
                    int(addr_df[time_col].max()),
                ],
            })
        else:
            stats_list.append(empty_dict)

    return stats_list


def _find_fault_time_per_pod(logDF):
    """
    From the pod message log, find the time of the first fault response (0x0202)
    for each pod address. Returns a dict of {address: fault_time}.
    Pods without a fault are not included.
    """
    if logDF is None or logDF.empty or 'address' not in logDF.columns:
        return {}

    fault_times = {}
    for addr, grp in logDF.groupby('address'):
        # Look for 0x0202 fault response messages
        fault_rows = grp[grp['msgDict'].apply(
            lambda md: isinstance(md, dict) and md.get('msgType') == '0x0202')]
        if len(fault_rows) > 0:
            t = pd.to_datetime(fault_rows.iloc[0]['time'], errors='coerce')
            if pd.notna(t):
                if t.tzinfo is None:
                    t = t.tz_localize('UTC')
                fault_times[addr.upper()] = t
    return fault_times


def _filter_post_fault(df, fault_times):
    """
    Remove connect/disconnect rows that occur at or after the fault time for
    each pod address. This excludes the post-fault connection (where the app
    stays connected or reconnects to read fault details) from statistics.
    """
    if not fault_times:
        return df

    mask = pd.Series(True, index=df.index)
    for addr, cutoff in fault_times.items():
        addr_rows = df['pod_address'].str.upper() == addr
        mask = mask & ~(addr_rows & (df['time'] >= cutoff))
    return df[mask]


def analyzePodConnectionTime(fileDict, connectDF, logDF, outFlag, vFlag):
    """
        Purpose: analyze the connectDF which lists times for pod connect
                 and disconnect messages

        Input:
            fileDict - pass through to next function
            connectDF dataFrame with these columns
                time
                pod_address
                pod_connect: value is 0 for a disconnect and 1 for a connect
            logDF - pod message log dataFrame (used to find last message time
                    per pod to exclude post-fault connect/disconnect events)
            outFlag used to route output (if needed)
            vFlag pass through selection for verbosity

        Returns:
            reconnectDF - rows representing disconnect→connect transitions
            reconnectStatsDict - per-pod reconnect time statistics
            connectedStatsDict - per-pod connected duration statistics
    """

    # ensure time is datetime
    connectDF['time'] = pd.to_datetime(connectDF['time'], errors='coerce', utc=True)

    # Exclude connect/disconnect events at or after a fault for each pod
    fault_times = _find_fault_time_per_pod(logDF)
    connectDF = _filter_post_fault(connectDF, fault_times)

    # calculate delta time from previous row in seconds
    connectDF['deltaTimeSec'] = (
        connectDF['time'] - connectDF['time'].shift()
    ).dt.total_seconds().fillna(0).astype(float)

    uniq_pod_address = connectDF['pod_address'].unique()

    # ── Reconnect time: disconnect (0) → next connect (1) ────────────────
    reconnect_condition = (
        (connectDF['pod_connect'] == 1) &
        (connectDF['pod_connect'].shift(1) == 0) &
        (connectDF['pod_address'] == connectDF['pod_address'].shift(1))
    )
    reconnectDF = connectDF[reconnect_condition].iloc[1:]  # skip first (may be partial)
    reconnectStatsDict = _compute_stats_per_pod(
        reconnectDF, 'deltaTimeSec', uniq_pod_address)

    # ── Connected duration: connect (1) → next disconnect (0) ────────────
    connected_condition = (
        (connectDF['pod_connect'] == 0) &
        (connectDF['pod_connect'].shift(1) == 1) &
        (connectDF['pod_address'] == connectDF['pod_address'].shift(1))
    )
    connectedDF = connectDF[connected_condition].iloc[1:]  # skip first (may be partial)
    connectedStatsDict = _compute_stats_per_pod(
        connectedDF, 'deltaTimeSec', uniq_pod_address)

    return reconnectDF, reconnectStatsDict, connectedStatsDict
