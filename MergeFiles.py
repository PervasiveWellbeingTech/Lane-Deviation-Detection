import os
import subprocess
import time
from stat import S_ISREG, ST_CTIME, ST_MODE

directory_list = []

# Navigate from root to the target directory
dir_path = os.path.dirname(os.path.realpath(__file__))
print(dir_path)

assembled_file_ending = ''
for directory in directory_list:
    for x in range(0, 2):
        if x == 0:
            print('Moving to new directory, left folder...')
            assembled_file_ending = "_Left_Assembled.MP4"
            os.chdir('Data\\' + directory + "\\Left\\")
            dir_path = os.getcwd()
            print(dir_path)
        elif x == 1:
            print('Moving to right folder...')
            assembled_file_ending = "_Right_Assembled.MP4"
            os.chdir('..\\..\\..\\Data\\' + directory + '\\Right\\')
            dir_path = os.getcwd()
            print(dir_path)
        else:
            print("Error")
            exit()

        # Get the file and file information in the current directory
        entries = (os.path.join(dir_path, fn) for fn in os.listdir(dir_path))
        entries = ((os.stat(path), path) for path in entries)
        entries = ((stat[ST_CTIME], path) for stat, path in entries if S_ISREG(stat[ST_MODE]))

        # Build assembly list; pretty much assumes folders are clean
        # TODO: Add additional filtering to files and folders
        video_command = ["("]

        previous_file = False
        for creation_date, path in sorted(entries):
            if path.endswith(directory + assembled_file_ending):
                os.remove(directory + assembled_file_ending)

            elif path.endswith('.MP4'):
                print(time.ctime(creation_date), os.path.basename(path))
                if previous_file:
                    video_command.append("&")
                    video_command.append("echo")
                    video_command.append("file '" + os.path.basename(path) + "'")
                else:
                    previous_file = True
                    video_command.append("echo")
                    video_command.append("file '" + os.path.basename(path) + "'")

        video_command.append(")")
        video_command.append(">")
        video_command.append("list.txt")

        # Execute commands
        subprocess.Popen(video_command, shell=True).wait()

        with open('list.txt', 'r') as infile, open('cleaned.txt', 'w') as outfile:
            data = infile.read()
            data = data.replace("\"", "")
            outfile.write(data)

        video_command = ["ffmpeg", "-f", "concat", "-i", "cleaned.txt", "-c", "copy", str(directory
                                                                                          + assembled_file_ending)]
        print("Merging files...")
        subprocess.Popen(video_command, shell=True).wait()
        os.remove('cleaned.txt')
        os.remove('list.txt')
        print("Completed.")

    # Transition directories
    print('Moving to root directory...')
    assembled_file_ending = "_Right_Assembled.MP4"
    os.chdir('..\\..\\..\\')
    dir_path = os.getcwd()
    print(dir_path)

# Done
print("Assembly process completed!")
