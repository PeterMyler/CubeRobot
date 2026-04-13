import cv2
from PIL import Image, ImageTk
import numpy as np
from time import sleep, time

CAMERA_RESOLUTION = (640, 480)
CAMERA_EXPOSURE = -1
DESIRED_CONTRAST = 1000

#                 0       1         2         3       4        5
COLOUR_NAMES = ["red", "orange", "yellow", "green", "blue", "white"]
RGB_COLOUR_VALUES = ((255, 0, 0), (255, 128, 0), (255, 255, 0), (0, 255, 0), (0, 0, 255), (255, 255, 255))
BOX_SIZE = 10  # pixel radius of colour detection
COLOUR_HUE_RANGES = (0, 3, 25, 53, 70, 160, 181)
BOX_COLOUR = (255, 0, 210)
# rubiks corner-piece colours in order of top, right, front
CORNER_COLOURS = ((5, 4, 0), (5, 0, 3), (5, 3, 1), (5, 1, 4), (2, 4, 1), (2, 1, 3), (2, 3, 0), (2, 0, 4))

def classify_hsv_colour(hsv_colour):
    h, s, v = hsv_colour

    # white - low Saturation and high Value
    if s < 190 and v > 50:
        return 5

    # special case to determine red or orange for low hue
    if 1 <= h <= 3:
        # red for Value below 140, orange for above
        return 0 if v < 70 else 1

    # determine colour (match to colour hue ranges)
    for i in range(len(COLOUR_HUE_RANGES) - 1):
        if COLOUR_HUE_RANGES[i] <= h < COLOUR_HUE_RANGES[i + 1]:
            return i % 5  # wrap back around to red

    return None

def classify_hsv_colours(hsv_colours):
    return [classify_hsv_colour(col) for col in hsv_colours]

def get_hidden_corner_colour(colour1, colour2):
    # find matching piece with matching colours in same order
    correct_order = (colour1, colour2)
    for corner in CORNER_COLOURS:
        for i in range(3):
            # if the current corner and the next one (wrapped around)
            # equal the correct order -> return the corner after that
            if (corner[i], corner[(i + 1) % 3]) == correct_order:
                return corner[(i + 2) % 3]
    return None


class Camera:
    def __init__(self, device_id, flip_upsidedown=False, name=None, box_coords=None):
        self.device_id = device_id
        self.flip_upsidedown = flip_upsidedown
        self.name = name
        self.label = None  # label from GUI script
        self.hidden_corner_indexes = None
        self.hidden_corner_text_coords = None

        # get box coords
        if box_coords is not None:
            with open(box_coords, "r") as f:
                self.box_coords = [list(map(int, l.split())) for l in f.readlines()]
                f.close()
        else:
            self.box_coords = None

        # Connect to camera:
        self.cap = cv2.VideoCapture(device_id, cv2.CAP_DSHOW)

        # Apply camera settings:
        # set camera resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_RESOLUTION[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_RESOLUTION[1])
        # set exposure
        self.cap.set(cv2.CAP_PROP_EXPOSURE, CAMERA_EXPOSURE)
        # self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        print("Connected to camera", device_id)

    def set_box_coords(self, path):
        with open(path, "r") as f:
            self.box_coords = [list(map(int, l.split())) for l in f.readlines()]
            f.close()

    def get_frame(self):
        ret, frame = self.cap.read()

        if not ret or frame is None:
            print("Camera is unavailable")
            return None

        # flip image 180 degrees
        if self.flip_upsidedown:
            cv2.rotate(frame, cv2.ROTATE_180, frame)

        # convert to RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # increase image contrast
        cv2.normalize(frame, frame, 0, DESIRED_CONTRAST, cv2.NORM_MINMAX)

        return frame

    def release(self):
        self.cap.release()

    def get_median_hsv_colours(self, img, size=BOX_SIZE):
        # get the median HSV in each given pixel coord
        colours = []
        for x, y in self.box_coords:
            # get the area around the box coord
            area = img[y - size:y + size + 1, x - size:x + size + 1]
            # apply Gaussian blur (reduces image grain)
            area = cv2.GaussianBlur(area, (5, 5), 0)
            # convert from RGB to HSV
            area = cv2.cvtColor(area, cv2.COLOR_RGB2HSV)
            # calculate the median of Hue, Saturation, and Value in the box area
            median_hsv = tuple(int(np.median(area[:, :, k])) for k in range(3))
            colours.append(median_hsv)
        return colours

    def draw_boxes(self, img, size=BOX_SIZE):
        # draw squares around the given pixel coords
        for i, (x, y) in enumerate(self.box_coords):
            img = cv2.rectangle(img, (x - size, y - size), (x + size, y + size), BOX_COLOUR, 2)
        return img

    def write_colour_values(self, img, colour_values, colours):
        # write given colour values next to every coord
        for i, (x, y) in enumerate(self.box_coords):
            curr_colour = BOX_COLOUR if colours[i] is None else RGB_COLOUR_VALUES[colours[i]]
            img = cv2.putText(img, f"{colour_values[i]}", (x - len(str(colour_values[i])) // 2 * 10, y - 15),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, curr_colour, 2, 2)
        return img

    def get_hidden_corner_colours(self, colours):
        result = []
        for i1, i2 in self.hidden_corner_indexes:
            result.append(get_hidden_corner_colour(colours[i1], colours[i2]))
        return result












if __name__ == "__main__":
    cam = Camera(0, True)
    cam.set_box_coords("camB_boxes.txt")

    while True:
        sleep(0.5)
        frame = cam.get_frame()
        if not frame is None:
            # get median hsv for each piece
            median_hsv_colours = cam.get_median_hsv_colours(frame)
            # classify hsv colours
            piece_colours = classify_hsv_colours(median_hsv_colours)

            # figure out hidden corner colours
            corner1 = get_last_corner_colour(piece_colours[18], piece_colours[9])
            corner2 = get_last_corner_colour(piece_colours[12], piece_colours[6])
            corner3 = get_last_corner_colour(piece_colours[0], piece_colours[14])
            # write them on the frame
            corners = [corner1, corner2, corner3]
            for i, (x, y) in enumerate(((530, 400), (300, 20), (20, 420))):
                if corners[i] is None: continue
                frame = cv2.putText(frame, f"{COLOUR_NAMES[corners[i]]}", (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.75, BOX_COLOUR, 2, 2)

            # draw boxes
            frame = cam.draw_boxes(frame)

            # draw text
            frame = cam.write_colour_values(frame, median_hsv_colours, piece_colours)

            cv2.imshow('camera feed', cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

        if cv2.waitKey(1) & 0xFF == ord('q') or cv2.getWindowProperty('camera feed', cv2.WND_PROP_VISIBLE) < 1:
            cam.release()
            cv2.destroyAllWindows()
            exit()
