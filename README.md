# OmniLoopMessageParser
python code to parse the messages found in Loop Reports from loop-priv

## Origins
Some of the intial work done by Eelke Jager on the Jupyter workbook was copied to my local computer to enable batch processing and easy reprocessing (https://omnikit-lab.herokuapp.com/lab?)

## runLastLoopReport.py

Step 1

Download one Loop Report and place in folder for that person; insert _Nominal or _0xFF for the FF fault type

Run python runLastLoopReport.py which reports stuff to the cmd window and adds a line to the output_master.csv file

Copy and paste some of the output to the zulip window

Repeat until all new reports have been downloaded

Step 2

Copy new lines into my spreadsheet

Review updated statistics

## runAll.py

When code has been modified to report an additional column (or to reorder the columns), archive and then delete output_master.csv

Run python runAll.py

This will apply new processing and send output table for every file in the Loop Reports directory to a new output_master.csv with updated header row.

## Main Code

analyzeMessageLogs.py : main routine for processing and reporting results from Loop Report. Started with work from Eelke and Marion on Jupyter and have added a bunch of output without subtracting very much.  Very verbose and could be cleaned up as we progress

## Low Level Utilities

messageLogs_functions.py : group of functions created by Eelke and Marion on Jupyter for early analysis work, builds the pandas DataFrame from the Loop Report messages and various other functions

byteUtils.py : combine array of bytes into appropriate integer

get_file_list.py : given a path, find all the named subpaths with their associated Loop Report.md file, return list sorted from oldest to newest

basal_analysis.py : basal timing analysis added to Jupyter by Eelke and copied over on 3/2/2019

utils.py : add new low level routines used by more than one function (needed for Eelke basal analysis and Marion extract sequences from dataframe)

messagePatternParsing.py : decides which parser to call and if parser doesn't exist yet, returns default msgDict dictionary

parse_1d.py : parses 0x1d response and returns results in msgDict dictionary

parse_02.py : parses (some of the) 0x02 response and returns results in msgDict dictionary

parse_06.py : parses the nonce resync 0x06 response and returns results in msgDict dictionary

## Ignore Everything Else

I use workbook.py to copy and paste lines directly into python when testing and figuring things out

I use test.py to rapidly test a new thing

I copied some other items from various other places while trying to learn how to do stuff, but they are not currently in use. 
