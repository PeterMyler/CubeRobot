import random
import serial
# import twophase.solver as sv  # to solve the cube
import magiccube  # to virtually execute moves
from magiccube.cube_base import Face
from cubescrambler import scrambler333  # to get a random scramble
import cv2
from numpy import sum as npsum
from numpy import median as npmedian
from fractions import Fraction
from time import time, sleep

# cube = 'wowgybwyogygybyoggrowbrgywrborwggybrbwororbwborgowryby'
# cube = "oyygwwborgrggrwwboywwrgygrrrybyywbogborrogyoyobwgbbwbo"
# cubestring = 'DUUBULDBFRBFRRULLLBRDFFFBLURDBFDFDRFRULBLUFDURRBLBDUDL'

faceToCol = {"U": "w", "D": "y", "L": "o", "R": "r", "F": "g", "B": "b"}
colToFace = {"w": "U", "y": "D", "o": "L", "r": "R", "g": "F", "b": "B"}

#################################################################
# setup camera
# RGB - white, red, green, yellow, orange, blue
ideal_colour_values_rgb = [(255, 255, 255), (255, 0, 0), (0, 255, 0), (255, 255, 0), (255, 128, 0), (0, 0, 255)]
colour_names = ["white", "red", "green", "yellow", "orange", "blue"]
# pixels to check: (x, y)
bottom_camera = [(108, 350), (171, 312), (253, 260), (121, 265), (260, 163), (190, 145), (263, 90),
                 (345, 260), (425, 306), (487, 338), (337, 162), (474, 261), (338, 90), (409, 148),
                 (148, 418), (217, 386), (301, 341), (386, 376), (456, 410), (236, 449), (375, 443)]

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
print(f"Aspect ratio: {Fraction(x / y).limit_denominator()} ({x / y})")
#################################################################

# connect to arduino
arduino = serial.Serial(port='COM4', baudrate=115200, timeout=.1)
while not arduino.readline(): pass
print("Arduino ready.")


def twophaseSolveToNormal(s):
    out = []
    if "(" in s: s = s[:s.find("(") - 1]
    for m in s.split():
        match m[1]:
            case "1":
                out.append(m[0])
            case "2":
                out.append(m)
            case "3":
                out.append(m[0] + "\'")
    return " ".join(out)


def coloursToFaces(cube):
    # converts face colours to facelets used by the twophase library
    # e.g. "ygrb" -> "DFRB"
    # (assumes white is up and green is forwards)

    global colToFace
    cube = [cube[x:x + 9] for x in range(0, 50, 9)]
    centers = [f[4] for f in cube]
    cube = "".join(cube[centers.index(c)] for c in "wrgyob")  # w, r, g, y, o, b
    cube = "".join(colToFace[c] for c in cube)
    return cube


def magiccubeToTwoPhase(mc):
    mc = "".join("".join(str(v)[-1:] for v in mc.get_face_flat(eval("Face." + col))) for col in "URFDLB")
    mc = coloursToFaces(mc.lower())
    return mc


def scrambleCube(s):
    # executes moves on a new cube, returns cubestring for twophase
    mc = magiccube.Cube(3, "".join(c * 9 for c in "WOGRBY"))
    mc.rotate(s)

    return magiccubeToTwoPhase(mc)


def generateRandomScramble():
    print("Generating scramble...")
    return scrambler333.get_WCA_scramble()


def getRandomScramble():
    f = open("../scrambles.txt", "r")
    scrambles_ = f.readlines()
    f.close()
    s_ = scrambles_[random.randint(0, len(scrambles_) - 1)]
    return s_.strip()


def arduinoWriteRead(x):
    # sends data to arduino, waits for response, and then returns it
    arduino.write(bytes(x, 'utf-8'))
    while not (data := arduino.readline()): pass
    return data.decode('utf-8').strip()


#################################################################

def drawSquares(img, coords, size):
    for i, (x, y) in enumerate(coords):
        img = cv2.rectangle(img, (x - size, y - size), (x + size, y + size), (128, 0, 128), 1)
        img = cv2.putText(img, f"{i}", (x + 10, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2, 2)
    return img


def readAvgHSV(hsv_arr, coords, cell_size):
    res = []
    for ind, (col, row) in enumerate(coords):
        # Center of each patch
        center_y = row
        center_x = col

        # Get small patch around center
        patch = hsv_arr[center_y - cell_size:center_y + cell_size,
                center_x - cell_size:center_x + cell_size]
        patch = patch.reshape(-1, 3)
        median_hsv = npmedian(patch, axis=0)
        res.append(median_hsv)

    return res


def camera_func():
    # Capture frame
    ret, frame = cap.read()
    frame = cv2.rotate(frame, cv2.ROTATE_180)  # flip image upsidedown
    # cv2.normalize(frame, frame, 0, 1100, cv2.NORM_MINMAX)  # change image contrast
    output = frame.copy()  # save BGR frame (for output)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)  # Convert to HSV

    # Optionally normalize lighting
    # h, s, v = cv2.split(hsv)
    # clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    # v = clahe.apply(v)
    # hsv = cv2.merge((h, s, v))

    hsv_values = readAvgHSV(hsv, bottom_camera, 10)  # draw squares
    output = drawSquares(output, bottom_camera, 10)  # draw squares

    # Display the drawn on frame
    cv2.imshow('camera feed', output)

    if cv2.waitKey(1) & 0xFF == ord('q') or cv2.getWindowProperty('camera feed', cv2.WND_PROP_VISIBLE) < 1:
        # release camera
        cap.release()
        cv2.destroyAllWindows()
        exit()

    return hsv_values


#################################################################

arduinoWriteRead("450 50")  # send motor delay params. safe = "450 100"

mc = magiccube.Cube(3, "".join(c * 9 for c in "WOGRBY"))  # create virtual magic cube
HSV_colours = [[], [], [], [], [], []]  # HSV - white, red, green, yellow, orange, blue
prev_scramble = ""
for iteration in range(5):
    scramble = getRandomScramble()
    prev_scramble += scramble + " "
    print(prev_scramble)

    mc.rotate(scramble)  # execute scramble in magic cube
    cubeString = magiccubeToTwoPhase(mc)  # convert magic cube to TwoPhaseSolver's virtual cube

    print(arduinoWriteRead(scramble))  # scramble the real cube
    sleep(0.5)
    print("done scrambling")

    # camera
    RBG_values = camera_func()
    camera_to_tph = [42, 43, 44, 39, 41, 37, 38, 24, 25, 26, 21, 23, 18, 19, 33, 30, 27, 28, 29, 34, 32]
    for sticker in range(21):
        actual_colour = faceToCol[cubeString[camera_to_tph[sticker]]]
        HSV_colours["wrgyob".find(actual_colour)].append(RBG_values[sticker])

    # print(*HSV_colours, sep="\n")

print("final list:")
print(*HSV_colours, sep="\n")

HSV_ranges = []
for i, HSVs in enumerate(HSV_colours):
    lowest = tuple(map(min, zip(*HSVs)))
    highest = tuple(map(max, zip(*HSVs)))
    HSV_ranges.append((lowest, highest))
print("HSV ranges:")
for i, (lowest, highest) in enumerate(HSV_ranges):
    print(f"    {'white, red, green, yellow, blue, orange'.split(', ')[i]}: {(lowest, highest)},")
cv2.waitKey(0)
