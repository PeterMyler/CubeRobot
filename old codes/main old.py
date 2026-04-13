import random
import serial  # to communicate with arduino
import time
from time import process_time
import twophase.solver as sv  # to solve the cube
import magiccube  # to virtually execute moves
from magiccube.cube_base import Face
from cubescrambler import scrambler333  # to get a random scramble
from keyboard import is_pressed, wait
# cube = 'wowgybwyogygybyoggrowbrgywrborwggybrbwororbwborgowryby'
# cube = "oyygwwborgrggrwwboywwrgygrrrybyywbogborrogyoyobwgbbwbo"
# cubestring = 'DUUBULDBFRBFRRULLLBRDFFFBLURDBFDFDRFRULBLUFDURRBLBDUDL'

faceToCol = {"U": "w", "D": "y", "L": "o", "R": "r", "F": "g", "B": "b"}
colToFace = {"w": "U", "y": "D", "o": "L", "r": "R", "g": "F", "b": "B"}

# connect to arduino
arduino = serial.Serial(port='COM5', baudrate=115200, timeout=.1)
while not arduino.readline(): pass
print("Arduino ready.")


def twophaseToNormal(s):
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


def scrambleCube(s):
    # executes moves on a new cube, returns cubestring for twophase
    mc = magiccube.Cube(3, "".join(c*9 for c in "WOGRBY"))
    mc.rotate(s)
    print(mc)
    mc = "".join("".join(str(v)[-1:] for v in mc.get_face_flat(eval("Face."+col))) for col in "URFDLB")
    mc = coloursToFaces(mc.lower())
    print(mc)
    return mc


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


scramble = r"D2 B' U' D' R D' R B2 D' B U' D2 L D' L F2 L2 B D L F2 L F R2 U2 U' F B' R2 D2 L2 R2 U' L2 U' R B2 D' B2 L U2 D2 B2 D' L F' D2 B' D2 R R' L D L D' B' U2 F' R F D' L2 D' R2 D' B' U' B2 R' D B2 D L2 D' R R2 L2 B2 D2 L2 D2 L U2 B L2 F2 R2 U2 R2 D' R' L2 B F' L F U D' F2 R F' L B' R L F2 U B' D2 L2 U F2 R D L U' L2 F L2 U' D2 B' F D2 L'"
# scramble = getRandomScramble()
print(scramble)
vCube = scrambleCube(scramble)  # scramble the virtual cube (used for solving alg)
arduinoWriteRead("450 50")  # send motor delay params; min = (340 0)
# arduinoWriteRead(scramble)  # scramble the real cube
print("done scrambling")

input("Waiting for input to start solve: ")  # wait for user
# solve and execute
solve = twophaseToNormal(sv.solve(vCube, 0, 0.1))  # solve the virtual cube (max time = 0.1 sec)
print(solve)
print(arduinoWriteRead(solve))  # send moves to arduino

