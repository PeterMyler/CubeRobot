import cv2
import numpy as np

# Define HSV color ranges
# These ranges need to be calibrated for your own cube and lighting!
color_ranges = {
    'red1':    ((0, 100, 100), (10, 255, 255)),
    'red2':    ((170, 100, 100), (180, 255, 255)),  # second red range
    'orange': ((8, 100, 100), (20, 255, 255)),
    'yellow': ((20, 250, 130), (50, 255, 255)),
    'green':  ((40, 100, 100), (80, 255, 180)),
    'blue':   ((100, 180, 100), (140, 255, 255)),
    'white':  ((80, 140, 180), (180, 240, 255))  # low saturation, high value
}
# pixels to check: (x, y)
bottom_camera = [(108, 350), (171, 312), (253, 260), (121, 265), (260, 163), (190, 145), (263, 90),
                 (345, 260), (425, 306), (487, 338), (337, 162), (474, 261), (338, 90), (409, 148),
                 (148, 418), (217, 386), (301, 341), (386, 376), (456, 410), (236, 449), (375, 443)]

def get_color(hsv_pixel):
    for color, (lower, upper) in color_ranges.items():
        l = np.array(lower)
        u = np.array(upper)
        if np.all(hsv_pixel >= l) and np.all(hsv_pixel <= u):
            return color.replace('1', '').replace('2', '')
    return 'unknown'

# Load image
# image = cv2.imread('pics\\raw_frame3.png')
image = cv2.imread('pics\\contrasted_frame1.png')
if image is None:
    raise ValueError("Image not found!")

# Convert to HSV
hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

# Optionally normalize lighting
# h, s, v = cv2.split(hsv)
# clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
# v = clahe.apply(v)
# hsv = cv2.merge((h, s, v))

# Grid size
cell_height = 20
cell_width = 20

# Output image for visualization
output = image.copy()

for ind, (row, col) in enumerate(bottom_camera):
    # Center of each patch
    center_x = col
    center_y = row

    # Get small patch around center
    patch = hsv[center_x-cell_width//2:center_x+cell_width//2, center_y-cell_height//2:center_y+cell_height//2]
    patch = patch.reshape(-1, 3)
    median_hsv = np.median(patch, axis=0)

    color = get_color(median_hsv)

    # Draw detected color name
    cv2.putText(output, f"{ind}. {color}", (center_y-30, center_x+15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255), 1)
    # Optionally draw rectangle around patch
    cv2.rectangle(output, (center_y-cell_height//2, center_x-cell_width//2), (center_y+cell_height//2,  center_x+cell_width//2), (173, 216, 230), 1)

    print(f"{ind}) Pos: {(col, row)}; HSV: {median_hsv}; Colour: {color}")

# Show results
cv2.imwrite("current_image.png", output)
cv2.imshow('Detected Colors', output)
cv2.waitKey(0)
cv2.destroyAllWindows()