# Load the Pandas libraries with alias 'pd' as so on...
import math
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.signal import savgol_filter

# Variables
WITH_FILTERING = True

# Read data from file 'filename.csv'
df = pd.read_csv("L37-ThirdDrive-Output.txt")
if WITH_FILTERING:
    filterText = "-filtered"
else:
    filterText = "-raw"

# Preview the first 5 lines of the loaded data
print(df.head())

# Remove detection % line at end of file
print(df.iloc[-1].Time)
df.drop(df.tail(1).index, inplace=True)

# Filter out single instance (non-consecutive moments) of None deviation calculations
if WITH_FILTERING:
    try:
        for idx, row in df.iterrows():
            last_idx = idx
            if df.loc[idx, 'Deviation'] == "None" and df.loc[idx - 1, 'Deviation'] is not None and \
                    df.loc[idx - 1, 'Deviation'] != "None" and df.loc[idx + 1, 'Deviation'] is not None and \
                    df.loc[idx + 1, 'Deviation'] != "None":
                df.drop(idx, inplace=True)
    except KeyError:
        print("KeyError: " + str(last_idx))
        df.drop(last_idx, inplace=True)

# Remove rows with 'None' deviation
data = df[df['Deviation'] != 'None'].copy(deep=True)

# Convert columns necessary for current calculations
data['Time'] = data['Time'].astype(float)
data['Quality'] = data['Quality'].astype(int)
data['Deviation'] = data['Deviation'].astype(float)

# Remove data after 8 minutes
indexNames = data[data['Time'] >= 480].index
data.drop(indexNames, inplace=True)

# Add car range to data frame
for idx, row in data.iterrows():
    data.loc[idx, 'LeftRange'] = data.loc[idx, 'Deviation'] - 0.91
    data.loc[idx, 'RightRange'] = data.loc[idx, 'Deviation'] + 0.91

# Filter deviation files
if WITH_FILTERING:
    dev_hat = savgol_filter(data["Deviation"], 5, 3)
    data["Deviation"] = dev_hat

# Static plot variables
dashes = [10, 5, 100, 5]

# Plot Results
for x in range(0, 8):
    subset = data[data['Time'] > x * 60]
    subset = subset[subset['Time'] <= (x + 1) * 60]

    # Standard Deviation of Center Line (Based on prior code)
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
    SEVERE_TH = 2.61
    MILD_TH = 1.82
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
            elif prev is not None and -MILD_TH < prev:
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
            elif prev is not None and prev < MILD_TH:
                severe_count += 1
        prev = vehicle_edge


    # Calculate how much of the minute is covered by OpenCV
    subset_2 = df.copy(deep=True)
    subset_2['Time'] = subset_2['Time'].astype(float)
    subset_2 = subset_2[subset_2['Time'] > x * 60]
    subset_2 = subset_2[subset_2['Time'] <= (x + 1) * 60]

    noDetections = 0
    measurements = 0

    for pos in subset_2.Deviation:
        measurements += 1
        if pos == 'None':
            noDetections += 1

    subset_2 = subset_2[subset_2['Deviation'] == 'None']

    plt.title("Minute " + str(x + 1) + filterText)
    plt.axhline(y=0, dashes=dashes, color="black", label='Center Line')
    plt.axhline(y=-1.82, dashes=dashes, color="orange", label='Lane Markers')
    plt.axhline(y=1.82, dashes=dashes, color="orange")
    plt.plot(subset.Time, subset.Deviation, label="Car Deviation")
    plt.ylabel('Deviation (m)')
    plt.xlabel('Time (sec)')
    plt.ylim(-5.5, 5.5)
    plt.fill_between(subset.Time, subset.LeftRange, subset.RightRange, color="lightgray", label='Car Width')

    try:
        plt.text((x + 1) * 60, -4.75,
                 'Std Dev: ' + str('{:.2f}'.format(sdlp)) +
                 ', Severe Departures: ' + str(severe_count) +
                 ', Mild Departures: ' + str(mild_count) +
                 ', CV Coverage: ' + str('{:.2f}'.format(1 - (noDetections / measurements))) + "%",
                 verticalalignment='bottom', horizontalalignment='right',
                 color='black', fontsize=8)

    except ZeroDivisionError:
        print("Zero Division Error Handling")
        plt.text((x + 1) * 60, -4.75,
                 'Std Dev: ' + str('{:.2f}'.format(sdlp)) +
                 ', Severe Departures: ' + str(severe_count) +
                 ', Mild Departures: ' + str(mild_count) +
                 ', CV Coverage: Error',
                 verticalalignment='bottom', horizontalalignment='right',
                 color='black', fontsize=8)

    plt.text((x + 1) * 60, -5.25,
             '(Low Confidence Areas)',
             verticalalignment='bottom', horizontalalignment='right',
             color='red', alpha=0.5, fontsize=7)

    for missing in subset_2.Time:
        plt.axvline(missing, ymin=0.35, ymax=.65, color="red", alpha=0.1, zorder=-1)

    plt.legend(loc='upper left')
    plt.savefig('Minute-' + str(x + 1) + filterText + '.png')
    plt.show()
