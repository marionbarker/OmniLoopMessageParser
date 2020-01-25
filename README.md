# OmniLoopMessageParser
python code to parse the messages found in Loop Reports from loop-priv

## January 2020 Updates
Set up tag v1.0 to be the August 2019 version, then begin updates.

First wave is to update the parser so that it can handle having this format:
    ## MessageLog
    goodstuff

    status: ## PumpManagerStatus
And BeautifulSoup doesn't handle the status: the way I need it to - add a check and remove final parsed_content['MessageLog'] record if necessary

Also, add to the parser: PodInfoFaultEvent - this is a WIP
Modify all the files to be LF instead of CRLF so it matches the change Michael Pangborg made to the repo (don't want spurious diffs showing).

Check in the interim version of 2020/01/25 - then update to handle the new parser of commands for updated rileylink_ios code.

## Origins
Some of the intial work done by Eelke Jager on the Jupyter workbook was copied to my local computer to enable batch processing and easy reprocessing (https://omnikit-lab.herokuapp.com/lab?)

## Rev3 Version

Create an action dictionary that associates messages together.

For example, a temporary basal (with current version of code) requires:
* cancel TB (1f02)
* pod status response (1d)
* set new TB (1a16)
* pod status response (1d)

If these 4 do not line up as sequential messages for any TB in the podState dataframe, identified by the index for the associated 1a16 row, that '1a16' index is inserted in an incompleteList for that action.

If they do line up, then the start time (in sec from start of pod) and response time (from 1f02 to final 1d) is tabulated along with the state of the pod - i.e., is it running a scheduled basal (True) or not (False) prior to the initial cancel TB message. All 4 of the indices for each complete action instance are combined into a completedList.

This enables better reporting of various results and enables easier additions of requested analysis tasks.

# How Marion uses the code:

## Updates to output_master_rev3.csv

Download one Loop Report from Zulip and place in folder for that person; insert _0xFF if there was a FF fault reported (even if the 0x0202 message was not captured)

* python whatIsLastReport.py  # to make sure file is in right place

* python runLastLoopReport.py # to report formatted information to the terminal window and add a row to the output_master_rev3.csv file

If there is anything off-nominal or interesting, copy and paste that to the zulip window, otherwise, just do a thumbs-up emoji to indicate report was captured.

Repeat until all new reports have been downloaded

Copy the new lines from the csv and Paste Values (Shift-Ctrl-V) to end of the Current Uploaded tab of the google sheet (link is in Zulip)

## Replace output_master_rev3.csv following code improvements

First delete or archive output_master_rev3.csv

Run python runAll433_Rev3.py which ignores any report with original antenna

# Main Code

## analyzeMessageLogsRev3.py :

Rev3 version of main routine for processing and reporting results from Loop Report.

Parses the message logs, prints a report and, if asked, outputs a row to a named csv file.

Top Level functions called by analyzeMessageLogsRev3:
* read_file
* generate_table
* parse_info_from_filename
* podStateAnalysis
* checkAction

## messageLogs_functions.py :

Group of functions originally created by Eelke on Jupyter. Subsequently modified slightly with a few new functions added. Generates a pandas dataframe, aka, df, from every message in the log. Includes:
* read_file
* select_extra_command
* generate_table
* parse_info_from_filename

## podStateAnalysis.py

This parses every raw message in df. The output from this function includes the podState dataframe, which reports useful information like time stamp (UTC), radio on time, time since start of pod, bool values for immediate_bolus_active, temp_basal_active and scheduled_basal_active, and the last requested values for Bolus and TB.  It also has the message_type and raw_value of the message from the df frame. (Note - I did not put in logic tracking for extended_bolus_active since that is not used by Loop so is always false).

## checkAction.py

This uses the actionDict (from podUtils) to extract typical actions from podState.  (See example at beginning of README.md.) If an action exists in the actionDict, it is grouped into the actionFrame dataframe returned by this function. The indices associated with the pod initialization are also returned, with the pod_progress values used to identify when pod is being initialized.

*     actionColumnNames = ('actionName', 'msgPerAction', 'cumStartSec', \
      'responseTime' , 'SchBasalState', 'incompleteList','completedList' )

## Lower Level functions

* byteUtils.py : combine array of bytes into appropriate integer

* get_file_list.py : given a path, find all the named subpaths with their associated Loop Report.md files, return list sorted from oldest to newest

* utils.py : low level routines used by more than one function

* messagePatternParsing.py : decides which parser to call and if parser doesn't exist yet, returns default msgDict dictionary

The following functions parse the indicated command and return result in a msgDict dictionary:
* parse_1a13.py
* parse_1a16.py
* parse_1a16.py
* parse_1d.py
* parse_1f.py
* parse_02.py
* parse_06.py
* parse_0e.py

podUtils.py : contains various pod specific utilities:
* getPodProgessMeaning
* getUnitsFromPulses
* getActionDict

* getAnalysisIO: switches between Marion's configuration of files for Mac and PC without having to tweak the runLastLoopReport or runAll433_Rev3 code manually. For anyone pulling this repo to their machine, this should be the only function that requires editing.

## DEPRECATED

This code will still run. None of these functions are used by  analyzeMessageLogsRev3.py

* analyzeMessageLogsNew.py :

Deprecated main routine for processing and reporting results from Loop Report. Uses podStateAnalysis function.  But other code is found in deprecated .py functions.

The deprecated_PodSuccess code takes every message read from the Loop_Report file and then parses it using the deprecated send, recv and complete message dictionaries.

* analyzeMessageLogs.py :

Deprecated (original) main routine for processing and reporting results from Loop Report. Started with work from Eelke and Marion on Jupyter then added a bunch of output without subtracting very much.  Uses functions found in deprecated_PodSequence (completely superceded by checkAction.)

## Deprecated Low Level Utilities

* basal_analysis.py : basal timing analysis added to Jupyter by Eelke and copied over on 3/2/2019
* deprecated_PodSequence: initial idea - replaced by podStateAnalysis
* deprecated_PodSuccess: replaced by checkAction
