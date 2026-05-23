import cv2
import numpy as np
from time import sleep, time
from pygrabber.dshow_graph import FilterGraph

#                 0       1         2         3       4        5
COLOUR_NAMES = ("red", "orange", "yellow", "green", "blue", "white")
RGB_COLOUR_VALUES = ((255, 0, 0), (255, 128, 0), (255, 255, 0), (0, 255, 0), (0, 0, 255), (255, 255, 255))  # ideal values
COLOUR_HUE_RANGES = (0, 3, 23, 45, 84, 146, 181)  # (0, 3, 25, 53, 70, 160, 181)
WHITE_LIMITS = (60, 185, 120, 75, 130)  # low max s, [max s, min v, min h, max, h]
BAD_RED_LIMITS = (8, 130)  # max hue, max value
BAD_GREEN_LIMITS = (40, 175)  # min hue, max v - green for Value below threshold, yellow for above
BOX_COLOUR = (255, 0, 210)

# rubiks corner-piece colours in order of top, right, front
CORNER_COLOURS = ((5, 4, 0), (5, 0, 3), (5, 3, 1), (5, 1, 4), (2, 4, 1), (2, 1, 3), (2, 3, 0), (2, 0, 4))

# camera variables
CAMERA_RESOLUTION = (640, 480)
CAMERA_NAME = "Trust Webcam"
CAMERA_EXPOSURE = -1
DESIRED_CONTRAST = 2000

# find available camera devices
devices = FilterGraph().get_input_devices()
print("Available cameras:", *enumerate(devices))


def classify_hsv_colour(hsv_colour):
    h, s, v = hsv_colour

    # white - low Saturation and high Value
    if (s <= WHITE_LIMITS[0]) or (s <= WHITE_LIMITS[1] and v >= WHITE_LIMITS[2]
                                  and WHITE_LIMITS[3] <= h <= WHITE_LIMITS[4]):
        return 5

    # special case to determine red or orange for low hue
    if COLOUR_HUE_RANGES[1] <= h <= BAD_RED_LIMITS[0]:
        # red for Value below v, orange for above
        return 0 if v <= BAD_RED_LIMITS[1] else 1

    # special case to determine green or yellow
    if BAD_GREEN_LIMITS[0] <= h <= COLOUR_HUE_RANGES[3]:
        # green for Value below threshold, yellow for above
        return 3 if v <= BAD_GREEN_LIMITS[1] else 2

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
        self.width, self.height = CAMERA_RESOLUTION
        self.box_coords = box_coords

        if not(len(devices) > device_id and devices[device_id] == CAMERA_NAME):
            self.cap = None
            return

        try:
            # Connect to camera:
            self.cap = cv2.VideoCapture(device_id, cv2.CAP_DSHOW)

            # Apply camera settings:
            # set camera resolution
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            # set exposure
            self.cap.set(cv2.CAP_PROP_EXPOSURE, CAMERA_EXPOSURE)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 0)

            print("Connected to camera", device_id)
        except Exception as e:
            self.cap = None
            print(e)


    def set_box_coords(self, path):
        with open(path, "r") as f:
            self.box_coords = [list(map(int, l.split())) for l in f.readlines()]
            f.close()

    def get_frame(self):
        if not self.cap: return None
        ret, frame = self.cap.read()

        if not ret or frame is None:
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

    def get_median_hsv_colours(self, img):
        # get the median HSV in each given pixel coord
        colours = []
        hsv_img = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)

        # for x, y in self.box_coords:
        #     # get the area around the box coord
        #     area = hsv_img[y - size:y + size + 1, x - size:x + size + 1]
        #     # apply Gaussian blur (reduces image grain)
        #     area = cv2.GaussianBlur(area, (5, 5), 0)
        #     # convert from RGB to HSV
        #     area = cv2.cvtColor(area, cv2.COLOR_RGB2HSV)
        #     # calculate the median of Hue, Saturation, and Value in the box area
        #     median_hsv = tuple(int(np.median(area[:, :, k])) for k in range(3))
        #     colours.append(median_hsv)

        for quad in self.box_coords:
            pts = np.array(quad)
            # get the bounding box of the quad
            x, y, w, h = cv2.boundingRect(pts)
            area = hsv_img[y:y + h, x:x + w]
            # area = cv2.GaussianBlur(area, (5, 5), 0)

            # shift points to new area space coords
            pts_shifted = pts - [x, y]

            # mask quad area
            mask = np.zeros((h, w), dtype=np.uint8)
            cv2.fillPoly(mask, [pts_shifted], 255)

            # get pixels with mask applied
            pixels = area[mask == 255]

            if len(pixels) == 0:
                print("Median calculation failed")
                colours.append(None)
            else:
                # append median hsv values
                colours.append(np.median(pixels, axis=0).astype(int))

        return colours

    def draw_boxes(self, img):
        # draw squares around the given pixel coords
        for box_ind, box in enumerate(self.box_coords):
            # img = cv2.rectangle(img, (x - size, y - size), (x + size, y + size), BOX_COLOUR, 2)
            pts = np.array(box, np.int32)
            pts = pts.reshape((-1, 1, 2))
            img  = cv2.polylines(img, [pts], True, BOX_COLOUR, 2)
        return img

    def write_colour_values(self, img, colour_values, colours):
        # write given colour values next to every coord
        for i, quad in enumerate(self.box_coords):
            curr_colour = BOX_COLOUR if colours[i] is None else RGB_COLOUR_VALUES[colours[i]]

            centre_x = sum([a for a, b in quad])//4
            centre_y = sum([b for a, b in quad])//4
            img = cv2.putText(img, f"{colour_values[i]}",
                              (centre_x - len(str(colour_values[i])) // 2 * 10, centre_y - 15),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, curr_colour, 2, 2)
        return img

    def get_hidden_corner_colours(self, colours):
        result = []
        for i1, i2 in self.hidden_corner_indexes:
            result.append(get_hidden_corner_colour(colours[i1], colours[i2]))
        return result



if __name__ == "__main__":
    print("Nope")
