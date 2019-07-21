# Load the Pandas libraries with alias 'pd' as so on...
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import math

# Read data from file 'filename.csv'
data = pd.read_csv("Output.csv")

# Preview the first 5 lines of the loaded data
print(data.head())

# Remove data after 8 mins
indexNames = data[data['Time'] >= 480].index
data.drop(indexNames, inplace=True)

# Add car range to dataframe
data['Left-Range'] = 0
data['Right-Range'] = 0
for idx, row in data.iterrows():
    data.loc[idx, 'LeftRange'] = data.loc[idx, 'Deviation'] - 0.875
    data.loc[idx, 'RightRange'] = data.loc[idx, 'Deviation'] + 0.875

#Plot Results
for x in range (0, 8):
    subset = data[data['Time'] > x * 60]
    subset = subset[subset['Time'] <= (x+1) * 60]
    dashes = [10, 5, 100, 5]

    #Standard Deviation of Center Line (Based on prior code)
    total = 0
    num = 0
    averagePos = np.average(subset.Deviation)
    for pos in subset.Deviation:
        total += (pos - averagePos) * (pos - averagePos)
        num += 1

    sdlp = math.sqrt(total / num)

    #Count of Severe and Mild Departures
    SEVERE_TH = 2.0
    MILD_TH = 1.75
    severe_count = 0
    mild_count = 0
    for vehicle_edge in subset.LeftRange:
        if vehicle_edge < -MILD_TH and vehicle_edge > -SEVERE_TH:
            mild_count += 1

    for vehicle_edge in subset.LeftRange:
        if vehicle_edge < -SEVERE_TH:
            severe_count += 1

    for vehicle_edge in subset.RightRange:
        if vehicle_edge > MILD_TH and vehicle_edge < SEVERE_TH:
            mild_count += 1

    for vehicle_edge in subset.LeftRange:
        if vehicle_edge > SEVERE_TH:
            severe_count += 1

    plt.title("Minute " + str(x+ 1))
    plt.axhline(y=0, dashes=dashes, color="black", label='Non-Visible Center Line')
    plt.axhline(y=-1.75, dashes=dashes, color="orange", label='Lane Markers')
    plt.axhline(y=1.75, dashes=dashes, color="orange")
    plt.plot(subset.Time, subset.Deviation, label="Car Deviation")
    plt.ylabel('Deviation (m)')
    plt.xlabel('Time (sec)')
    plt.ylim(-4, 4)
    plt.fill_between(subset.Time, subset.LeftRange, subset.RightRange, color="lightgray", label='Car Width')
    plt.legend(loc='upper left')
    plt.text((x+1) * 60, -3.75,
             'Std Dev: ' + str('{:.2f}'.format(sdlp)) +
             ', Severe Departures: '+str(severe_count)+
             ', Mild Departures: '+str(mild_count),
            verticalalignment='bottom', horizontalalignment='right',
            color='black', fontsize=10)

    plt.show()
    plt.savefig('Minute-'+str(x+1)+'.png')

