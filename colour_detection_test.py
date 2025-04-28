import random
import serial
import twophase.solver as sv  # to solve the cube
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
# real RGB colour values
colour_values = [[(76, 177, 254), (81, 162, 252), (108, 247, 255), (78, 161, 214), (208, 253, 246), (59, 169, 249), (180, 243, 239), (219, 254, 248), (119, 222, 253), (129, 129, 83), (134, 200, 194), (210, 254, 254), (100, 252, 255), (84, 208, 255), (75, 239, 255), (65, 157, 234), (123, 214, 254), (90, 174, 250), (81, 180, 253), (146, 226, 219), (84, 188, 252), (36, 152, 235), (58, 113, 161), (70, 103, 133), (159, 145, 147), (110, 250, 255), (157, 183, 205), (198, 254, 253), (68, 130, 167), (91, 187, 254), (70, 110, 117), (115, 225, 255), (81, 213, 255), (61, 159, 228), (149, 193, 168), (66, 155, 198), (16, 135, 200)],
[(209, 33, 22), (97, 0, 0), (159, 8, 0), (85, 2, 0), (113, 13, 14), (136, 14, 0), (93, 0, 0), (123, 17, 0), (128, 6, 1), (153, 0, 0), (105, 16, 31), (162, 0, 0), (113, 0, 0), (47, 5, 1), (151, 7, 0), (41, 6, 6), (52, 3, 2), (112, 22, 9), (111, 0, 0), (143, 16, 0), (109, 10, 28), (105, 0, 0), (54, 4, 2), (108, 0, 0), (111, 16, 8), (64, 9, 5), (51, 3, 1), (124, 12, 6), (135, 13, 0), (173, 4, 0), (254, 13, 0), (255, 46, 28), (219, 16, 0), (228, 0, 0)],
[(0, 76, 0), (36, 255, 0), (0, 87, 0), (9, 92, 0), (0, 111, 0), (0, 144, 0), (0, 58, 0), (0, 91, 0), (0, 80, 0), (0, 126, 0), (0, 170, 0), (0, 62, 0), (4, 85, 1), (0, 128, 0), (0, 117, 0), (0, 108, 0), (0, 141, 0), (11, 70, 2), (0, 77, 0), (8, 89, 0), (18, 122, 14), (12, 95, 0), (0, 66, 0), (0, 143, 0), (0, 112, 0), (0, 145, 0), (3, 131, 31), (0, 94, 0), (8, 88, 0), (0, 114, 0), (16, 110, 11), (0, 63, 0), (0, 107, 0), (0, 129, 0), (1, 138, 0), (0, 184, 0)],
[(117, 255, 0), (165, 195, 0), (170, 180, 0), (95, 171, 0), (147, 246, 0), (77, 249, 0), (118, 139, 0), (129, 255, 0), (129, 224, 0), (186, 205, 0), (88, 187, 0), (149, 254, 0), (82, 255, 0), (241, 255, 0), (90, 147, 1), (111, 252, 0), (172, 178, 0), (236, 254, 0), (128, 255, 0), (97, 171, 0), (185, 254, 0), (101, 164, 0), (222, 255, 2), (85, 190, 0), (102, 253, 0), (132, 148, 1), (139, 152, 0), (196, 238, 0), (195, 231, 0), (76, 143, 0), (133, 255, 0), (111, 255, 0), (135, 249, 0), (61, 154, 0), (84, 250, 0), (245, 255, 0), (152, 164, 0), (42, 210, 0), (54, 255, 0)],
[(254, 63, 1), (196, 48, 0), (208, 52, 0), (245, 61, 0), (121, 41, 0), (254, 70, 0), (255, 79, 0), (154, 44, 0), (255, 106, 20), (135, 48, 3), (255, 63, 0), (255, 72, 0), (255, 61, 0), (228, 46, 0), (215, 53, 0), (234, 49, 0), (255, 74, 0), (145, 42, 1), (255, 87, 0), (219, 45, 0), (228, 63, 0), (248, 78, 30), (252, 61, 0), (159, 46, 0), (160, 34, 0), (255, 108, 7), (255, 88, 10), (255, 78, 0), (228, 70, 5), (248, 53, 0), (255, 73, 0), (149, 58, 23), (147, 56, 2), (147, 46, 7), (254, 64, 0), (210, 38, 0), (255, 71, 0), (248, 66, 0), (255, 95, 9), (161, 6, 0), (183, 21, 0), (234, 18, 0), (153, 17, 0)],
[(0, 21, 174), (26, 137, 254), (0, 13, 84), (0, 16, 86), (0, 25, 180), (9, 40, 87), (0, 51, 162), (0, 20, 98), (0, 20, 104), (0, 20, 107), (3, 39, 71), (0, 23, 170), (0, 17, 44), (0, 17, 108), (2, 41, 78), (5, 22, 79), (9, 41, 148), (4, 16, 29), (0, 20, 167), (0, 22, 134), (1, 15, 67), (0, 21, 123), (0, 19, 107), (0, 18, 81), (17, 79, 172), (0, 21, 202), (0, 25, 126), (7, 39, 142), (0, 37, 109), (4, 37, 81), (0, 15, 57), (0, 24, 118), (0, 30, 140)]]
colour_names = ["white", "red", "green", "yellow", "orange", "blue"]
# pixels to check: (x, y)
bottom_camera = [(108, 350), (171, 312), (253, 260), (121, 265), (260, 163), (190, 145), (255, 90),
                 (345, 260), (425, 306), (485, 330), (337, 162), (474, 261), (338, 90), (409, 148),
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
    f = open("scrambles.txt", "r")
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
ongoing = ""
for i in range(20):
    scramble = getRandomScramble()
    ongoing += scramble + " "
    print(ongoing)

    mc.rotate(scramble)  # execute scramble in magic cube
    cubeString = magiccubeToTwoPhase(mc)  # convert magic cube to TwoPhaseSolver's virtual cube

    print(arduinoWriteRead(scramble))  # scramble the real cube
    sleep(0.5)
    print("done scrambling")

    # camera
    RBG_values = camera_func()
    camera_to_tph = [42, 43, 44, 39, 41, 37, 38, 24, 25, 26, 21, 23, 18, 19, 33, 30, 27, 28, 29, 34, 32]
    for col in range(21):
        actual_colour = "wrgyob".find(faceToCol[cubeString[camera_to_tph[col]]])
        if actual_colour != getClosestRGB(RBG_values[col], colour_values):
            print("Not matched - ", col, RBG_values[col])
            print(actual_colour, "!=", getClosestRGB(RBG_values[col], colour_values))
            print("Updated table...")
            colour_values[actual_colour].append(RBG_values[col])



# solve and execute
solve = twophaseSolveToNormal(sv.solve(cubeString, 0, 0.1))  # solve the virtual cube (max time = 0.1 sec)
print(solve)
print(arduinoWriteRead(solve))  # send moves to arduino

print(*colour_values, sep="\n")

