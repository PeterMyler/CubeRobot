import random
import serial
# import twophase.solver as sv  # to solve the cube
import magiccube  # to virtually execute moves
from magiccube.cube_base import Face
from cubescrambler import scrambler333  # to get a random scramble
import cv2
from numpy import sum as npsum
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
ideal_colour_values = [(255, 255, 255), (255, 0, 0), (0, 255, 0), (255, 255, 0), (255, 128, 0), (0, 0, 255)]
colour_values = [(121, 200, 253), (128, 0, 0), (0, 166, 0), (207, 255, 0), (230, 40, 0), (0, 12, 70)]
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
print(f"Aspect ratio: {Fraction(x/y).limit_denominator()} ({x/y})")
#################################################################

# connect to arduino
arduino = serial.Serial(port='COM9', baudrate=115200, timeout=.1)
while not arduino.readline(): pass
print("Arduino ready.")


def twophaseSolveToNormal(s):
    out = []
    if "(" in s: s = s[:s.find("(") - 1]
    for m in s.split():
        match m[1]:
            case "1": out.append(m[0])
            case "2": out.append(m)
            case "3": out.append(m[0]+"\'")
    return " ".join(out)


def coloursToFaces(cube):
    # converts face colours to facelets used by the twophase library
    # e.g. "ygrb" -> "UBLR"
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
    mc = magiccube.Cube(3, "".join(c*9 for c in "WOGRBY"))
    mc.rotate(s)

    return magiccubeToTwoPhase(mc)


def generateRandomScramble():
    print("Generating scramble...")
    return scrambler333.get_WCA_scramble()

def getRandomScramble():
    f = open("../scrambles.txt", "r")
    scrambles_ = f.readlines()
    f.close()
    s_ = scrambles_[random.randint(0, len(scrambles_)-1)]
    return s_.strip()


def arduinoWriteRead(x):
    # sends data to arduino, waits for response, and then returns it
    arduino.write(bytes(x, 'utf-8'))
    while not (data := arduino.readline()): pass
    return data.decode('utf-8').strip()

#################################################################

def drawSquares(img, coords, size):
    i = 0
    for x, y in coords:
        img = cv2.rectangle(img, (x-size, y-size), (x+size, y+size), (128, 0, 128), 1)
        img = cv2.putText(img, f"{i}", (x+10, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2, 2)
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
    RBG_values_ = readAvgRGB(frame, bottom_camera, 10)  # draw squares
    frame = drawSquares(frame, bottom_camera, 10)  # draw squares

    # Display the resulting frame
    cv2.imshow('camera feed', cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    if cv2.waitKey(1) & 0xFF == ord('q') or cv2.getWindowProperty('camera feed', cv2.WND_PROP_VISIBLE) < 1:
        # release camera
        cap.release()
        cv2.destroyAllWindows()
        exit()

    return RBG_values_


arduinoWriteRead("450 100")  # send motor delay params

mc = magiccube.Cube(3, "".join(c*9 for c in "WOGRBY"))  # create virtual magic cube
colours = [[], [], [], [], [], []]  # RGB - white, red, green, yellow, orange, blue
for i in range(10):
    scramble = getRandomScramble()
    print(scramble)

    mc.rotate(scramble)  # execute scramble in magic cube
    cubeString = magiccubeToTwoPhase(mc)  # convert magic cube to TwoPhaseSolver's virtual cube

    print(arduinoWriteRead(scramble))  # scramble the real cube
    sleep(0.5)
    print("done scrambling")

    # camera
    RBG_values = camera_func()
    camera_to_tph = [42, 43, 44, 39, 41, 37, 38, 24, 25, 26, 21, 23, 18, 19, 33, 30, 27, 28, 29, 34, 32]
    for col in range(21):
        actual_colour = faceToCol[cubeString[camera_to_tph[col]]]
        colours["wrgyob".find(actual_colour)].append(RBG_values[col])

    print(*colours, sep="\n")

print("final list:")
for c in colours:
    print(list(set(c)))

