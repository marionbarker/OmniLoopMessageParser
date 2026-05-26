# loop_read_file.py

import re
import pandas as pd
import numpy as np
#
from parsers.messageLogs_functions import extract_fault_info
from parsers.messageLogs_functions import extract_loop_version
from parsers.messageLogs_functions import extract_messages
from parsers.messageLogs_functions import extract_pod_manager
from parsers.messageLogs_functions import parse_filehandle
from parsers.fx_logs.extract_raw_pod import extract_raw_pod
from parsers.fx_logs.extract_raw_determBasal import extract_raw_determBasal
from parsers.fx_logs.extract_raw_determTdd import extract_raw_determTdd
from parsers.fx_logs.extract_raw_TDD import extract_raw_TDD
from parsers.pod_connect.extract_pod_connect_time import extract_pod_connect_time

def _extract_trio_build_info(raw_content):
    """Extract OS-AID and OmnipodKit branch/SHA from a Trio 'DEV: Trio Started' line.

    Example line fragment:
      DEV: Trio Started: v0.6.0.51(1) ... [Branch: mdb/add_all_managers 38a7315]
      [submodules: ..., OmnipodKit: O5-integration-continued2 482be1a, ...]
    """
    result = {'osAidBranch': '', 'osAidSHA': '',
              'omnipodKitBranch': '', 'omnipodKitSHA': ''}
    # find the DEV: Trio Started line first, then search within it
    line_match = re.search(r'DEV: Trio Started.*', raw_content)
    if not line_match:
        return result
    line = line_match.group(0)
    # OS-AID branch and SHA from [Branch: <branch> <sha>]
    m = re.search(r'\[Branch:\s+(\S+)\s+([0-9a-f]+)\]', line)
    if m:
        result['osAidBranch'] = m.group(1)
        result['osAidSHA'] = m.group(2)
    # OmnipodKit branch and SHA from submodules list
    m = re.search(r'OmnipodKit:\s+(\S+)\s+([0-9a-f]+)', line)
    if m:
        result['omnipodKitBranch'] = m.group(1)
        result['omnipodKitSHA'] = m.group(2)
    return result


# pass in fileDict instead of filename
def loop_read_file(fileDict):
    """
      loop with little "l" handles Loop, Trio, iAPS
      Handles either MessageLog; Device Communication Log or FAPSX log
      Note - there were several version of having status being tacked
             on to the end of the MessageLog, handle these cases
      Break into more modular chunks
      returns a dictionary of items
    """
    fileDict['recordType'] = "unknown"
    parsed_content = {}
    # define empty dataframes
    logDF = pd.DataFrame({})
    connectDF = pd.DataFrame({})
    determBasalDF = pd.DataFrame({})
    determTddDF_old = pd.DataFrame({})
    determTddDF_tcd = pd.DataFrame({})
    podMgrDict = {}
    loopVersionDict = {}
    faultInfoDict = {}
    noisy = 0

    # prepare default return dictonary, note that fileDict might be modified
    loopReadDict = {'fileDict': fileDict,
                    'logDF': logDF,
                    'podMgrDict': podMgrDict,
                    'faultInfoDict': faultInfoDict,
                    'loopVersionDict': loopVersionDict,
                    'determBasalDF': determBasalDF,
                    'determTddDF_old': determTddDF_old,
                    'determTddDF_tcd': determTddDF_tcd,
                    'connectDF': connectDF}

    # check loopType and act accordingly
    filename = fileDict['filename']
    if fileDict['loopType'].lower() == "loop":
        file = open(filename, "r", encoding='UTF8')
        parsed_content = parse_filehandle(file)
        # ensure file is closed
        file.close()
        # also need raw_content for omnipod timing
        fp = open(filename, "r", encoding='UTF8')
        raw_content = fp.read()
        fp.close()

        if parsed_content.get('MessageLog'):
            fileDict['recordType'] = "messageLog"
            # handle various versions of status: being tacked onto end
            tmp = parsed_content['MessageLog'][-1]
            tmpEnd = tmp[len(tmp)-7:]
            # Handle case where last line of messageLog is 'status: ##'
            if tmpEnd == 'status:':
                if noisy:
                    print(' *** Last Message:\n',
                          parsed_content['MessageLog'][-1])
                if len(tmp) == 7:
                    if noisy:
                        print('  length of last message was {:d}'.
                              format(len(tmp)))
                    parsed_content['MessageLog'] = \
                        parsed_content['MessageLog'][:-1]
                else:
                    if noisy:
                        print('  length of last message was {:d} (not 7)'.
                              format(len(tmp)))
                    parsed_content['MessageLog'][-1] = tmp[:len(tmp)-8]
                    if noisy:
                        print('  ',
                              parsed_content['MessageLog'][-1], '\n ***\n')
        if parsed_content.get('Device Communication Log'):
            fileDict['recordType'] = "deviceLog"

        logDF = extract_messages(fileDict['recordType'], parsed_content, raw_content)
        recordType = fileDict['recordType']
        connectDF = extract_pod_connect_time(raw_content, recordType)
        faultInfoDict = extract_fault_info(parsed_content)
        loopVersionDict = extract_loop_version(parsed_content)
        if 'PodState' in parsed_content:
            podMgrDict = extract_pod_manager(parsed_content)
        else:
            podMgrDict = {}

    elif fileDict['loopType'].lower() == "fx":
        """
            read the raw content then parse for pods / fx separately
        """
        fp = open(filename, "r", encoding='UTF8')
        raw_content = fp.read()
        fp.close()

        logDF = extract_raw_pod(raw_content)
        determBasalDF = extract_raw_determBasal(raw_content)
        # read version from old version and evaluate new versionq
        determTddDF_old = extract_raw_determTdd(raw_content)
        determTddDF_tcd = extract_raw_TDD(raw_content)
        recordType = "FAPSX"
        connectDF = extract_pod_connect_time(raw_content, recordType)

        fileDict['recordType'] = "FAPSX"  # overwrite if both DF are empty
        if determBasalDF.empty and logDF.empty:
            fileDict['recordType'] = "not_FAPSX"
            fileDict['date'] = fileDict['recordType']
        elif logDF.empty:
            thisDate = pd.to_datetime(determBasalDF.loc[0,
                                      'date_time'])
            fileDict['date'] = thisDate.strftime('%Y%m%d')
        else:
            thisDate = logDF.loc[0, 'time']
            fileDict['date'] = thisDate.strftime('%Y%m%d')
        faultInfoDict = {}
        loopVersionDict = {}
    else:
        print('loopType is not recognized')
        return loopReadDict

    # There are some items that are useful to have in fileDict that are
    # sometimes found in loopVersionDict and sometimes with different id
    # This field has had various names over the versions of Loop, collect them
    # fill those in with values or empty strings before returning.
    fileDict['appNameAndVersion'] = ''
    fileDict['buildDateString'] = ''
    fileDict['gitRevision'] = ''
    fileDict['gitBranch'] = ''
    fileDict['workspaceGitRevision'] = ''
    fileDict['workspaceGitBranch'] = ''
    if 'appNameAndVersion' in loopVersionDict:
        fileDict['appNameAndVersion'] = loopVersionDict['appNameAndVersion']
    if 'codeVersion' in loopVersionDict:
        fileDict['appNameAndVersion'] = loopVersionDict['codeVersion']
        loopVersionDict['appNameAndVersion'] = loopVersionDict['codeVersion']
    if 'Version' in loopVersionDict:
        fileDict['appNameAndVersion'] = loopVersionDict['Version']
        loopVersionDict['appNameAndVersion'] = loopVersionDict['Version']
    if 'buildDateString' in loopVersionDict:
        fileDict['buildDateString'] = loopVersionDict['buildDateString']
    if 'gitRevision' in loopVersionDict:
        fileDict['gitRevision'] = loopVersionDict['gitRevision']
    if 'gitBranch' in loopVersionDict:
        fileDict['gitBranch'] = loopVersionDict['gitBranch']
    if 'workspaceGitRevision' in loopVersionDict:
        fileDict['workspaceGitRevision'] = \
            loopVersionDict['workspaceGitRevision']
    if 'workspaceGitBranch' in loopVersionDict:
        fileDict['workspaceGitBranch'] = loopVersionDict['workspaceGitBranch']

    # OS-AID app type, workspace branch/SHA, and OmnipodKit submodule branch/SHA
    fileDict['osAidBranch'] = ''
    fileDict['osAidSHA'] = ''
    fileDict['omnipodKitBranch'] = ''
    fileDict['omnipodKitSHA'] = ''
    if fileDict['loopType'].lower() == 'loop':
        fileDict['osAidType'] = 'Loop'
        fileDict['osAidBranch'] = loopVersionDict.get('Workspace branch', '')
        fileDict['osAidSHA'] = loopVersionDict.get('Workspace SHA', '')
        opkValue = loopVersionDict.get('OmnipodKit', '')
        if opkValue and ', ' in opkValue:
            parts = opkValue.split(', ', 1)
            fileDict['omnipodKitBranch'] = parts[0].strip()
            fileDict['omnipodKitSHA'] = parts[1].strip()
    elif fileDict['loopType'].lower() == 'fx':
        fileDict['osAidType'] = 'Trio'
        trioBuildInfo = _extract_trio_build_info(raw_content)
        fileDict.update(trioBuildInfo)
    else:
        fileDict['osAidType'] = ''

    loopReadDict = {'fileDict': fileDict,
                    'logDF': logDF,
                    'podMgrDict': podMgrDict,
                    'faultInfoDict': faultInfoDict,
                    'loopVersionDict': loopVersionDict,
                    'determBasalDF': determBasalDF,
                    'determTddDF_old': determTddDF_old,
                    'determTddDF_tcd': determTddDF_tcd,
                    'connectDF': connectDF}

    return loopReadDict