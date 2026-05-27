# buildOmnipodKitPodList.py
#
# Post-process omnipodkit_raw_pod_list.csv to produce omnipodkit_pod_list.csv.
#
# Grouping strategy: compute each row's approximate pod pairing time
#   (pairedAt = lastMsgDate - podHrs). For each person, sort by pairedAt
#   and cluster consecutive rows within PAIRING_TOL_HRS into one pod session.
#   This is robust to pod addresses recycling across sessions.
#
# Exclusion: Success pods whose max podHrs < MIN_NOMINAL_HRS are still
#   running and are omitted. Fault pods are always included.
#
# Loop files: message stats come from the row with the largest logHrs.
# Trio files:
#   - If no gaps between consecutive daily rows (gap < TRIO_GAP_HRS):
#     sum logHrs, #Messages, #Sent, #Recv across all rows.
#   - If intermediate files are missing: use last row for message stats.

import os
import pandas as pd

outputPath = os.path.expanduser('~/dev/OPK_Private_Beta/Output')
rawFile  = os.path.join(outputPath, 'omnipodkit_raw_pod_list.csv')
outFile  = os.path.join(outputPath, 'omnipodkit_pod_list.csv')

MIN_NOMINAL_HRS = 60.0   # Success pods below this hrs → still running, skip
PAIRING_TOL_HRS =  2.0   # rows within this window of pairedAt → same pod session
TRIO_GAP_HRS    = 26.0   # gap between Trio rows → intermediate file missing


# ── helpers ───────────────────────────────────────────────────────────────────

def sv(val):
    """Stripped string, empty for NaN/None."""
    return '' if pd.isna(val) else str(val).strip()

def to_float(series):
    return pd.to_numeric(series.astype(str).str.strip(), errors='coerce').fillna(0.0)

def to_int(series):
    return pd.to_numeric(series.astype(str).str.strip(), errors='coerce').fillna(0).astype(int)


# ── load ──────────────────────────────────────────────────────────────────────

df = pd.read_csv(rawFile, skipinitialspace=True)
df.columns = df.columns.str.strip()

df['podHrs']           = to_float(df['podHrs'])
df['logHrs']           = to_float(df['logHrs'])
df['#Messages']        = to_int(df['#Messages'])
df['#Sent']            = to_int(df['#Sent'])
df['#Recv']            = to_int(df['#Recv'])
df['InsulinDelivered'] = to_float(df['InsulinDelivered'])
df['lastMsgDate']      = pd.to_datetime(df['lastMsgDate'], errors='coerce')

# Compute approximate pod pairing timestamp for every row
df['pairedAt'] = df['lastMsgDate'] - pd.to_timedelta(df['podHrs'], unit='h')


# ── process each person ───────────────────────────────────────────────────────

output_rows = []

for who, person_df in df.groupby('Who', sort=True):
    person_df = person_df.sort_values('pairedAt').reset_index(drop=True)

    # Cluster rows into pod sessions by pairedAt proximity
    sessions = []
    current  = [0]
    session_anchor = person_df.iloc[0]['pairedAt']

    for i in range(1, len(person_df)):
        gap_hrs = (person_df.iloc[i]['pairedAt'] - session_anchor).total_seconds() / 3600
        if gap_hrs <= PAIRING_TOL_HRS:
            current.append(i)
        else:
            sessions.append(current)
            current = [i]
            session_anchor = person_df.iloc[i]['pairedAt']
    sessions.append(current)

    for session_indices in sessions:
        grp = person_df.iloc[session_indices].copy().reset_index(drop=True)

        # podAddr and OS-AID type from the most common value in the session
        pod_addr    = grp['podAddr'].mode().iloc[0]
        os_aid      = sv(grp['OS-AID'].mode().iloc[0])
        max_pod_hrs = grp['podHrs'].max()

        # Sort within session by lastMsgDate for end-row and Trio gap detection
        grp = grp.sort_values('lastMsgDate').reset_index(drop=True)
        end_row     = grp.iloc[-1]
        end_finish2 = sv(end_row['Finish2'])

        # Exclusion: still running
        if end_finish2 != 'Fault' and max_pod_hrs < MIN_NOMINAL_HRS:
            print(f'  Skipping {who} / {pod_addr}: still running '
                  f'({max_pod_hrs:.2f} hrs, no fault)')
            continue

        # Pairing row: earliest row with PkgLot
        has_pairing = grp['PkgLot'].apply(lambda v: sv(v) != '')
        start_row   = grp[has_pairing].iloc[0] if has_pairing.any() else None

        # ── pairing fields ────────────────────────────────────────────────
        pkg_lot = sv(start_row['PkgLot']) if start_row is not None else ''
        pod_fw  = sv(start_row['PodFW'])  if start_row is not None else ''
        ble_fw  = sv(start_row['BleFW'])  if start_row is not None else ''
        lot_no  = sv(start_row['LotNo'])  if start_row is not None else ''
        seq_no  = sv(start_row['SeqNo'])  if start_row is not None else ''

        # ── end-of-pod fields ─────────────────────────────────────────────
        finish1           = sv(end_row['Finish1'])
        finish2           = sv(end_row['Finish2'])
        last_msg_date     = end_row['lastMsgDate']
        pod_hrs           = end_row['podHrs']
        insulin_delivered = end_row['InsulinDelivered']
        pdm_ref_code  = sv(end_row['PDM RefCode'])   if finish2 == 'Fault' else ''
        raw_hex_fault = sv(end_row['rawHex(Fault)']) if finish2 == 'Fault' else ''

        # ── build info from end row (rule 2f) ─────────────────────────────
        app_name_ver  = sv(end_row['appNameAndVersion'])
        build_date    = sv(end_row['buildDate'])
        os_aid_branch = sv(end_row['OS-AID branch'])
        os_aid_sha    = sv(end_row['OS-AID SHA'])
        opk_branch    = sv(end_row['OmnipodKit branch'])
        opk_sha       = sv(end_row['OmnipodKit SHA'])

        # ── message stats ─────────────────────────────────────────────────
        n = len(grp)
        if os_aid == 'Loop':
            # Use row with largest logHrs
            best_row = grp.loc[grp['logHrs'].idxmax()]
            log_hrs  = best_row['logHrs']
            num_msgs = best_row['#Messages']
            num_sent = best_row['#Sent']
            num_recv = best_row['#Recv']
        else:
            # Trio: check for gaps between consecutive daily rows
            if n >= 2:
                dates   = grp['lastMsgDate'].tolist()
                gaps    = [(dates[i+1] - dates[i]).total_seconds() / 3600
                           for i in range(n - 1)]
                has_gap = any(g > TRIO_GAP_HRS for g in gaps)
            else:
                has_gap = False

            if has_gap:
                # Missing intermediate files: use last row
                log_hrs  = end_row['logHrs']
                num_msgs = end_row['#Messages']
                num_sent = end_row['#Sent']
                num_recv = end_row['#Recv']
            else:
                # All files present: accumulate
                log_hrs  = grp['logHrs'].sum()
                num_msgs = grp['#Messages'].sum()
                num_sent = grp['#Sent'].sum()
                num_recv = grp['#Recv'].sum()

        recv_send_pct = int(round(100 * num_recv / num_sent)) if num_sent > 0 else 0

        # ── filenames: all unique filenames across the session ─────────────
        seen, filenames = set(), []
        for f in grp['filename']:
            fstr = sv(f)
            if fstr and fstr not in seen:
                seen.add(fstr)
                filenames.append(fstr)
        filenames_str = '; '.join(filenames)

        output_rows.append({
            'Who':               who,
            'OS-AID':            os_aid,
            'Finish1':           finish1,
            'Finish2':           finish2,
            'lastMsgDate':       last_msg_date,
            'podAddr':           pod_addr,
            'podHrs':            f'{pod_hrs:6.2f}',
            'logHrs':            f'{log_hrs:6.2f}',
            '#Messages':         num_msgs,
            '#Sent':             num_sent,
            '#Recv':             num_recv,
            '#Recv/#Send%':      recv_send_pct,
            'InsulinDelivered':  f'{insulin_delivered:6.2f}',
            'PkgLot':            pkg_lot,
            'PodFW':             pod_fw,
            'BleFW':             ble_fw,
            'LotNo':             lot_no,
            'SeqNo':             seq_no,
            'PDM RefCode':       pdm_ref_code,
            'rawHex(Fault)':     raw_hex_fault,
            'filenames':         filenames_str,
            'appNameAndVersion': app_name_ver,
            'buildDate':         build_date,
            'OS-AID branch':     os_aid_branch,
            'OS-AID SHA':        os_aid_sha,
            'OmnipodKit branch': opk_branch,
            'OmnipodKit SHA':    opk_sha,
        })


# ── write output ──────────────────────────────────────────────────────────────

if output_rows:
    out_df = pd.DataFrame(output_rows, columns=[
        'Who', 'OS-AID', 'Finish1', 'Finish2', 'lastMsgDate', 'podAddr',
        'podHrs', 'logHrs', '#Messages', '#Sent', '#Recv', '#Recv/#Send%',
        'InsulinDelivered', 'PkgLot', 'PodFW', 'BleFW', 'LotNo', 'SeqNo',
        'PDM RefCode', 'rawHex(Fault)', 'filenames',
        'appNameAndVersion', 'buildDate',
        'OS-AID branch', 'OS-AID SHA', 'OmnipodKit branch', 'OmnipodKit SHA',
    ])
    out_df.fillna('').to_csv(outFile, index=False)
    print(f'\n{len(output_rows)} pod(s) written to {outFile}')
else:
    print('\nNo pods to write.')
