# OmniLoopMessageParser
python code to parse the messages found in Loop Reports from loop-priv

## Origins
Some of the intial work done by Eelke Jager on the Jupyter workbook was copied to my local computer to enable batch processing and easy reprocessing (https://omnikit-lab.herokuapp.com/lab?)

## 3/16/2019: Even better version WIP

Create an action dictionary that associates messages together.  For example, a temporary basal (with current version of code) requires a cancel TB (1f02), with 1d status return, followed by set the new TB (1a16), followed by another 1d status return.  If these 4 do not line up, then that TB (identified by the 1a16 row) is treated as a "failure".  If they do line up, then the start time (in sec from start of pod) and response time (from 1f02 to final 1d) is tabulated along with the state of the pod - is it running a schedule basal (True) or not (False).

This enables better reporting of various results.  The lower level functions are working.  Need more testing and the main reporting function to call the new stuff.

New files:

checkAction.py

podUtils.py

## 3/10/2019: NEW VERSION - WIP

New code takes every message read from the Loop_Report file and then parses it.
There is a send dictionary that provides the name for the request (from OpenOmni/Wiki) along with the expected response message - typically 1d.

There is a recv dictionary that provides the name for the response (from wiki).

Joe has requested more fidelity on some of the reporting.

## Main Code

NEW

analyzeMessageLogsNew.py :

New main routine for processing and reporting results from Loop Report. Calls some new routines found in the podStateAnalysis.py file and builds up the message list along with the current pod state for each message. Note that for the most part, the pod state (see next line) updates in response to the 1d response.

Keep track of pod_progress, insulin delivered, last TB request, last Bolus request, current value (True/False) for immediate_bolus_active, temp_basal_active, scheduled_basal_active.  (Note - I did not put in tracking for extended_bolus_active since that is not used by Loop so is always false)

DEPRECATED - but still runs

analyzeMessageLogs.py : main routine for processing and reporting results from Loop Report. Started with work from Eelke and Marion on Jupyter and have added a bunch of output without subtracting very much.  Very verbose and could be cleaned up as we progress

## Low Level Utilities

NEW:

podStateAnalysis.py : routines used to update the pod state on a per message basis

EXISTING (some are modified to support new features, maintain old analysis)

messageLogs_functions.py : group of functions created by Eelke and Marion on Jupyter for early analysis work, builds the pandas DataFrame from the Loop Report messages and various other functions

byteUtils.py : combine array of bytes into appropriate integer

get_file_list.py : given a path, find all the named subpaths with their associated Loop Report.md file, return list sorted from oldest to newest

utils.py : add new low level routines used by more than one function

messagePatternParsing.py : decides which parser to call and if parser doesn't exist yet, returns default msgDict dictionary

The following parse the indicated command and return result in a msgDict dictionary:

parse_1a13.py, parse_1a16.py, parse_1a16.py, parse_1d.py, parse_1f.py, parse_02.py, parse_06.py, parse_0e.py

DEPRECATED (portion still in use is found in podStateAnalysis.py)

basal_analysis.py : basal timing analysis added to Jupyter by Eelke and copied over on 3/2/2019

## Ignore Everything Else

I use workbook.py to copy and paste lines directly into python when testing and figuring things out

I use test.py to rapidly test a new thing

I copied some other items from various other places while trying to learn how to do stuff, but they are not currently in use and have been deleted from current master

## 3/10/2019: OLD VERSION - DEPRECATED but leave all the code working

runLastLoopReport.py

## Step 1

Download one Loop Report and place in folder for that person; insert _Nominal or _0xFF for the FF fault type

Run python runLastLoopReport.py which reports stuff to the cmd window and adds a line to the output_master.csv file

Copy and paste some of the output to the zulip window

Repeat until all new reports have been downloaded

## Step 2

Copy new lines into my spreadsheet

Review updated statistics

## runAll.py

When code has been modified to report an additional column (or to reorder the columns), archive and then delete output_master.csv

Run python runAll.py

This will apply new processing and send output table for every file in the Loop Reports directory to a new output_master.csv with updated header row.
