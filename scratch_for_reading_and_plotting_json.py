# scratch_for_reading_and_plotting_json.py

# use the same project as OmniLoopMessageParser, but may need to break out later

# first read in a Nightscout json file and print out selected results

# copy imports from messageLogs_function.py

import re
import tempfile
import numpy as np
# import os
import pandas as pd
import json
import matplotlib.pyplot as plt
from util.misc import printDict


def read_raw_nightscout(filename):
    print("filename in read_json_file = ", filename)
    fp = open(filename, "r", encoding='UTF8')
    raw_content = fp.read()
    fp.close()
    # remove the beginning and ending []
    content = raw_content[1:-2]
    # break into separate json lines
    content = content.replace(',{"_id', '\n{"_id')
    return content
    

def extract_devicestatus(content):

    nsDeviceDataDF = pd.DataFrame({})
 
    noisy = 0
    if noisy:
        print("\n>>>   call to extract_devicestatus")
        print("first 256 characters : ", content[:256])
        print("\nlast  256 characters : ", content[-256:])

    # split by newline:
    lines_raw = content.splitlines()
    print("\nlines_raw has ", len(lines_raw), " lines")

    # parse the devicedata output
    jdx=0
    loop_time=[]
    iob_time=[]
    iob=[]
    glucose_time=[]
    glucose=[]
    recommendedBolus=[]
    for line in lines_raw:
        try:
            json_dict = json.loads(line)
            if (jdx < 2 & noisy):
                print('\n *** jdx = ', jdx)
                printDict(json_dict)
            loop_time.append(json_dict['loop']['timestamp'][0:-1]) # remove Z
            iob_time.append(json_dict['loop']['iob']['timestamp'])
            iob.append(json_dict['loop']['iob']['iob'])
            glucose_time.append(json_dict['loop']['predicted']['startDate'])
            glucose.append(json_dict['loop']['predicted']['values'][0])
            recommendedBolus.append(json_dict['loop']['recommendedBolus'])
            if noisy:
                print("\n *** jdx = ", jdx)
                print(loop_time[jdx], glucose_time[jdx], iob_time[jdx], glucose[jdx], iob[jdx])
            jdx=jdx+1

        except Exception as e:
            print("Failure parsing json")
            print("*** exception:")
            print(e)
            print("*** line:")
            print(line)
            exit

    d = {'loop_time': loop_time, 'iob_time': iob_time, 
         'glucose_time': glucose_time,
        'IOB': iob, 'glucose': glucose, 'recommendedBolus': recommendedBolus}
    tmpDF = pd.DataFrame(d)
    # split the time into a new column, use for plots 0 to 24 hour
    time_array = pd.to_datetime(tmpDF['loop_time'])
    tmpDF['time'] = time_array
    # nightscout data downloaded in reverse time
    # nsDeviceDataDF = tmpDF.sort_values(by="time")
    nsDeviceDataDF = tmpDF.sort_index(ascending=False)

    return nsDeviceDataDF



def extract_treatments(content):

    nsTreatmentsDF = pd.DataFrame({})
    test_designation = "Not Provided"
 
    noisy = 0
    if noisy:
        print("\n>>>   call to extract_treatments")
        print("first 256 characters : ", content[:256])
        print("\nlast  256 characters : ", content[-256:])

    # split by newline:
    lines_raw = content.splitlines()
    print("\nlines_raw has ", len(lines_raw), " lines")

    # parse the devicedata output
    tb_string = 'Temp Basal'
    ab_string = 'Correction Bolus'
    note_string = 'Note'
    lost_basal = -0.60/60 # units per minute
    jdx=0
    timestamp=[]
    insulin=[]
    for line in lines_raw:
        try:
            json_dict = json.loads(line)
            #if (noisy & jdx < 2):
            #    print('\n *** jdx = ', jdx)
            #    printDict(json_dict)
            
            # check eventType
            eventType = json_dict['eventType']
            if eventType == tb_string:
                duration = json_dict['duration']
                insulin.append(lost_basal*duration)
                timestamp.append(json_dict['timestamp'])
            elif eventType == ab_string:
                insulin.append(json_dict['insulin'])
                timestamp.append(json_dict['timestamp'])
            elif eventType == note_string:
                test_designation=json_dict['notes']
                print(json_dict['created_at'], json_dict['notes'])
            else:
                print(json_dict['created_at'], eventType)
            if noisy:
                print("\n *** jdx = ", jdx)
                print(timestamp[jdx], insulin[jdx])
            jdx=jdx+1

        except Exception as e:
            print("Failure parsing json")
            print("*** exception:")
            print(e)
            print("*** line:")
            print(line)
            exit

    d = {'timestamp': timestamp, 'insulin': insulin}
    tmpDF = pd.DataFrame(d)
    # split the time into a new column, use for plots
    time_array = pd.to_datetime(tmpDF['timestamp'])
    tmpDF['time'] = time_array
    # nightscout data downloaded in reverse time
    # nsTreatmentsDF = tmpDF.sort_values(by="time")
    nsTreatmentsDF = tmpDF.sort_index(ascending=False)

    return test_designation, nsTreatmentsDF

def generatePlot(outFile, label, df1, df2):
    nrow = 3
    ncol = 1
    naxes = 3
    day_in_sec = 24*60*60
    one_hr_in_sec = day_in_sec/24
    #xRange = [0, day_in_sec+1]
    #bottom_ticks = np.arange(0, day_in_sec+1, step=two_hr_in_sec)
    mkSize = 10

    fig, axes = plt.subplots(nrow, ncol, figsize=(15, 7))
    start_time = df1.iloc[0]['time']
    end_time = df1.iloc[-1]['time']
    xRange = [start_time, end_time]
    #elapsed_time = end_time - start_time
    #bottom_ticks = np.arange(0, 21600, step=one_hr_in_sec)

    print("start and end ", start_time, ", ", end_time)

    title_string = (f'Analysis: {start_time}  {label}')

    print()
    print("Plot Title:")
    print(" *** ", title_string)

    axes[0].set_title(title_string)

    #df1.plot(x='time', y='glucose', c='green', ax=axes[0], style='-',
    #        xlim=xRange, xticks=bottom_ticks)
    #df1.plot(x='time', y='IOB', c='blue', ax=axes[1], style='-',
    #        xlim=xRange, xticks=bottom_ticks)
    df1.plot(x='time', y='glucose', c='green', ax=axes[0], style='-',
            xlim=xRange)
    df1.plot(x='time', y='IOB', c='blue', ax=axes[1], style='-',
            xlim=xRange)
    df2.plot(x='time', y='insulin_cumsum', c='black', ax=axes[2], style='-',
            xlim=xRange)

    for x in axes:
        x.grid('on')
        x.legend(bbox_to_anchor=(1.11, 1.0), framealpha=1.0)

    idx = 0
    while idx < naxes:
        x_axis = axes[idx].axes.get_xaxis()
        # x_label = x_axis.get_label()
        x_axis.set_ticklabels([])
        idx += 1

    # set limits for BG (always in mg/dl)
    axes[0].set_ylabel("glucose")
    bg_ylim = axes[0].get_ylim()
    a = min(bg_ylim[0], 0)
    b = max(1.1*bg_ylim[1], 300)
    axes[0].set_ylim([a, b])

    # handle case where IOB is never zero for entire plot
    axes[1].set_ylabel("IOB")
    iob_ylim = axes[1].get_ylim()
    a = min(1.1*iob_ylim[0], -1)
    b = max(1.1*iob_ylim[1], 10)
    axes[1].set_ylim([a, b])

    axes[2].set_ylabel("Sum Insulin")

    plt.draw()
    plt.pause(0.001)
    plt.pause(1)
    # for use in interactive screen: plt.draw();plt.pause(0.001)
    plt.savefig(outFile)
    plt.close(fig)


def main():
    foldername = "/Users/marion/dev/Loop_FreeAPS_Dash_Development/01-AlgorithmExperiments"
    devicestatus_filename = foldername + "/" + "devicestatus_output.txt"
    content1 = read_raw_nightscout(devicestatus_filename)
    nsDeviceDataDF = extract_devicestatus(content1)
    print(" *** nsDeviceDataDF:")
    print(nsDeviceDataDF)

    treatments_filename = foldername + "/" + "treatments_output.txt"
    content2 = read_raw_nightscout(treatments_filename)
    [test_designation, nsTreatmentsDF] = extract_treatments(content2)

    # create a sum for insulin but start at first value of 122 in the dataframe
    idx=nsDeviceDataDF[nsDeviceDataDF.glucose == 122].index[0]
    begin_time = nsDeviceDataDF.iloc[idx]['time']
    print(begin_time)
    #print(nsDeviceDataDF.iloc[idx])
    nsTreatmentsDF['insulin_cumsum'] = nsTreatmentsDF['insulin'].cumsum()
    print(" *** nsTreatmentsDF:")
    print(nsTreatmentsDF)

    # plot pandas dataframe containing Nightscout data
    thisOutFile = foldername + "/" + "preliminary_plot_20230615-1230.png"
    #label="Enter status for RC/IRC AB: Constant/GBAF"
    generatePlot(thisOutFile, test_designation, nsDeviceDataDF, nsTreatmentsDF)
    print(' *** plot created:     ', thisOutFile)


if __name__ == "__main__":
    main()

