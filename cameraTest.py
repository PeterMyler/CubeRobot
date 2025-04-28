import cv2
from numpy import sum as npsum
from fractions import Fraction
from time import time, sleep

# RGB - white, red, green, yellow, orange, blue
ideal_colour_values = [(255, 255, 255), (255, 0, 0), (0, 255, 0), (255, 255, 0), (255, 128, 0), (0, 0, 255)]
# colour_values = [(121, 200, 253), (128, 0, 0), (0, 166, 0), (207, 255, 0), (230, 40, 0), (0, 12, 70)]
colour_values = [[(244, 249, 250), (115, 255, 255), (78, 160, 188), (125, 255, 255), (161, 255, 255), (204, 232, 227), (73, 140, 171), (223, 255, 255), (75, 135, 177), (167, 165, 151), (53, 112, 122), (250, 253, 254), (131, 173, 193), (162, 164, 151), (163, 226, 245), (132, 174, 182), (216, 255, 255), (222, 255, 255), (144, 197, 220), (192, 225, 217), (199, 254, 255), (182, 184, 164), (228, 255, 255), (142, 255, 255), (191, 242, 237), (218, 255, 255), (136, 242, 253), (229, 255, 255), (165, 165, 167), (149, 219, 199), (133, 230, 254), (130, 179, 167), (169, 241, 209), (252, 255, 255), (117, 254, 255), (155, 230, 254), (78, 159, 229), (94, 212, 250)],
[(165, 10, 0), (165, 1, 0), (145, 13, 33), (248, 31, 2), (144, 11, 3), (144, 0, 0), (137, 6, 2), (106, 0, 0), (132, 2, 0), (67, 1, 7), (213, 8, 4), (106, 5, 0), (140, 0, 0), (150, 2, 0), (239, 13, 13), (159, 0, 0), (140, 7, 2), (136, 9, 3), (185, 15, 23), (181, 1, 0), (150, 17, 0), (229, 30, 24), (92, 10, 0), (55, 4, 0), (199, 0, 0), (78, 14, 1), (183, 0, 0), (151, 2, 0), (245, 27, 5), (155, 2, 0), (147, 5, 0), (172, 3, 0), (138, 9, 1), (146, 11, 3), (173, 0, 0), (170, 0, 0)],
[(12, 254, 0), (0, 245, 0), (4, 156, 7), (2, 86, 1), (4, 95, 0), (0, 234, 0), (0, 159, 0), (0, 225, 0), (0, 106, 0), (0, 139, 0), (0, 249, 0), (7, 213, 0), (0, 165, 0), (0, 227, 0), (0, 185, 0), (2, 152, 0), (0, 187, 0), (0, 255, 0), (0, 242, 0), (0, 134, 0), (0, 167, 0), (0, 200, 0), (0, 145, 0), (9, 150, 15), (0, 191, 0), (0, 189, 0), (0, 92, 0), (0, 171, 0), (0, 193, 0), (0, 107, 0), (0, 129, 0), (5, 159, 4), (0, 65, 0), (0, 186, 0), (3, 177, 0)],
[(255, 255, 0), (88, 137, 0), (244, 255, 0), (254, 255, 0), (93, 183, 0), (160, 255, 0), (189, 254, 0), (124, 254, 0), (193, 255, 0), (212, 229, 0), (102, 181, 0), (205, 237, 0), (253, 255, 0), (245, 250, 2), (87, 139, 0), (174, 255, 0), (164, 255, 0), (245, 249, 0), (187, 255, 0), (85, 157, 0), (221, 255, 0), (85, 139, 0), (161, 255, 0), (98, 167, 0), (223, 255, 0), (207, 233, 0), (173, 255, 0), (215, 219, 0)],
[(255, 91, 14), (189, 50, 3), (252, 71, 0), (255, 79, 0), (255, 123, 0), (255, 127, 0), (148, 34, 0), (255, 61, 0), (238, 57, 0), (254, 61, 0), (203, 42, 0), (255, 83, 0), (255, 94, 30), (255, 74, 0), (255, 96, 0), (254, 80, 4), (244, 61, 0), (255, 89, 0), (255, 98, 0), (255, 113, 0), (208, 40, 0), (255, 143, 1), (255, 146, 0), (255, 102, 0), (255, 83, 8), (233, 70, 0), (251, 67, 0), (255, 97, 6), (255, 101, 0)],
[(0, 50, 210), (0, 109, 241), (0, 104, 254), (0, 32, 158), (0, 49, 113), (0, 84, 254), (3, 33, 80), (0, 122, 250), (0, 48, 206), (0, 30, 106), (0, 28, 118), (1, 103, 249), (0, 82, 253), (0, 43, 216), (0, 22, 120), (0, 21, 97), (0, 40, 244), (0, 26, 99), (0, 22, 80), (0, 54, 188), (0, 47, 97), (2, 36, 103), (0, 100, 255), (5, 27, 84), (0, 31, 213), (0, 21, 93), (0, 28, 150), (0, 43, 172), (0, 13, 73), (0, 24, 85), (0, 30, 165), (0, 52, 229), (0, 38, 151), (0, 36, 211), (0, 56, 183), (0, 24, 72)]]
colour_names = ["white", "red", "green", "yellow", "orange", "blue"]

# pixels to check: (x, y)
bottom_camera = [(108, 350), (171, 312), (253, 260), (115, 265), (260, 160), (190, 140), (255, 90),
                 (345, 260), (425, 306), (485, 337), (337, 162), (470, 261), (333, 90), (409, 153),
                 (148, 418), (217, 380), (301, 335), (386, 376), (456, 410), (236, 449), (375, 443)]

# Open the device at the ID 0
cap = cv2.VideoCapture(0)
# set camera resolution
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # 640x480
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
# set exposure
cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0)
cap.set(cv2.CAP_PROP_EXPOSURE, -1)

sleep(0.5)

# print camera info
_, f = cap.read()
y, x = f.shape[:2]
print(f"Resolution: {x}x{y}")
print(f"Aspect ratio: {Fraction(x/y).limit_denominator()} ({x/y})")


def getClosestRGB(given_colour, colours_to_match):
    difference = 1
    res = None

    for i, cols in enumerate(colours_to_match):
        for c in cols:
            curr_diff = 0
            for colour_index in range(3):
                curr_diff += abs(given_colour[colour_index] - c[colour_index]) / 255
            curr_diff /= 3
            if curr_diff < difference:
                difference = curr_diff
                res = i
    return res

def drawSquares(img, coords, size):
    i = 0
    for x, y in coords:
        area = img[y-size:y+size+1, x-size:x+size+1]
        average_colour = tuple(int(npsum(area[:, :, k]) // ((size*2+1)**2)) for k in range(3))
        curr_colour = getClosestRGB(average_colour, colour_values)

        # if curr_colour == 4 or curr_colour == 1:
        #     curr_colour = 1 if abs(average_colour[1] - average_colour[2]) / 255 < 0.07 else 4
        #     if average_colour[0] > 250: curr_colour = 1 if average_colour[1] < 35 else 4
        #     if 190 < average_colour[0] < 210 and 15 < average_colour[1] < 25 and average_colour[2] < 4: curr_colour = 4
        #     if average_colour[0] < 190: curr_colour = 1 if average_colour[1] < 10 else 4
        #
        # if average_colour[0] == average_colour[2] == 0 and average_colour[1] > 35: curr_colour = 2
        # if curr_colour == 0 and average_colour[0] < 90: curr_colour = 5
        # if all(c > 50 for c in average_colour): curr_colour = 0

        # print(i, average_colour)

        img = cv2.rectangle(img, (x-size, y-size), (x+size, y+size), (128, 0, 128), 1)
        img = cv2.putText(img, f"{i}", (x+10, y), cv2.FONT_HERSHEY_SIMPLEX, 1,
                          ideal_colour_values[curr_colour], 2, 2)

        i += 1
    return img

def readAvgRGB(img, coords, size):
    res = []
    for x, y in coords:
        area = img[y-size:y+size+1, x-size:x+size+1]
        average_colour = tuple(int(npsum(area[:, :, k]) // ((size*2+1)**2)) for k in range(3))
        res.append(average_colour)

    return res


def camera_func():
    # Capture frame
    ret, frame = cap.read()
    frame = cv2.rotate(frame, cv2.ROTATE_180)  # flip image upsidedown
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # convert to rgb

    # cv2.imshow('camera feed before contrast change', cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    cv2.normalize(frame, frame, 0, 1100, cv2.NORM_MINMAX)  # change image contrast
    frame = drawSquares(frame, bottom_camera, 10)  # draw squares

    # Display the resulting frame
    cv2.imshow('camera feed', cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    if cv2.waitKey(1) & 0xFF == ord('q') or cv2.getWindowProperty('camera feed', cv2.WND_PROP_VISIBLE) < 1:
        # release camera
        cap.release()
        cv2.destroyAllWindows()
        exit()


while True:
    camera_func()




