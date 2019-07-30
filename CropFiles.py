import pandas as pd
import subprocess

MappingFilePath = "Data\\2019-07-26-DrivingLogs.csv"
df = pd.read_csv(MappingFilePath)
rows, cols = df.shape

for x in range(0, rows):
    print("Trimming: Data\\" + df.loc[x].Group + " Group\\" + df.loc[x].Participant + "\\" + df.loc[x].Video + "\\"
          + df.loc[x].Participant
          + "_" + df.loc[x].Video + "_Assembled.MP4")

    # First Drive
    video_command = ["ffmpeg", "-i", "Data\\" + df.loc[x].Group + " Group\\" + df.loc[x].Participant
                     + "\\"+df.loc[x].Video+"\\" + df.loc[x].Participant + "_"+df.loc[x].Video+"_Assembled.MP4", "-ss",
                     df.loc[x].First_Start, "-t",
                     df.loc[x].First_Duration, "-c", "copy",
                     "Data\\" + df.loc[x].Group + " Group\\" + df.loc[x].Participant + "\\"+df.loc[x].Video+"\\"
                     + df.loc[x].Participant
                     + "_First_Drive_"+df.loc[x].Video+".MP4"]

    print("First Drive Video: " + df.loc[x].First_Duration)
    subprocess.call(video_command, shell=True)

    # Second Drive
    video_command = ["ffmpeg", "-i", "Data\\" + df.loc[x].Group + " Group\\" + df.loc[x].Participant
                     + "\\"+df.loc[x].Video+"\\" + df.loc[x].Participant + "_"+df.loc[x].Video+"_Assembled.MP4", "-ss",
                     df.loc[x].Second_Start, "-t",
                     df.loc[x].Second_Duration, "-c", "copy",
                     "Data\\" + df.loc[x].Group + " Group\\" + df.loc[x].Participant + "\\"+df.loc[x].Video+"\\"
                     + df.loc[x].Participant
                     + "_Second_Drive_"+df.loc[x].Video+".MP4"]

    print("Second Drive Video: " + df.loc[x].Second_Duration)
    subprocess.call(video_command, shell=True)

    # Second Drive
    video_command = ["ffmpeg", "-i", "Data\\" + df.loc[x].Group + " Group\\" + df.loc[x].Participant
                     + "\\"+df.loc[x].Video+"\\" + df.loc[x].Participant + "_"+df.loc[x].Video+"_Assembled.MP4", "-ss",
                     df.loc[x].Third_Start, "-t",
                     df.loc[x].Third_Duration, "-c", "copy",
                     "Data\\" + df.loc[x].Group + " Group\\" + df.loc[x].Participant + "\\"+df.loc[x].Video+"\\"
                     + df.loc[x].Participant
                     + "_Third_Drive_"+df.loc[x].Video+".MP4"]

    print("Third Drive Video: " + df.loc[x].Third_Duration)
    subprocess.call(video_command, shell=True)

print("Program Completed")
