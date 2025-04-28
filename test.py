import cv2
from time import sleep
from fractions import Fraction

# Open the device
cap1 = cv2.VideoCapture(0)
cap2 = cv2.VideoCapture(1)
# set camera resolution
cap1.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # 640x480
cap1.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
# set camera resolution
cap2.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # 640x480
cap2.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

sleep(0.5)

while True:
    # Capture frame
    ret, frame = cap1.read()
    frame = cv2.rotate(frame, cv2.ROTATE_180)  # flip image upsidedown
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # convert to rgb

    cv2.imshow('camera feed 1', cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    ret, frame = cap2.read()
    frame = cv2.rotate(frame, cv2.ROTATE_180)  # flip image upsidedown
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # convert to rgb

    cv2.imshow('camera feed 2', cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    if cv2.waitKey(1) & 0xFF == ord('q') or cv2.getWindowProperty('camera feed 1', cv2.WND_PROP_VISIBLE) < 1:
        # release camera
        cap1.release()
        cap2.release()
        cv2.destroyAllWindows()
        exit()
