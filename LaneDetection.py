import cv2
import numpy as np
import math

if __name__ == '__main__':
    VIDEO_WIDTH = 300
    VIDEO_HEIGHT = 1080
    heightright = 600
    heightleft = 500

    # Width in meters
    LANE_WIDTH = 3.35
    CAR_WIDTH = 1.75
    CAM_WIDTH = 1.52

    size = 100

    leftCamFile = "H144 F C6.mp4"
    rightCamFile = "H144 F C7.mp4"

    cap1 = cv2.VideoCapture(leftCamFile)
    cap2 = cv2.VideoCapture(rightCamFile)

    #white lane lines
    line_color = [([235,235,235], [255,255,255])]

    file = open('H144F', 'w')

    #arrays that keep track of deviation and position for later averaging
    devList = []
    posList = []
    timeList = []
    outList = []

    idx = 0
    timecount = 0

    while(True):
        ret1, frame1 = cap1.read()
        ret2, frame2 = cap2.read()
        out = False
        valid = True
        if frame1 is not None and frame2 is not None:
            #The center of frame to minimize distortion
            frame1 = frame1[0:1440, 830:1130]
            frame2 = frame2[0:1440, 830:1130]
            #frame1 = cv2.addWeighted(frame1, 1.8, np.zeros(frame1.shape, frame1.dtype), 1, 15)
            #frame2 = cv2.addWeighted(frame2, 1.8, np.zeros(frame2.shape, frame2.dtype), 1, 15)

            for (lower, upper) in line_color:
                lower = np.array(lower, dtype="uint8")
                upper = np.array(upper, dtype="uint8")

                mask1 = cv2.inRange(frame1, lower, upper)
                mask2 = cv2.inRange(frame2, lower, upper)

                output1 = cv2.bitwise_and(frame1, frame1, mask = mask1)
                output2 = cv2.bitwise_and(frame2, frame2, mask = mask2)

            gray1 = cv2.cvtColor(output1,cv2.COLOR_RGB2RGBA)
            gray2 = cv2.cvtColor(output2, cv2.COLOR_RGB2RGBA)

            #cv2.imshow("gray1", gray1)
            #cv2.imshow("gray2", gray2)

            edges1 = cv2.Canny(gray1, 60,150, apertureSize = 3)
            edges2 = cv2.Canny(gray2, 60,150, apertureSize = 3)

            lines1 = cv2.HoughLines(edges1, 1 ,np.pi/180,60)
            lines2 = cv2.HoughLines(edges2, 1 ,np.pi/180,65)

            #if lines1 is not None and lines2 is not None:
            total = 0
            count = 0
            leftLines = False
            rightLines = False

            if lines1 is not None and (len(lines1) < 100):
                for x in range(0, len(lines1)):
                    for rho,theta in lines1[x]:

                        a = np.cos(theta)
                        b = np.sin(theta)
                        x0 = a * rho
                        y0 = b * rho

                        x1 = int(x0 + 1000 * (-b))
                        y1 = int(y0 + 1000 * (a))
                        x2 = int(x0 - 1000 * (-b))
                        y2 = int(y0 - 1000 * (a))
                        if (x2 - x1) is not 0 and (y1 > heightleft) and (-200 <= (y1 - y2) <= 200):
                            k = (y2 - y1) / (x2 - x1)
                            b = y1 - k * x1
                            yf = k * VIDEO_WIDTH + b
                            midy = (int)(b + yf) / 2
                            total += midy
                            count += 1
                            cv2.line(frame1, (x1, y1), (x2, y2), (0, 0, 255), 2)
                            leftLines = True

                if count != 0:
                    avg1 = (int)(total / count)
                    avgMeters1 = CAM_WIDTH / VIDEO_HEIGHT * avg1
                    cv2.line(frame1, (0, avg1), (frame1[0].size, avg1), (255, 255, 0), 2)
            else :
                valid = False
            total = 0
            count = 0

            if lines2 is not None and len(lines2 < 100):
                for x in range(0, len(lines2)):
                    for rho,theta in lines2[x]:
                        a = np.cos(theta)
                        b = np.sin(theta)
                        x0 = a * rho
                        y0 = b * rho
                        x1 = int(x0 + 1000 * (-b))
                        y1 = int(y0 + 1000 * (a))
                        x2 = int(x0 - 1000 * (-b))
                        y2 = int(y0 - 1000 * (a))
                        if (x2 - x1) is not 0 and (y1 < heightright) and (-200 <= (y1 - y2) <= 200):
                            k = (y2 - y1) / (x2 - x1)
                            b = y1 - k * x1
                            yf = k * VIDEO_WIDTH + b
                            midy = (int)(b + yf) / 2
                            total += midy
                            count += 1
                            cv2.line(frame2, (x1, y1), (x2, y2), (0, 0, 255), 2)
                            rightLines = True

                if count != 0:
                    avg2 = (int)(total / count)
                    avgMeters2 = CAM_WIDTH / VIDEO_HEIGHT * (VIDEO_HEIGHT - avg2)
                    cv2.line(frame2, (0, avg2), (frame2[0].size, avg2), (255, 255, 0), 2)

            else :
                valid = False

            if valid:

                if leftLines and rightLines:
                    dev = avgMeters1 - avgMeters2
                    devList.append(dev)

                else:
                    out = True
                    if not leftLines and rightLines and avgMeters2 > LANE_WIDTH / 4:
                        outlen = CAR_WIDTH - (LANE_WIDTH - avgMeters2)
                        devList.append((LANE_WIDTH - CAR_WIDTH) / 2 + outlen)

                    if not rightLines and leftLines and avgMeters1 > LANE_WIDTH:
                        outlen = CAR_WIDTH - (LANE_WIDTH - avgMeters1)
                        devList.append((LANE_WIDTH - CAR_WIDTH) / 2 + outlen)

                timecount += 20

                if timecount >= 200 and len(devList) != 0:
                    timestamp = round(cap1.get(cv2.CAP_PROP_POS_MSEC) / 1000, 2)
                    timeList.append((str)(timestamp))
                    if out:
                        outList.append(1)
                    else:
                        outList.append(0)
                    averageDev = np.median(devList)
                    posList.append(averageDev)
                    timecount = 0
                    devList = []
                    idx += 1



            cv2.imshow('frame1',frame1)
            cv2.imshow('frame2', frame2)
            cv2.imshow('raw1', edges1)
            cv2.imshow('raw2', edges2)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        else:
               break;

    #Calculate Mean Lateral Position
    averagePos = np.average(posList)
    total = 0
    num = 0

    for pos in posList:
        total += (pos - averagePos) * (pos - averagePos)
        num += 1
    sdlp = math.sqrt(total/num)
    file.write((str)(sdlp))
    file.write("\n")

    curr = 0
    while idx > 0:
        file.write(timeList[curr])
        file.write(" ")
        file.write((str)(posList[curr]))
        file.write(" ")
        file.write((str)(outList[curr]))
        file.write(" ")
        file.write("\n")
        idx -= 1
        curr += 1

    cap1.release()
    cap2.release()

    file.close()
    file.close()

    cv2.destroyAllWindows()
