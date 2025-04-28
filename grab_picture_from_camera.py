import cv2
from time import sleep
from fractions import Fraction

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


while True:
    # Capture frame
    ret, frame = cap.read()
    frame = cv2.rotate(frame, cv2.ROTATE_180)  # flip image upsidedown
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # convert to rgb

    cv2.imshow('camera feed before contrast change', cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    cv2.imwrite("pics\\raw_frame8.png", cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    cv2.normalize(frame, frame, 0, 1100, cv2.NORM_MINMAX)  # change image contrast

    # Display the resulting frame
    cv2.imshow('camera feed', cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    cv2.imwrite("pics\\contrasted_frame8.png", cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    if cv2.waitKey(1) & 0xFF == ord('q') or cv2.getWindowProperty('camera feed', cv2.WND_PROP_VISIBLE) < 1:
        # release camera
        cap.release()
        cv2.destroyAllWindows()
        exit()
