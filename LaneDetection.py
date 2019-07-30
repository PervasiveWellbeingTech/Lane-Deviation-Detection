import cv2
import numpy as np
import math


def apply_brightness_contrast(input_img, brightness=0, contrast=0):
    if brightness != 0:
        if brightness > 0:
            shadow = brightness
            highlight = 255
        else:
            shadow = 0
            highlight = 255 + brightness
        alpha_b = (highlight - shadow) / 255
        gamma_b = shadow

        buf = cv2.addWeighted(input_img, alpha_b, input_img, 0, gamma_b)
    else:
        buf = input_img.copy()

    if contrast != 0:
        f = 131 * (contrast + 127) / (127 * (131 - contrast))
        alpha_c = f
        gamma_c = 127 * (1 - f)

        buf = cv2.addWeighted(buf, alpha_c, buf, 0, gamma_c)

    return buf


if __name__ == '__main__':
    # initialize video variables
    VIDEO_WIDTH = 300  # of 1920?
    VIDEO_HEIGHT = 1080
    heightRight = 500  # this was originally 600, but these variables are currently unused.
    heightLeft = 500  # unused

    # Estimated width in meters of lane, car, and FOV of camera (assumed correct)
    LANE_WIDTH = 3.65  # 12 Feet
    CAR_WIDTH = 1.75  # Assumed correct
    CAM_WIDTH = 1.15  # Updated based on the new camera crops...

    RightSideConversion = CAM_WIDTH

    # white lane lines (related to color filter code below)
    # line_color = [([126, 129, 136], [126, 129, 136])]

    # arrays and variables that keep track of deviation and position for later averaging
    leftList = []  # estimated distance between the wheel and the left lane
    rightList = []  # estimated distance between the wheel and the right lane
    devList = []
    posList = []
    timeList = []  # timestamp of the measurement relative to the elapse time of the video
    typeList = []  # quality of the detection:
    # (2 = both lanes, -1 = left lane only, 1 = right lane only,
    # 0 = no lanes detected because they either aren't there or the lighting is bad)
    idx = 0
    timeCount = 0

    '''Start of scrubbing through video code below'''
    skip_ahead = 150
    cur_pos = 0

    # Open output files
    file = open('Output.txt', 'w')

    # Load data files
    leftCamFile = "Data\\L2\\Left\\L2_Left_ThirdDrive.MP4"
    rightCamFile = "Data\\L2\\Right\\L2_Right_ThirdDrive.MP4"
    cap1 = cv2.VideoCapture(leftCamFile)
    cap2 = cv2.VideoCapture(rightCamFile)

    while True:
        timestamp = round(cap1.get(cv2.CAP_PROP_POS_MSEC) / 1000, 2)
        ret1, frame1 = cap1.read()
        ret2, frame2 = cap2.read()
        avgMeters1 = "?"
        avgMeters2 = "?"

        '''TODO: Figure out how to scrub through sections of video faster'''
        if cur_pos < skip_ahead:
            cur_pos = cur_pos + 1
            continue

        out = False
        valid = True
        if frame1 is not None and frame2 is not None:
            # Crop the center of frame to reduce distortion
            frame1_original = frame1[185:1440, 830:1130]
            frame2_original = frame2[185:1440, 830:1130]

            '''This seems to work reasonably well to improve recognition in the image'''
            frame1 = apply_brightness_contrast(frame1_original, brightness=50, contrast=75)
            frame2 = apply_brightness_contrast(frame2_original, brightness=50, contrast=75)

            '''
            This code was applying a color-based filter, but this seems impractical
            as it throws out all the detections in the test data that was available to me at the time
            '''

            '''
            for (lower, upper) in line_color:
                lower = np.array(lower, dtype="uint8")
                upper = np.array(upper, dtype="uint8")

                mask1 = cv2.inRange(frame1, lower, upper)
                mask2 = cv2.inRange(frame2, lower, upper)

                output1 = cv2.bitwise_and(frame1, frame1, mask=mask1)
                output2 = cv2.bitwise_and(frame2, frame2, mask=mask2)
            '''

            gray1 = cv2.cvtColor(frame1, cv2.COLOR_RGB2RGBA)
            gray2 = cv2.cvtColor(frame2, cv2.COLOR_RGB2RGBA)

            edges1 = cv2.Canny(gray1, 60, 150, apertureSize=3)
            edges2 = cv2.Canny(gray2, 60, 150, apertureSize=3)

            lines1 = cv2.HoughLines(edges1, 1, np.pi / 180, 60)
            lines2 = cv2.HoughLines(edges2, 1, np.pi / 180, 65)

            '''
            This next commented out line was related to a prior assumption that both lines will be generally
            visible in the videos, it is unclear if that's is a fair assumption based on my test files. It is possible
            that the data I am using is just an example of when the camera's were accidentally misaligned here vs 
            a systemic issue
            '''

            # if lines1 is not None and lines2 is not None:
            total = 0
            count = 0
            leftLines = False
            rightLines = False

            if lines1 is not None and (len(lines1) < 100):
                for x in range(0, len(lines1)):
                    for rho, theta in lines1[x]:

                        a = np.cos(theta)
                        b = np.sin(theta)
                        x0 = a * rho
                        y0 = b * rho

                        x1 = int(x0 + 1000 * (-b))
                        y1 = int(y0 + 1000 * a)
                        x2 = int(x0 - 1000 * (-b))
                        y2 = int(y0 - 1000 * a)

                        '''
                        The original code  here w.r.t. heightLeft and the ranging on y1 and y2 
                        seem to make the assumption that the line is going to be of a certain size and perhaps to try
                        and remove other larger lines like the yellow-painted lane indicators. This works okay, but
                        the line can become heavily distorted based on distance, speed/motion, etc. so this seems 
                        impractical. Trying to reduce these distortions is probably a heavy lift, but relaxing
                        these conditions seems to work well enough. 
                        '''

                        # if (x2 - x1) is not 0 and (y1 > heightLeft) and (-200 <= (y1 - y2) <= 200):
                        if (x2 - x1) is not 0 and math.fabs(y1 - y2) >= 30:
                            k = (y2 - y1) / (x2 - x1)
                            b = y1 - k * x1
                            yf = k * VIDEO_WIDTH + b
                            mid_y = int(b + yf) / 2
                            total += mid_y
                            count += 1
                            cv2.line(frame1_original, (x1, y1), (x2, y2), (0, 0, 255), 2)
                            leftLines = True

                if count != 0:
                    avg1 = int(total / count)
                    avgMeters1 = CAM_WIDTH / VIDEO_HEIGHT * avg1
                    cv2.line(frame1_original, (0, avg1), (frame1[0].size, avg1), (255, 255, 0), 2)

            else:
                valid = False

            total = 0
            count = 0
            if lines2 is not None and (len(lines2) < 100):
                for x in range(0, len(lines2)):
                    for rho, theta in lines2[x]:
                        a = np.cos(theta)
                        b = np.sin(theta)
                        x0 = a * rho
                        y0 = b * rho
                        x1 = int(x0 + 1000 * (-b))
                        y1 = int(y0 + 1000 * a)
                        x2 = int(x0 - 1000 * (-b))
                        y2 = int(y0 - 1000 * a)

                        '''
                        The original code  here w.r.t. heightRight and the ranging on y1 and y2 
                        seem to make the assumption that the line is going to be of a certain size and perhaps to try
                        and remove other larger lines like the yellow-painted lane indicators. This works okay, but
                        the line can become heavily distorted based on distance, speed/motion, etc. so this seems 
                        impractical. Trying to reduce these distortions is probably a heavy lift, but relaxing
                        these conditions seems to work well enough. 
                        '''

                        # if (x2 - x1) is not 0 and (y1 > heightRight) and (-200 <= (y1 - y2) <= 200):
                        if (x2 - x1) is not 0 and math.fabs(y1 - y2) >= 30:
                            k = (y2 - y1) / (x2 - x1)
                            b = y1 - k * x1
                            yf = k * VIDEO_WIDTH + b
                            mid_y = int(b + yf) / 2
                            total += mid_y
                            count += 1
                            cv2.line(frame2_original, (x1, y1), (x2, y2), (0, 0, 255), 2)
                            rightLines = True

                if count != 0:
                    avg2 = int(total / count)
                    avgMeters2 = CAM_WIDTH / VIDEO_HEIGHT * (VIDEO_HEIGHT - avg2)
                    cv2.line(frame2_original, (0, avg2), (frame2[0].size, avg2), (255, 255, 0), 2)

            else:
                valid = False

            if valid:
                if leftLines and rightLines:
                    dev = avgMeters1 - avgMeters2
                    devList.append(dev)

                timeCount += 20

                if timeCount >= 200 and len(devList) != 0:
                    timeList.append(str(timestamp))
                    averageDev = np.median(devList)
                    posList.append('{:.2f}'.format(averageDev - 0.725))

                    try:
                        leftList.append('{:.2f}'.format(avgMeters1))
                    except ValueError:
                        print("Value Error Handling: leftList.append() issue")
                        leftList.append(None)

                    try:
                        rightList.append('{:.2f}'.format(avgMeters2))
                    except ValueError:
                        print("Value Error Handling: rightList.append() issue")
                        leftList.append(None)

                    typeList.append(2)
                    timeCount = 0
                    devList = []
                    idx += 1

                    try:
                        # noinspection PyTypeChecker
                        print(str('{:.2f}'.format(round(timestamp, 2))) + " - Quality: B,  Deviation: " +
                              str('{:.2f}'.format(round((averageDev - 0.725) * 3.25), 2)) + " ft, Left: " +
                              str('{:.2f}'.format(round(avgMeters1 * 3.28, 2))) + " ft , Right: " +
                              str('{:.2f}'.format(round((RightSideConversion - avgMeters2) * 3.28), 2)) + " ft")
                    except TypeError:
                        print("Type Error Handling: Weird multiplication issue")

            else:
                timestamp = round(cap1.get(cv2.CAP_PROP_POS_MSEC) / 1000, 2)
                timeCount += 20

                if timeCount >= 200:
                    timeCount = 0
                    devList = []

                    '''
                    Converting output to feet (1 meter = 3.28 feet)
                    Position is roughly the deviation from the center of line, in feet, where 2.98 is half the
                    width of the car (2.87 in feet)
                    '''

                    if avgMeters1 == "?":
                        display1 = "?"

                    else:
                        display1 = str('{:.2f}'.format(round((avgMeters1 * 3.28), 2))) + " ft"

                    if avgMeters2 == "?":
                        display2 = "?"

                    else:
                        temp = RightSideConversion - avgMeters2
                        display2 = str('{:.2f}'.format(round((temp * 3.28), 2))) + " ft"

                    if display1 != "?":
                        idx += 1
                        timeList.append(str('{:.2f}'.format(timestamp)))
                        posList.append('{:.2f}'.format((-round(6 - ((avgMeters1 * 3.28) + 2.87), 2)) * 0.3048))
                        print(str('{:.2f}'.format(round(timestamp, 2)))
                              + " - Quality: L,  "
                              + "Deviation: " + str('{:.2f}'.format(-round(6 - ((avgMeters1 * 3.28) + 2.87), 2)))
                              + " ft, Left: " + display1
                              + ", Right: " + display2)

                        leftList.append('{:.2f}'.format(avgMeters1))
                        rightList.append(None)
                        typeList.append(-1)

                    elif display2 != "?":
                        idx += 1
                        timeList.append(str('{:.2f}'.format(timestamp)))
                        temp = RightSideConversion - avgMeters2
                        posList.append('{:.2f}'.format(round(6 - ((temp * 3.28) + 2.87), 2) * 0.3048))
                        print(str('{:.2f}'.format(round(timestamp, 2))) + " - Quality: R, "
                              + "Deviation: " + str('{:.2f}'.format(round(6 - ((temp * 3.28) + 2.87), 2)))
                              + " ft, Left: " + display1
                              + ", Right: " + display2)

                        leftList.append(None)
                        rightList.append('{:.2f}'.format(avgMeters2))
                        typeList.append(1)

                    else:
                        idx += 1
                        timeList.append(str('{:.2f}'.format(timestamp)))
                        posList.append(None)
                        print(str('{:.2f}'.format(round(timestamp, 2))) + " - Quality: N, "
                              + " Deviation: " + str("?")
                              + ", Left: " + display1
                              + ", Right: " + display2)

                        leftList.append(None)
                        rightList.append(None)
                        typeList.append(0)

            ''' 
            Position the output videos with left video on left and right video on right
            '''

            # rotate cw
            out = cv2.transpose(frame1_original)
            out = cv2.flip(out, flipCode=1)
            cv2.imshow('frame1', out)

            out = cv2.transpose(edges1)
            out = cv2.flip(out, flipCode=1)
            cv2.imshow('raw1', out)

            # rotate ccw
            out = cv2.transpose(frame2_original)
            out = cv2.flip(out, flipCode=0)
            cv2.imshow('frame2', out)

            out = cv2.transpose(edges2)
            out = cv2.flip(out, flipCode=0)
            cv2.imshow('raw2', out)

            '''
            End sequence command and write output if available
            '''

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            ''' Helpful for debugging purposes '''
            # if timestamp > 15:
            #     break

        else:
            break

    # Calculate Mean Lateral Position
    if len(posList) == 0:
        print("No positional data? Exiting...")
        cap1.release()
        cap2.release()

        file.close()
        file.close()

        cv2.destroyAllWindows()

        exit()

    print("Writing results...")
    curr = 0
    measurements = idx
    noDetections = 0
    percentPossibleDetection = 0
    file.write("Time")
    file.write(",")
    file.write("Quality")
    file.write(",")
    file.write("Deviation")
    file.write(",")
    file.write("L_Dist")
    file.write(",")
    file.write("R_Dist")
    file.write("\n")
    while idx > 0:
        file.write(timeList[curr])
        file.write(",")
        file.write(str(typeList[curr]))
        file.write(",")
        file.write(str(posList[curr]))
        file.write(",")
        file.write(str(leftList[curr]))
        file.write(",")

        try:
            file.write(str(rightList[curr]))
        except IndexError:
            print("Index Error Handling: rightList[curr] issue")
            file.write('None')

        file.write("\n")

        if posList[curr] is None and leftList[curr] is None and rightList[curr] is None:
            noDetections += 1

        idx -= 1
        curr += 1

    cap1.release()
    cap2.release()

    detections = "Detection rate: " + str('{:.2f}'.format(1 - (noDetections / measurements))) + " %"
    print(detections)
    file.write(detections + "\n")

    file.close()
    cv2.destroyAllWindows()
