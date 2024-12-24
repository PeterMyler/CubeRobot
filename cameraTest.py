import cv2
from numpy import sum as npsum
from fractions import Fraction
from time import time, sleep

# RGB - white, red, green, yellow, orange, blue
ideal_colour_values = [(255, 255, 255), (255, 0, 0), (0, 255, 0), (255, 255, 0), (255, 128, 0), (0, 0, 255)]
colour_values = [(121, 200, 253), (128, 0, 0), (0, 166, 0), (207, 255, 0), (230, 40, 0), (0, 12, 70)]
colour_names = ["white", "red", "green", "yellow", "orange", "blue"]
red_weight, green_weight, blue_weight = 1, 1, 1
colour_sensitivity = 5000  # higher = won't reject colours as much

# pixels to check: (x, y)
bottom_camera = [(108, 350), (171, 312), (253, 260), (121, 265), (260, 163), (190, 145), (263, 90),
                 (345, 260), (425, 306), (487, 338), (337, 162), (474, 261), (338, 90), (409, 148),
                 (148, 418), (217, 386), (301, 341), (386, 376), (456, 410), (236, 449), (375, 443)]

xOff, yOff = 110, 30
cubeL = 420
pieceL = cubeL // 3

# text stuff
font = cv2.FONT_HERSHEY_SIMPLEX
fontScale = 1
fontColor = (255, 255, 255)
thickness = 1
lineType = 2

# Open the device at the ID 0
cap = cv2.VideoCapture(0)
# set camera resolution
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # 640x480
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
# set exposure
cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0)
cap.set(cv2.CAP_PROP_EXPOSURE, -1)

sleep(0.5)

_, frame = cap.read()
y, x = frame.shape[:2]
print(f"Resolution: {x}x{y}")
print(f"Aspect ratio: {Fraction(x/y).limit_denominator()} ({x/y})")


def getPercentageDiff(a, b):
    return abs(a - b) / 255

def getClosestRGB(given_colour, colours_to_match):
    difference = 1
    res = 1000

    for i, c in enumerate(colours_to_match):
        curr_diff = 0
        for colour_index in range(3):
            curr_diff += getPercentageDiff(given_colour[colour_index], c[colour_index])
        curr_diff /= 3
        if curr_diff < difference:
            difference = curr_diff
            res = i
    return res

def drawSquares(img, arr, size):
    i = 0
    for x, y in arr:
        area = img[y-size:y+size+1, x-size:x+size+1]
        average_colour = tuple(int(npsum(area[:, :, i]) // ((size*2+1)**2)) for i in range(3))
        curr_colour = getClosestRGB(average_colour, colour_values)

        if curr_colour == 4 or curr_colour == 1:
            curr_colour = 1 if getPercentageDiff(average_colour[1], average_colour[2]) < 0.07 else 4
            if average_colour[0] > 250: curr_colour = 1 if average_colour[1] < 35 else 4
            if 190 < average_colour[0] < 210 and 15 < average_colour[1] < 25 and average_colour[2] < 4: curr_colour = 4
            if average_colour[0] < 190: curr_colour = 1 if average_colour[1] < 10 else 4

        if average_colour[0] == average_colour[2] == 0 and average_colour[1] > 35: curr_colour = 2
        if curr_colour == 0 and average_colour[0] < 90: curr_colour = 5
        if all(c > 50 for c in average_colour): curr_colour = 0

        print(i, average_colour)

        img = cv2.rectangle(img, (x-size, y-size), (x+size, y+size), (128, 0, 128), 1)
        img = cv2.putText(img, f"{i}", (x+10, y), cv2.FONT_HERSHEY_SIMPLEX, 1,
                          ideal_colour_values[curr_colour], 2, 2)

        i += 1
    return img

while True:
    t = time()
    # Capture frame-by-frame
    ret, frame = cap.read()
    frame = cv2.rotate(frame, cv2.ROTATE_180)  # flip image upsidedown (do if camera is upsidedown)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # convert to rgb

    cv2.imshow('camera feed before contrast change', cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    cv2.normalize(frame, frame, 0, 1100, cv2.NORM_MINMAX)  # change image contrast
    frame = drawSquares(frame, bottom_camera, 10)

    # Display the resulting frame
    cv2.imshow('camera feed', cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))


    # Wait for a user input to quit the application
    if cv2.waitKey(1) & 0xFF == ord('q') or cv2.getWindowProperty('camera feed', cv2.WND_PROP_VISIBLE) < 1:
        break




# release camera
cap.release()
cv2.destroyAllWindows()




