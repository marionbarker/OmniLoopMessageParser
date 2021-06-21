# OmniLoopMessageParser
python code to parse the messages found in Loop Reports when pump is Omnipod

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

### example format:
#### Comments:
* log.txt is today since midnight local time
* log_prev.txt is yesterday (midnight to midnight)
    * no sure what happens if change time zone

#### Manual Extraction Example:
$ grep "318 - DEV: Device message:" log_prev.txt

#### WARNING
The log format of: "318 - DEV: Cancel Bolus" without a hex code that might be an open loop glitch (for freeaps-x/release/v0.2.0)
The instances noted were associated with an uncertain bolus with IOB not handled correctly

#### Showing a 0e, 1d exchange:
2021-06-06T00:03:53-0700 [DeviceManager] DeviceDataManager.swift - deviceManager(_:logEventForDeviceIdentifier:type:message:completion:) - 318 - DEV: Device message: 1f091a4634030e010003e8
2021-06-06T00:03:53-0700 [DeviceManager] DeviceDataManager.swift - deviceManager(_:logEventForDeviceIdentifier:type:message:completion:) - 318 - DEV: Device message: 1f091a46380a1d2802265800001a13ff00bc

#### There is no identifying information at the beginning of the file:
log.txt: first line
2021-06-07T00:00:01-0700 [DeviceManager] DeviceDataManager.swift - pumpManagerBLEHeartbeatDidFire(_:) - 173 - DEV: Pump Heartbeat

log_prev.txt: last line
2021-06-06T23:59:00-0700 [DeviceManager] DeviceDataManager.swift - pumpManagerBLEHeartbeatDidFire(_:) - 173 - DEV: Pump Heartbeat

log_prev.txt: first line
2021-06-06T00:00:49-0700 [Nightscout] FetchGlucoseManager.swift - subscribe() - 26 - DEV: FetchGlucoseManager heartbeat

Compared to Loop output:
* 2021-04-04 09:22:00 +0000 Omnipod 1F0C2055 send 1f0c2055101f1a0e3ef1a12102009101008000080008170d00005000030d400000000000008293
* 2021-04-04 09:22:03 +0000 Omnipod 1F0C2055 receive 1f0c2055140a1d5802572008001b4fff81b7

#### Time Stamps
For FreeAPS X log and log_prev files, they run from midnight local time.
The time stamp noted is local time with the -0700 (from PDT) indicated difference wrt GMT 
