import random
import serial  # to communicate with arduino
import twophase.solver as sv  # to solve the cube
import magiccube  # to virtually execute moves
from cubescrambler import scrambler333  # to get a random scramble
from time import process_time

# dicts to convert between cube formats
faceToCol = {"U": "w", "D": "y", "L": "o", "R": "r", "F": "g", "B": "b"}
colToFace = {"w": "U", "y": "D", "o": "L", "r": "R", "g": "F", "b": "B"}

# arrays to convert camera colour values to cube state colours
camB_conv = (42, 43, 44, 39, 41, 37, 38,
             24, 25, 26, 21, 23, 18, 19,
             33, 30, 27, 28, 29, 34, 32)
camB_hidden_conv = (15, 6, 53)
camT_conv = (16, 17, 12, 14, 9, 10, 11,
             8, 5, 2, 7, 1, 3, 0,
             51, 52, 48, 50, 45, 46, 47)
camT_hidden_conv = (20, 36, 35)
centres_conv = (49, 22, 31, 13, 40, 4)

def connect_to_arduino():
    try:
        a = serial.Serial(port='COM9', baudrate=115200, timeout=1)
    except serial.serialutil.SerialException as e:
        print("Couldn't connect to Arduino.", e)
        return None

    while not a.readline(): pass
    print("Connected to Arduino")
    return a

def twophaseToNormal(s):
    print(s)
    if s.startswith("Error"): return None
    out = []
    for m in s.split()[:-1]:
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
    print("Generating random scramble...")
    return scrambler333.get_WCA_scramble()


def getRandomScramble():
    f = open("scrambles.txt", "r")
    scrambles_ = f.readlines()
    f.close()
    s_ = scrambles_[random.randint(0, len(scrambles_)-1)]
    return s_.strip()


class Cube:
    def __init__(self):
        self.state = None
        self.arduino = connect_to_arduino()
        self.arduinoWriteRead("450 50")  # set default motor speed

    def arduinoWriteRead(self, command):
        # sends data to arduino, waits for response, and then returns it
        self.arduino.write(bytes(command.upper(), 'utf-8'))
        while not (data := self.arduino.readline()): pass
        return data.decode('utf-8').strip()

    def set_cubestate(self, camB_colours, camB_hidden_colours, camT_colours, camT_hidden_colours):
        # colours_map = "ROYGBW"
        colours_map = "RLDFBU"
        cubestate = [""] * 54
        # map colour data from camera to cube string indexes
        for col, conv in zip(camB_colours, camB_conv):
            cubestate[conv] = colours_map[col]
        for col, conv in zip(camB_hidden_colours, camB_hidden_conv):
            cubestate[conv] = colours_map[col]
        for col, conv in zip(camT_colours, camT_conv):
            cubestate[conv] = colours_map[col]
        for col, conv in zip(camT_hidden_colours, camT_hidden_conv):
            cubestate[conv] = colours_map[col]
        # map centres
        for col, conv in enumerate(centres_conv):
            cubestate[conv] = colours_map[col]

        cubestate = "".join(cubestate)
        self.state = cubestate
        print(cubestate)

    def solve_cube(self):
        return twophaseToNormal(sv.solve(self.state, 0, 0.1))

    def scramble_cube(self, use_precalculated=True):
        if use_precalculated:
            scramble = getRandomScramble()
            print("Used precalculated scramble")
        else:
            scramble = generateRandomScramble()

        self.arduinoWriteRead(scramble)
        return scramble

    def release(self):
        self.arduino.close()

if __name__ == "__main__":
    print("wrong script mate")
