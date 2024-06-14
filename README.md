# OmniLoopMessageParser

## Use Cases

1. Parse Saved Files when selected pump is Omnipod and prepare csv file with every Pod message in the file for each individual pod included in the file, valid for
    * Loop Reports
    * FreeAPS X Log Files
        * updated to work with iAPS and Trio files
1. Parse HEX strings from rPi DASH simulator or Xcode debug logs
    * This is done one string at a time

If you want to parse a whole saved Xcode debug log refer to [Select OmniBLE Parser Scheme in Xcode](https://github.com/LoopKit/OmniBLE/pull/124#issuecomment-2148210959)

## Usage Instructions

Please see the [wiki](https://github.com/marionbarker/OmniLoopMessageParser/wiki) for instructions on how to use this parser.

 
## July 2020
* Reorganize the code (with help from #1 child)
    * Use flake8 to force pretty code
    * Use folders and set up packages
* Move the documentation to the wiki (WIP)

## April 2021
* Use pd.at instead of deprecated pd.set_value
* Do some work using git on windows, then switch to mac exclusively

## June 2021
* FreeAPS X aka OpenAPS on an iPhone is available for test (using since April)
    * The log files (log.txt, log_prev.txt) have the message hex code for pods
    * The format is different, so need to expand the parsers to handle Messages

## Later updates
* The README.md was not updated with later updates. Please refer to the [wiki](https://github.com/marionbarker/OmniLoopMessageParser/wiki).
