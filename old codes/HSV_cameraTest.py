import cv2
import numpy as np
from time import sleep

# Define HSV color ranges
# color_ranges = {
#     'red1':    ((0, 100, 100), (10, 255, 255)),
#     'red2':    ((170, 100, 100), (180, 255, 255)),  # second red range
#     'orange': ((8, 100, 100), (20, 255, 255)),
#     'yellow': ((20, 250, 130), (50, 255, 255)),
#     'green':  ((40, 100, 100), (80, 255, 180)),
#     'blue':   ((100, 180, 100), (140, 255, 255)),
#     'white':  ((80, 140, 180), (180, 240, 255))  # low saturation, high value
# }
color_ranges = {
    "white": ((21.0, 8.0, 25.0), (107.5, 208.5, 79.0)),
    "red": ((108.0, 209.0, 10.0), (117.0, 255.0, 54.0)),
    "green": ((0.0, 204.0, 9.0), (173.0, 255.0, 41.0)),
    "yellow": ((22.0, 221.0, 18.0), (51.0, 255.0, 96.0)),
    "blue": ((46.0, 238.5, 9.0), (62.0, 255.0, 33.0)),
    "orange": ((5.0, 230.0, 30.0), (11.0, 255.0, 105.0))
}
# pixels to check: (x, y)
bottom_camera = [(108, 350), (171, 312), (253, 260), (121, 265), (260, 163), (190, 145), (263, 90),
                 (345, 260), (425, 306), (487, 338), (337, 162), (474, 261), (338, 90), (409, 148),
                 (148, 418), (217, 386), (301, 341), (386, 376), (456, 410), (236, 449), (375, 443)]

# Load image
# image = cv2.imread('pics\\raw_frame3.png')
# image = cv2.imread('pics\\contrasted_frame1.png')
# if image is None:
#     raise ValueError("Image not found!")

#################################################################

# Open the device at the ID 0
cap = cv2.VideoCapture(0)
# set camera resolution
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # 640x480
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
# set exposure
cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0)
cap.set(cv2.CAP_PROP_EXPOSURE, -1)
sleep(0.5)

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
        median_hsv = np.median(patch, axis=0)
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


def get_color(hsv_pixel):
    for color, (lower, upper) in color_ranges.items():
        l = np.array(lower)
        u = np.array(upper)
        if np.all(hsv_pixel >= l) and np.all(hsv_pixel <= u):
            return color.replace('1', '').replace('2', '')
    return 'unknown'


#################################################################


HSV_values = camera_func()

for i, pixel in enumerate(HSV_values):
    print(f"{i} - {get_color(pixel)} - {pixel}")


cv2.waitKey(0)
cv2.destroyAllWindows()