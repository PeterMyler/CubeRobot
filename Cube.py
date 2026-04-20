import random
import serial  # to communicate with arduino
import json
import twophase.solver as sv  # to solve the cube
import magiccube  # to virtually execute moves
from magiccube.cube_base import Face
from cubescrambler import scrambler333  # to get a random scramble
from time import process_time, sleep
from Camera import get_hidden_corner_colour

ARDUINO_PORT = "COM9"
ARDUINO_BAUD_RATE = 115200

# dicts to convert between cube formats
faceToCol = {"U": "w", "D": "y", "L": "o", "R": "r", "F": "g", "B": "b"}
colToFace = {"w": "U", "y": "D", "o": "L", "r": "R", "g": "F", "b": "B"}
colours_map = "RLDFBU"

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

# for error correction
BOTTOM_HIDDEN_CORNERS = ((18, 9), (12, 6), (0, 14))
TOP_HIDDEN_CORNERS = ((7, 4), (20, 13), (1, 14))
ERROR_COLOURS = (1, 0, 3, 2, 5, 4)


def read_from_json():
    try:
        with open("cube_data.json", "r") as file:
            return json.loads(file.read())
    except Exception as e:
        print("Could not read json file.", e)
    return None

def write_to_json(data):
    try:
        with open("cube_data.json", "w") as file:
            file.write("{\n")
            items = list(data.items())
            for i, (k, v) in enumerate(items):
                line = f'  "{k}": {json.dumps(v, separators=(", ", ": "))}'
                if i < len(items) - 1:
                    file.write(line + ",\n")
                else:
                    file.write(line + "\n")
            file.write("}")
    except Exception as e:
        print("Could not write to json file.", e)


def connect_to_arduino():
    print(end="Connecting to arduino... ")

    try:
        ard = serial.Serial(port=ARDUINO_PORT, baudrate=ARDUINO_BAUD_RATE, timeout=1, write_timeout=None)
    except serial.serialutil.SerialException as e:
        # couldn't connect to arduino
        print(" Failed:", e)
        return None

    # wait for arduino to be ready
    while not ard.readline(): pass
    print("Connected")
    return ard

def twophaseToNormal(s):
    if s.startswith("Error"):
        return s
    # remove 1s, replace 3s with ', remove move count
    return " ".join(s.replace("1", "").replace("3", "\'").split()[:-1])


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

def get_random_moves(amount, double_moves=False):
    sequence = []
    for i in range(amount):
        main_move = random.choice(["U", "D", "L", "R", "F", "B"])
        modifier = random.choice(["", "\'", "2"] if double_moves else ["", "\'"])
        sequence.append(main_move + modifier)
    return " ".join(sequence)

def convert_cam_data_to_cubestate(camB_colours, camB_hidden_colours, camT_colours, camT_hidden_colours):
    cubestate = [""] * 54
    # map colour data from camera to cube string indexes
    for col, conv in zip(camB_colours, camB_conv):
        cubestate[conv] = " " if col is None else colours_map[col]
    for col, conv in zip(camB_hidden_colours, camB_hidden_conv):
        cubestate[conv] = " " if col is None else colours_map[col]
    for col, conv in zip(camT_colours, camT_conv):
        cubestate[conv] = " " if col is None else colours_map[col]
    for col, conv in zip(camT_hidden_colours, camT_hidden_conv):
        cubestate[conv] = " " if col is None else colours_map[col]
    # map centres
    for col, conv in enumerate(centres_conv):
        cubestate[conv] = colours_map[col]

    return "".join(cubestate)

def magiccubeToTwoPhase(mc):
    mc = "".join("".join(str(v)[-1:] for v in mc.get_face_flat(eval("Face." + col))) for col in "URFDLB")
    mc = coloursToFaces(mc.lower())
    return mc

class Cube:
    def __init__(self):
        self.state = None
        self.arduino = connect_to_arduino()

        if self.arduino is not None:
            sleep(0.5)
            self.arduinoWriteRead("U U U U")

    def arduinoWriteRead(self, command):
        # sends data to arduino, waits for response, and then returns it
        self.arduino.write(bytes(command.upper(), 'utf-8'))
        while not (data := self.arduino.readline()): pass
        return data.decode('utf-8').strip()

    def set_cubestate(self, camB_colours, camB_hidden_colours, camT_colours, camT_hidden_colours):
        self.state = convert_cam_data_to_cubestate(camB_colours, camB_hidden_colours, camT_colours, camT_hidden_colours)
        return self.state

    def solve_cube(self):
        # attempt to solve
        solve = sv.solve(self.state, 0, 0.2)
        if not solve.startswith("Error"):
            # solve success
            print(solve)
            return twophaseToNormal(solve)

        # attempt to fix cube by swapping each colour with its possible error
        old_cubestate = self.state
        for tp_ind in range(len(old_cubestate)):
            # skip hidden corner colours
            if tp_ind in camB_hidden_conv or tp_ind in camT_hidden_conv: continue

            curr_state = list(old_cubestate)
            old_col = colours_map.index(old_cubestate[tp_ind])
            new_col = old_col + (1 if old_col%2==0 else -1)  # ERROR_COLOURS[old_col]
            # swap colour
            curr_state[tp_ind] = colours_map[new_col]

            # attempt to solve
            # solve = sv.solve("".join(curr_state), 0, 0.1)
            # if not solve.startswith("Error"):
            #     # solve success
            #     return twophaseToNormal(solve)

            # convert twophase index to camera index
            cam_ind = hidden_corner_indexes = conv = hidden_conv = None
            if tp_ind in camB_conv:
                cam_ind = camB_conv.index(tp_ind)
                hidden_corner_indexes = BOTTOM_HIDDEN_CORNERS
                conv = camB_conv
                hidden_conv = camB_hidden_conv
            elif tp_ind in camT_conv:
                cam_ind = camT_conv.index(tp_ind)
                hidden_corner_indexes = TOP_HIDDEN_CORNERS
                conv = camT_conv
                hidden_conv = camT_hidden_conv

            # if used in a hidden corner calc - redo it
            if not cam_ind is None:
                for h_ind, corner in enumerate(hidden_corner_indexes):
                    if cam_ind in corner:
                        cols = [None, None]
                        cor_ind = corner.index(cam_ind)
                        cols[cor_ind] = new_col
                        cols[cor_ind - 1] = colours_map.index(curr_state[conv[corner[cor_ind - 1]]])

                        corner_col = get_hidden_corner_colour(cols[0], cols[1])
                        if corner_col is not None:
                            curr_state[hidden_conv[h_ind]] = colours_map[corner_col]
                            # print("Fixed hidden corner:", self.state)
                            break

            # attempt to solve
            solve = sv.solve("".join(curr_state), 0, 0.1)
            if not solve.startswith("Error"):
                # solve success
                print(solve)
                return twophaseToNormal(solve)

        # send cubestate to solver
        solve = sv.solve(self.state, 0, 0.1)
        return twophaseToNormal(solve)

    # def scramble_cube(self, use_precalculated=True):
    #     if use_precalculated:
    #         scramble = getRandomScramble()
    #         print("Used precalculated scramble")
    #     else:
    #         scramble = generateRandomScramble()
    #
    #     self.arduinoWriteRead(scramble)
    #     return scramble

    def release(self):
        self.arduino.close()

if __name__ == "__main__":
    print("wrong script mate")
