import cv2
from fractions import Fraction
from time import time, sleep

# RGB - white, red, green, yellow, orange, blue
colour_values = [(255, 255, 255), (255, 0, 0), (0, 255, 0), (255, 255, 0), (255, 128, 0), (0, 0, 255)]
colour_values = [(167, 132, 125), (177, 8, 4), (0, 45, 7), (183, 150, 43), (241, 49, 5), (4, 20, 69)]
colour_names = ["white", "red", "green", "yellow", "orange", "blue"]
red_weight, green_weight, blue_weight = 1, 1, 1
colour_sensitivity = 5000  # higher = won't reject colours as much

xOff, yOff = 110, 30
cubeL = 420
pieceL = cubeL // 3

# text stuff
font = cv2.FONT_HERSHEY_SIMPLEX
fontScale = 1
fontColor = (255, 255, 255)
thickness = 1
lineType = 2

# Open the device at the ID 0
cap = cv2.VideoCapture(0)
# set res
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # 640x480
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
# set exposure
cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0)
cap.set(cv2.CAP_PROP_EXPOSURE, -1)

sleep(0.5)

_, frame = cap.read()
y, x = frame.shape[:2]
print(f"Resolution: {x}x{y}")
print(f"Aspect ratio: {Fraction(x/y).limit_denominator()} ({x/y})")


def getClosestRGB(col):
    closest_value = 255**3
    colour_index = -1
    r1, g1, b1 = col
    for i, rgb in enumerate(colour_values):
        d = ((rgb[0] - r1) * red_weight)**2 + ((rgb[1] - g1) * blue_weight)**2 + ((rgb[2] - b1) * green_weight)**2
        if d < closest_value:
            closest_value = d
            colour_index = i

    return colour_index if closest_value < colour_sensitivity else -1


while True:
    t = time()
    # Capture frame-by-frame
    ret, frame = cap.read()
    frame = cv2.rotate(frame, cv2.ROTATE_180)  # flip image upsidedown (do if camera is upsidedown)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # convert to rgb
    cv2.normalize(frame, frame, 0, 1500, cv2.NORM_MINMAX)  # change image contrast

    # draw outline
    cv2.line(frame, (xOff, yOff), (xOff + cubeL, yOff), (0, 0, 255), 2)
    cv2.line(frame, (xOff + cubeL, yOff), (xOff + cubeL, yOff + cubeL), (0, 0, 255), 2)
    cv2.line(frame, (xOff + cubeL, yOff + cubeL), (xOff, yOff + cubeL), (0, 0, 255), 2)
    cv2.line(frame, (xOff, yOff + cubeL), (xOff, yOff), (0, 0, 255), 2)

    # get and draw center of each piece
    for y in range(yOff + pieceL//2, yOff + cubeL - 10, pieceL):
        for x in range(xOff + pieceL//2, xOff + cubeL - 10, pieceL):
            ind = getClosestRGB(frame[y][x])
            if ind == -1: continue
            colour_name = colour_names[ind]

            # write text on image
            tw, th = cv2.getTextSize(colour_name, font, fontScale, lineType)[0]
            cv2.putText(frame, colour_name, (x - tw // 2, y), font, fontScale, fontColor, thickness, lineType)


    # Display/save the resulting frame
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    cv2.imshow('camera feed', frame)

    #print(time() - t)

    # Wait for a user input to quit the application
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# release camera
cap.release()
cv2.destroyAllWindows()




