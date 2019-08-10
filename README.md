# Lane-Deviation-Detection

# Process

Assemble GoPro data into a directory of MP4s with each session containing folders for the left and right videos. Run MergeFiles.py to create one contiguous video based on the creation timestamp for each session and eash side. Then, manually timecode each video to extract the 3 minutes from the familiarization drive and the 8 minutes for each of the next two drives in each session. This data needs to be added to a configuration file that CropFiles, LaneDetection, and LanePlot will all use. Once the data has been cropped/trimmed, Lane Detection can be applied to create a CSV of raw data for each session. Finally, Lane Detection will filter, analyze, and plot this data. FilterScript is an auxillary script for looking at the results from an individual session.

# File Overview

MergeFiles.py - This script will walk through a directory of GoPro videos and merge them based on their creation timestamp.

CropFiles.py - Provide this script with a list of directories and files as well as manually generated time codes and it will trim videos into different segements for future analysis. This script is designed to run across a directory based on a configuration file.

LaneDetection.py - Based on the pre-calculated parameters of the car and garage, this script will calculate the distances from the left and right lane markers as well as the deviation from the center line in. The output file is in meters, but the display is in feet. This script is designed to run across a directory based on a configuration file.

LanePlot.py - will filter the output from LaneDetection.py, apply a Kalman filter, and provide various metrics for future analysis. This script is designed to run across a directory based on a configuration file.

FilterScript.put - Does the same thing as LanePlot in terms of filtering, but allows you to look at an individiaul output file.

# Configuration File Schema

Group - In the data folder will be Intervention and Control sub folders, tell the script in what folder the session is in.

Participant - The participant ID, used to walk directories

Video	- Left or Right side

First_Start - Timecode for the start of the first drive used by CropFiles

First_End	- Timecode for the end of the first drive used by CropFiles

First_Duration - Duration of the video; unused but helpful for troubleshooting output

Second_Start - Timecode for the start of the second drive used by CropFiles

Second_End - Timecode for the end of the second drive used by CropFiles

Second_Duration - Duration of the video; unused but helpful for troubleshooting output

Third_Start - Timecode for the start of the third drive used by CropFiles

Third_End - Timecode for the end of the third drive used by CropFiles

Third_Duration - Duration of the video; unused but helpful for troubleshooting output

Video_Duration - Duration of the video; unused but helpful for troubleshooting output

crop_adjust	- adjust the crop window because the camera was installed wrong

camera_flip - flip the camera because someone installed it upside down

e.g.,

![Image of ConfigurationFile](https://github.com/PervasiveWellbeingTech/Lane-Deviation-Detection/blob/master/imgs/ConfigExample.PNG?raw=true)

# Dependencies
Relies on Python3 and PIP to install standard dependencies (e.g., numpy, pandas, matplotlib); the only non-standard package is the Kalman filter, but it too was easy to install with PIP. Tested using PyCharm IDE and a Windows 10 machine.
