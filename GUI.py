import math
import cv2
import numpy as np
import customtkinter as ctk
from PIL import Image, ImageTk
from time import sleep, time

# define constants
COLOUR_HUE_RANGES = (0, 3, 25, 50, 85, 160, 181)
#                 0       1         2         3       4        5
COLOUR_NAMES = ["red", "orange", "yellow", "green", "blue", "white"]
RGB_COLOUR_VALUES = ((255, 0, 0), (255, 128, 0), (255, 255, 0), (0, 255, 0), (0, 0, 255), (255, 255, 255))
BOX_SIZE = 5
BOX_COLOUR = (38, 247, 253)

# corner piece colours in order of top, right, front
CORNER_COLOURS = ((5, 4, 0), (5, 0, 3), (5, 3, 1), (5, 1, 4), (2, 4, 1), (2, 1, 3), (2, 3, 0), (2, 0, 4))

# read box pixel coordinates for top and bottom cameras
with open("camB_boxes.txt", "r") as f:
    camB_boxes = [list(map(int, l.split())) for l in f.readlines()]
    f.close()
with open("camT_boxes.txt", "r") as f:
    camT_boxes = [list(map(int, l.split())) for l in f.readlines()]
    f.close()


# main GUI app
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("800x800")
        self.resizable(False, False)

        # init variables
        self.mouse_held = False
        self.camera_delay = 1  # in ms

        # Header
        # self.label = ctk.CTkLabel(self, text="e", )
        # self.label.pack(expand=True, fill="both")

        # Main camera frame
        self.camera_frame = ctk.CTkFrame(self)
        self.camera_frame.pack(side="right", fill="both")
        # ---- Top Camera ----
        self.top_container = ctk.CTkFrame(self.camera_frame, width=500)
        self.top_container.pack(expand=True, fill="both")
        self.top_frame = ctk.CTkFrame(self.top_container)
        self.top_frame.place(relx=0.5, rely=0.5, anchor="center")  # CENTERED
        self.top_title = ctk.CTkLabel(self.top_frame, text="Top Camera", font=("Arial", 20, "bold"))
        self.top_title.pack(pady=(0, 2))
        self.top_camera_label = ctk.CTkLabel(self.top_frame, text="")
        self.top_camera_label.pack()
        # ---- Bottom Camera ----
        self.bottom_container = ctk.CTkFrame(self.camera_frame)
        self.bottom_container.pack(expand=True, fill="both")
        self.bottom_frame = ctk.CTkFrame(self.bottom_container)
        self.bottom_frame.place(relx=0.5, rely=0.5, anchor="center")  # CENTERED
        self.bottom_title = ctk.CTkLabel(self.bottom_frame, text="Bottom Camera", font=("Arial", 20, "bold"))
        self.bottom_title.pack(pady=(0, 2))
        self.bottom_camera_label = ctk.CTkLabel(self.bottom_frame, text="")
        self.bottom_camera_label.pack()

        # bind mouse left click to move boxes
        self.bottom_camera_label.bind("<ButtonPress-1>", lambda e: self.set_mouse(True))
        self.bottom_camera_label.bind("<ButtonRelease-1>", lambda e: self.set_mouse(False))
        self.bottom_camera_label.bind("<Button-1>", lambda e: self.cam_clicked(e, "Bottom"))

        self.top_camera_label.bind("<ButtonPress-1>", lambda e: self.set_mouse(True))
        self.top_camera_label.bind("<ButtonRelease-1>", lambda e: self.set_mouse(False))
        self.top_camera_label.bind("<Button-1>", lambda e: self.cam_clicked(e, "Top"))


        # Buttons
        self.controls_frame = ctk.CTkFrame(self)
        self.controls_frame.pack(side="left", fill="both", expand=True)
        self.inner_frame = ctk.CTkFrame(self.controls_frame)
        self.inner_frame.place(relx=0.5, rely=0, anchor="n")
        self.button = ctk.CTkButton(self.inner_frame, text="Capture1", command=self.capture, width=300)
        self.button.pack(pady=10, padx=10)
        self.button1 = ctk.CTkButton(self.inner_frame, text="Capture2", command=self.capture)
        self.button1.pack(pady=10, padx=10)
        self.button2 = ctk.CTkButton(self.inner_frame, text="Save box coords", command=self.write_box_coords)
        self.button2.pack(pady=10, padx=10)

        # Open camera
        self.capB = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.capT = cv2.VideoCapture(1, cv2.CAP_DSHOW)
        # Apply camera settings
        for cap in [self.capB, self.capT]:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # 640x480
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_EXPOSURE, -1)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # launch cameras
        self.update_frames()
        print("Cameras launched")

    def update_frames(self):
        for cam_name, cap, camera_label, box_coords in (
                ("Bottom", self.capB, self.bottom_camera_label, camB_boxes),
                ("Top", self.capT, self.top_camera_label, camT_boxes)):

            ret, frame = cap.read()

            if ret and frame is not None:
                # flip image upsidedown if it's the bottom camera
                if cam_name == "Bottom": frame = cv2.rotate(frame, cv2.ROTATE_180)
                # Convert BGR → RGB
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # change image contrast
                cv2.normalize(frame, frame, 0, 1100, cv2.NORM_MINMAX)

                # get median hsv for each piece
                pieces_median_hsv = self.get_median_hsv(frame, box_coords)
                # classify hsv colours
                piece_colours = [self.classify_colour(median_hsv) for median_hsv in pieces_median_hsv]

                # figure out hidden corner colours
                if cam_name == "Bottom":
                    corner1 = self.get_last_corner_colour(piece_colours[18], piece_colours[9])
                    corner2 = self.get_last_corner_colour(piece_colours[12], piece_colours[6])
                    corner3 = self.get_last_corner_colour(piece_colours[0], piece_colours[14])
                    corners = [corner1, corner2, corner3]
                    for i, (x, y) in enumerate(((530, 400), (300, 20), (20, 420))):
                        if corners[i] is None: continue
                        frame = cv2.putText(frame, f"{COLOUR_NAMES[corners[i]]}", (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.75, BOX_COLOUR, 2, 2)


                # draw boxes
                frame = self.draw_boxes(frame, box_coords)
                # draw text
                frame = self.add_text(frame, box_coords, pieces_median_hsv, piece_colours)

                # display image in GUI
                img = Image.fromarray(frame)  # Convert to PIL image
                scale = 0.7
                ctk_img = ctk.CTkImage(light_image=img, size=(int(img.width * scale), int(img.height * scale)))
                camera_label.configure(image=ctk_img)
                camera_label.image = ctk_img
            else:
                print("Camera frame failed")

        # Call again after set delay
        self.after(self.camera_delay, self.update_frames)

    def on_close(self):
        self.capB.release()
        self.capT.release()
        print("Cameras closed")
        self.destroy()

    def capture(self):
        print("Button")

    def set_mouse(self, state):
        self.mouse_held = state

    def cam_clicked(self, event, cam, best_i=None):
        # return if mouse 1 isn't held down anymore
        if not self.mouse_held:
            return

        # m_x, m_y = int(event.x/0.7), int(event.y/0.7)
        box_coords = camT_boxes if cam == "Top" else camB_boxes
        label = self.top_camera_label if cam == "Top" else self.bottom_camera_label

        # get current mouse position
        m_x = int((label.winfo_pointerx() - label.winfo_rootx())/0.7)
        m_y = int((label.winfo_pointery() - label.winfo_rooty())/0.7)

        # find the closest box if it hasn't been provided
        if best_i is None:
            best_dist = 10000
            best_i = None
            for i, box in enumerate(box_coords):
                curr_dist = abs(m_x - box[0]) + abs(m_y - box[1])
                if curr_dist < best_dist:
                    best_dist = curr_dist
                    best_i = i

        # move box to mouse position
        box_coords[best_i] = [m_x, m_y]
        # run again set delay
        self.after(self.camera_delay, lambda: self.cam_clicked(event, cam, best_i))


    def write_box_coords(self):
        with open("camB_boxes.txt", "w") as f:
            for box_x, box_y in camB_boxes:
                f.write(f"{box_x} {box_y}\n")
            f.close()

        with open("camT_boxes.txt", "w") as f:
            for box_x, box_y in camT_boxes:
                f.write(f"{box_x} {box_y}\n")
            f.close()

        print("Box coords saved.")

    def classify_colour(self, given_colour):
        h, s, v = given_colour

        # white - low Saturation and high Value
        if s < 185 and v > 90:
            return 5

        # special case to determine red or orange for low hue
        if 1 < h < 10:
            # red for Value bellow 140, orange for above
            return 0 if v < 100 else 1

        # determine colour (match to colour hue ranges)
        for i in range(len(COLOUR_HUE_RANGES)-1):
            if COLOUR_HUE_RANGES[i] <= h < COLOUR_HUE_RANGES[i+1]:
                return i % 5  # wrap back around to red

        return None


    def get_median_hsv(self, img, coords, size=BOX_SIZE):
        colours = []
        for i, (x, y) in enumerate(coords):
            area = img[y-size:y+size+1, x-size:x+size+1]

            # apply Gaussian blur (reduces grain)
            area = cv2.GaussianBlur(area, (size, size), 0)
            # convert to HSV
            area = cv2.cvtColor(area, cv2.COLOR_RGB2HSV)

            # calculate median of each value in box area
            median_hsv = tuple(int(np.median(area[:, :, k])) for k in range(3))
            colours.append(median_hsv)

        return colours

    def draw_boxes(self, img, coords, size=BOX_SIZE):
        for i, (x, y) in enumerate(coords):
            img = cv2.rectangle(img, (x - size, y - size), (x + size, y + size), BOX_COLOUR, 2)
        return img

    def add_text(self, img, coords, hsv_values, colours):
        for i, (x, y) in enumerate(coords):
            curr_colour = BOX_COLOUR if colours[i] is None else RGB_COLOUR_VALUES[colours[i]]
            img = cv2.putText(img, f"{hsv_values[i]}", (x + 10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, curr_colour, 2, 2)
        return img

    def get_last_corner_colour(self, colour1, colour2):
        # find matching piece with matching colours in same order
        correct_order = (colour1, colour2)
        for corner in CORNER_COLOURS:
            if corner[0:2] == correct_order:
                return corner[2]
            elif corner[1:3] == correct_order:
                return corner[0]
            elif (corner[2], corner[0]) == correct_order:
                return corner[1]
        return None


app = App()
app.protocol("WM_DELETE_WINDOW", app.on_close)
app.mainloop()