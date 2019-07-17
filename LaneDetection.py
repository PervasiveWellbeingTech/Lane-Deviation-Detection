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
    LANE_WIDTH = 3.35
    CAR_WIDTH = 1.75
    CAM_WIDTH = 1.52 # Not sure if this needs to be updated based on the new camera crops...

    # ?
    size = 100

    # white lane lines (related to color filter code below)
    # line_color = [([126, 129, 136], [126, 129, 136])]

    # arrays and variables that keep track of deviation and position for later averaging
    leftList = []
    rightList = []
    devList = []
    posList = []
    timeList = []
    outList = []
    idx = 0
    timeCount = 0

    '''Start of scrubbing through video code below'''
    skip_ahead = 75
    cur_pos = 0

    # Open output files
    file = open('Output.txt', 'w')
    file_loc = open('Output_Locations.txt', 'w')

    # Load data files
    leftCamFile = "C4-FirstDrive.MP4"
    rightCamFile = "C6-FirstDrive.MP4"
    cap1 = cv2.VideoCapture(leftCamFile)
    cap2 = cv2.VideoCapture(rightCamFile)

    while True:
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
                    #print("Average Meters (Left): " + str(avgMeters1))
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
                    #print("Average Meters (Right): " + str(avgMeters2))

            else:
                valid = False

            timestamp = round(cqap1.get(cv2.CAP_PROP_POS_MSEC) / 1000, 2)
            print(str(timestamp))
            if valid:
                #print("Valid")
                if leftLines and rightLines:
                    dev = avgMeters1 - avgMeters2
                    devList.append(dev)

                '''
                else:
                    out = True
                    if not leftLines and rightLines and avgMeters2 > LANE_WIDTH / 4:
                        outLen = CAR_WIDTH - (LANE_WIDTH - avgMeters2)
                        devList.append((LANE_WIDTH - CAR_WIDTH) / 2 + outLen)

                    if not rightLines and leftLines and avgMeters1 > LANE_WIDTH:
                        outLen = CAR_WIDTH - (LANE_WIDTH - avgMeters1)
                        devList.append((LANE_WIDTH - CAR_WIDTH) / 2 + outLen)
                '''

                timeCount += 20

                if timeCount >= 200 and len(devList) != 0:
                    timestamp = round(cap1.get(cv2.CAP_PROP_POS_MSEC) / 1000, 2)
                    timeList.append(str(timestamp))

                    #if out:
                    #    outList.append(1)
                    #else:
                    #    outList.append(0)

                    averageDev = np.median(devList)
                    posList.append(averageDev)
                    leftList.append(avgMeters1)
                    rightList.append(avgMeters2)
                    timeCount = 0
                    devList = []
                    idx += 1

            else:
                timestamp = round(cap1.get(cv2.CAP_PROP_POS_MSEC) / 1000, 2)
                #print("Not Valid: " + str(timestamp))
                timeCount += 20

                if timeCount >= 200:
                    timestamp = round(cap1.get(cv2.CAP_PROP_POS_MSEC) / 1000, 2)
                    timeList.append(str(timestamp))

                    #if out:
                    #    outList.append(1)
                    #else:
                    #    outList.append(0)

                    posList.append("?")
                    leftList.append(avgMeters1)
                    rightList.append(avgMeters2)

                    timeCount = 0
                    devList = []
                    idx += 1

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

    #averagePos = np.average(posList)
    total = 0
    num = 0

    #for pos in posList:
    #    total += (pos - averagePos) * (pos - averagePos)
    #    num += 1

    #sdlp = math.sqrt(total / num)
    #file.write(str(sdlp))
    #file.write("\n")

    print("Writing results...")
    curr = 0
    measurements = idx
    noDetections = 0
    percentPossibleDetection = 0
    while idx > 0:
        file.write(timeList[curr])
        file.write(" ")
        file.write(str(posList[curr]))
        file.write(" ")
        #file.write(str(outList[curr]))
        #file.write(" ")
        file.write(str(leftList[curr]))
        file.write(" ")
        file.write(str(rightList[curr]))
        file.write(" ")
        file.write("\n")

        if posList[curr] == "?" and leftList[curr] == "?" and rightList[curr] == "?":
            noDetections = noDetections + 1

        idx -= 1
        curr += 1

    cap1.release()
    cap2.release()

    file.close()
    file.close()

    cv2.destroyAllWindows()

    if (1 - (noDetections/measurements)) == 1:
        print("Detection rate: " + str(1 - (noDetections / measurements)) + "0%")
    else:
        print("Detection rate: " + str(1 - (noDetections/measurements)) + "%")
