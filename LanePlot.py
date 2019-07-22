# Load the Pandas libraries with alias 'pd' as so on...
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import math

# Read data from file 'filename.csv'
df = pd.read_csv("Output.csv")

# Preview the first 5 lines of the loaded data
print(df.head())

# Remove detection % line at end of file
print(df.iloc[-1].Time)
df.drop(df.tail(1).index, inplace=True)

# Remove rows with 'None' deviation
data = df[df['Deviation'] != 'None']

# Convert columns necessary for current calculations
data.is_copy = None
data['Time'] = data['Time'].astype(float)
data['Quality'] = data['Quality'].astype(int)
data['Deviation'] = data['Deviation'].astype(float)

# Remove data after 8 minutes
indexNames = data[data['Time'] >= 480].index
data.drop(indexNames, inplace=True)

# Add car range to data frame
data['Left-Range'] = 0
data['Right-Range'] = 0
for idx, row in data.iterrows():
    data.loc[idx, 'LeftRange'] = data.loc[idx, 'Deviation'] - 0.875
    data.loc[idx, 'RightRange'] = data.loc[idx, 'Deviation'] + 0.875

# Plot Results
for x in range(0, 8):
    subset = data[data['Time'] > x * 60]
    subset = subset[subset['Time'] <= (x + 1) * 60]
    dashes = [10, 5, 100, 5]

    # Standard Deviation of Center Line (Based on prior code)
    total = 0
    num = 0
    averagePos = np.average(subset.Deviation)
    for pos in subset.Deviation:
        total += (pos - averagePos) * (pos - averagePos)
        num += 1

    sdlp = math.sqrt(total / num)

    # Count of Severe and Mild Departures
    SEVERE_TH = 2.0
    MILD_TH = 1.75
    severe_count = 0
    mild_count = 0
    for vehicle_edge in subset.LeftRange:
        if -MILD_TH > vehicle_edge > -SEVERE_TH:
            mild_count += 1

    for vehicle_edge in subset.LeftRange:
        if vehicle_edge < -SEVERE_TH:
            severe_count += 1

    for vehicle_edge in subset.RightRange:
        if MILD_TH < vehicle_edge < SEVERE_TH:
            mild_count += 1

    for vehicle_edge in subset.LeftRange:
        if vehicle_edge > SEVERE_TH:
            severe_count += 1

    # Calculate how much of the minute is covered by OpenCV
    subset_2 = df
    subset.is_copy = None
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

    plt.title("Minute " + str(x + 1))
    plt.axhline(y=0, dashes=dashes, color="black", label='Center Line')
    plt.axhline(y=-1.75, dashes=dashes, color="orange", label='Lane Markers')
    plt.axhline(y=1.75, dashes=dashes, color="orange")
    plt.plot(subset.Time, subset.Deviation, label="Car Deviation")
    plt.ylabel('Deviation (m)')
    plt.xlabel('Time (sec)')
    plt.ylim(-5.5, 5.5)
    plt.fill_between(subset.Time, subset.LeftRange, subset.RightRange, color="lightgray", label='Car Width')

    plt.text((x + 1) * 60, -4.75,
             'Std Dev: ' + str('{:.2f}'.format(sdlp)) +
             ', Severe Departures: ' + str(severe_count) +
             ', Mild Departures: ' + str(mild_count) +
             ', CV Coverage: ' + str('{:.2f}'.format(1 - (noDetections / measurements))) + "%",
             verticalalignment='bottom', horizontalalignment='right',
             color='black', fontsize=8)

    plt.text((x + 1) * 60, -5.25,
             '(Low Confidence Areas)',
             verticalalignment='bottom', horizontalalignment='right',
             color='red', alpha=0.5, fontsize=7)

    for missing in subset_2.Time:
        plt.axvline(missing, ymin=0.35, ymax=.65, color="red", alpha=0.1, zorder=-1)

    plt.legend(loc='upper left')
    plt.savefig('Minute-' + str(x + 1) + '.png')
    plt.show()
