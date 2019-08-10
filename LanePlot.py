# Load the Pandas libraries with alias 'pd' as so on...
import math
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
import simdkalman

out_file = open('CV-Output.csv', 'w')
out_file.write("Segment, SD, Mild, Severe, CV\n")

files = os.listdir("Analysis")
print(files)

# Analysis Bins
first_window_size_secs = []

# Read data from file 'filename.csv'
for y in range(0, len(files)):
    file_name = files[y].split('.')[0]
    print("\nLoading: " + file_name)
    df = pd.read_csv("Analysis\\"+file_name+".txt")
    if file_name.split('-')[1] == "FirstDrive":
        first_window_size_secs = [180]
    elif file_name.split('-')[1] == "SecondDrive" or file_name.split('-')[1] == "ThirdDrive":
        first_window_size_secs = [120, 180, 180]
    else:
        print("Error")
        exit()

    # Preview the first 5 lines of the loaded data
    print(df.head())

    # Remove detection % line at end of file
    print(df.iloc[-1].Time)
    df.drop(df.tail(1).index, inplace=True)

    # Remove rows with 'None' deviation
    data = df.copy(deep=True)
    for idx, row in data.iterrows():
        if data.loc[idx, 'Deviation'] == "None":
            data.loc[idx, 'Deviation'] = "NaN"

    # Convert columns necessary for current calculations
    data['Time'] = data['Time'].astype(float)
    data['Quality'] = data['Quality'].astype(int)
    data['Deviation'] = data['Deviation'].astype(float)

    # Remove data after 8 minutes
    indexNames = data[data['Time'] >= 480].index
    data.drop(indexNames, inplace=True)

    # Apply Kalman smoothing
    kf = simdkalman.KalmanFilter(
        state_transition=np.array([[1, 1], [0, 1]]),
        process_noise=np.diag([0.1, 0.01]),
        observation_model=np.array([[1, 0]]),
        observation_noise=1.0)

    Dev_array = np.asarray(data.Deviation)

    # fit noise parameters to data with the EM algorithm (optional)
    try:
        kf = kf.em(Dev_array, n_iter=10)

        # smooth data
        smoothed = kf.smooth(Dev_array)
        data.Deviation = smoothed.observations.mean[:]
    except ZeroDivisionError:
        print("This error should only show up for L2 because the first drive is missing...")

    # Add car range to data frame
    data['Left-Range'] = 0
    data['Right-Range'] = 0
    for idx, row in data.iterrows():
        data.loc[idx, 'LeftRange'] = data.loc[idx, 'Deviation'] - 0.91
        data.loc[idx, 'RightRange'] = data.loc[idx, 'Deviation'] + 0.91

    # Plot Results
    for x in range(0, len(first_window_size_secs)):
        if x == 0:
            subset = data[data['Time'] > 0]
            subset = subset[subset['Time'] <= first_window_size_secs[x]]
            text_pos = first_window_size_secs[x]
        elif x == 1:
            subset = data[data['Time'] > first_window_size_secs[x-1]]
            subset = subset[subset['Time'] <= (first_window_size_secs[x-1] + first_window_size_secs[x])]
            text_pos = (first_window_size_secs[x-1] + first_window_size_secs[x])
        elif x == 2:
            subset = data[data['Time'] > (first_window_size_secs[x-1] + first_window_size_secs[x])]
            subset = subset[subset['Time'] <= (first_window_size_secs[x - 2] + first_window_size_secs[x - 1] + first_window_size_secs[x])]
            text_pos = (first_window_size_secs[x - 2] + first_window_size_secs[x - 1] + first_window_size_secs[x])
        else:
            print("Error")
            exit()

        dashes = [10, 5, 100, 5]

        # Deviation of Center Line (Based on prior code)
        total = 0
        num = 0
        averagePos = np.average(subset.Deviation)
        for pos in subset.Deviation:
            total += (pos - averagePos) * (pos - averagePos)
            num += 1

        try:
            sdlp = math.sqrt(total / num)
        except ZeroDivisionError:
            print("Zero Division Error Handling")
            sdlp = 0

        # Count of Severe and Mild Departures
        SEVERE_TH = 2.5
        MILD_TH = 1.75
        severe_count = 0
        mild_count = 0

        prev = None
        for vehicle_edge in subset.LeftRange:
            if -MILD_TH > vehicle_edge > -SEVERE_TH:
                if prev is None:
                    mild_count += 1
                elif prev is not None and -MILD_TH < prev:
                    mild_count += 1
            prev = vehicle_edge

        prev = None
        for vehicle_edge in subset.LeftRange:
            if vehicle_edge < -SEVERE_TH:
                if prev is None:
                    severe_count += 1
                elif prev is not None and -SEVERE_TH < prev:
                    severe_count += 1
            prev = vehicle_edge

        prev = None
        for vehicle_edge in subset.RightRange:
            if MILD_TH < vehicle_edge < SEVERE_TH:
                if prev is None:
                    mild_count += 1
                elif prev is not None and prev < MILD_TH:
                    mild_count += 1
            prev = vehicle_edge

        prev = None
        for vehicle_edge in subset.LeftRange:
            if vehicle_edge > SEVERE_TH:
                if prev is None:
                    severe_count += 1
                elif prev is not None and prev < SEVERE_TH:
                    severe_count += 1
            prev = vehicle_edge

        subset_2 = df.copy(deep=True)
        # Calculate how much of the time is covered by OpenCV
        try:
            for idx, row in subset_2.iterrows():
                last_idx = idx
                if subset_2.loc[idx, 'Deviation'] == "None" and subset_2.loc[idx - 1, 'Deviation'] is not None and \
                        subset_2.loc[idx - 1, 'Deviation'] != "None" and subset_2.loc[idx + 1, 'Deviation'] is not None and \
                        subset_2.loc[idx + 1, 'Deviation'] != "None":
                    subset_2.drop(idx, inplace=True)
        except KeyError:
            print("Key Error: " + str(idx+1))
            subset_2.drop(last_idx, inplace=True)

        subset_2['Time'] = subset_2['Time'].astype(float)


        if x == 0:
            subset_2 = subset_2[subset_2['Time'] > 0]
            subset_2 = subset_2[subset_2['Time'] <= first_window_size_secs[x]]

        elif x == 1:
            subset_2 = subset_2[subset_2['Time'] > first_window_size_secs[x - 1]]
            subset_2 = subset_2[subset_2['Time'] <= (first_window_size_secs[x - 1] + first_window_size_secs[x])]

        elif x == 2:
            subset_2 = subset_2[subset_2['Time'] > (first_window_size_secs[x - 1] + first_window_size_secs[x])]
            subset_2 = subset_2[subset_2['Time'] <= (
                        first_window_size_secs[x - 2] + first_window_size_secs[x - 1] + first_window_size_secs[x])]

        else:
            print("Error")
            exit()

        noDetections = 0
        measurements = 0

        for pos in subset_2.Deviation:
            measurements += 1
            if pos == 'None':
                noDetections += 1


        subset_2 = subset_2[subset_2['Deviation'] == 'None']

        plt.title(file_name+'-'+str(x)+'-'+str(first_window_size_secs[x]))
        plt.axhline(y=0, dashes=dashes, color="black", label='Center Line')
        plt.axhline(y=-1.75, dashes=dashes, color="orange", label='Lane Markers')
        plt.axhline(y=1.75, dashes=dashes, color="orange")
        plt.plot(subset.Time, subset.Deviation, label="Car Deviation")
        plt.ylabel('Deviation (m)')
        plt.xlabel('Time (sec)')
        plt.ylim(-5.5, 5.5)
        plt.fill_between(subset.Time, subset.LeftRange, subset.RightRange, color="lightgray", label='Car Width')

        try:
            plt.text(text_pos, -4.75,
                     'Std Dev: ' + str('{:.2f}'.format(sdlp)) +
                     ', Severe Departures: ' + str(severe_count) +
                     ', Mild Departures: ' + str(mild_count) +
                     ', CV Coverage: ' + str('{:.2f}'.format(1 - (noDetections / measurements))) + "%",
                     verticalalignment='bottom', horizontalalignment='right',
                     color='black', fontsize=8)
        except ZeroDivisionError:
            print("Zero Division Error Handling")
            plt.text(text_pos, -4.75,
                     'Std Dev: ' + str('{:.2f}'.format(sdlp)) +
                     ', Severe Departures: ' + str(severe_count) +
                     ', Mild Departures: ' + str(mild_count) +
                     ', CV Coverage: Error',
                     verticalalignment='bottom', horizontalalignment='right',
                     color='black', fontsize=8)

        plt.text(text_pos, -5.25,
                 '(Low Confidence Areas)',
                 verticalalignment='bottom', horizontalalignment='right',
                 color='red', alpha=0.5, fontsize=7)

        for missing in subset_2.Time:
            plt.axvline(missing, ymin=0.35, ymax=.65, color="red", alpha=0.1, zorder=-1)

        plt.legend(loc='upper left')
        plt.savefig('Output\\'+file_name+'-'+str(x)+'-'+str(first_window_size_secs[x])+'.png')
        #plt.show()
        plt.close()

        #Write Data
        out_file.write(file_name+'-'+str(x)+'-'+str(first_window_size_secs[x]))
        out_file.write(",")
        out_file.write(str('{:.2f}'.format(sdlp)))
        out_file.write(",")
        out_file.write(str(mild_count))
        out_file.write(",")
        out_file.write(str(severe_count))
        out_file.write(",")
        if measurements != 0:
            out_file.write(str(str('{:.2f}'.format(1 - (noDetections / measurements)))))
        else:
            out_file.write(str('NaN'))
        out_file.write("\n")

out_file.close()
