from PIL import Image
import numpy as np
import customtkinter as ctk
import twophase.solver as sv  # Kociemba's algorithm
import magiccube  # to virtually represent a cube
import threading
import cv2
import csv
from time import sleep, time, monotonic
import Camera  # custom camera script
import Cube  # custom cube script

SPEED_LIMITS = (520, 320)
DELAY_LIMITS = (100, 0)
ctk.set_default_color_theme("dark-blue")
no_camera_image = Image.open("no_camera.png")


def connect_to_cameras(cube_data, b_label: ctk.CTkLabel, t_label: ctk.CTkLabel):
    # Bottom camera
    camB = Camera.Camera(cube_data["camera_ids"][0], flip_upsidedown=True, name="Bottom", box_coords=cube_data["bottom_camera_boxes"])
    camB.label = b_label
    camB.hidden_corner_indexes = Cube.BOTTOM_HIDDEN_CORNERS
    camB.hidden_corner_text_coords = ((530, 400), (300, 20), (20, 420))
    # Top camera
    camT = Camera.Camera(cube_data["camera_ids"][1], name="Top", box_coords=cube_data["top_camera_boxes"])
    camT.label = t_label
    camT.hidden_corner_indexes = Cube.TOP_HIDDEN_CORNERS
    camT.hidden_corner_text_coords = ((20, 40), (550, 40), (300, 465))

    return camB, camT

def get_min_and_max_hsv(col):
    return [(min(col,key=lambda l:l[n])[n], max(col,key=lambda l:l[n])[n]) for n in range(3)]


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("900x850")
        self.resizable(False, False)
        self.bind_all("<q>", lambda e: self.on_close())  # close app on q

        # read in cube data json
        cube_data = Cube.read_from_json()

        # init variables
        self.left_mouse_down = False
        self.right_mouse_down = False
        self.camera_delay = 33  # in ms
        self.show_colour_info = ctk.BooleanVar(value=False)
        self.camera_scale = 0.7
        self.ui_disabled = False
        self.start_time = None
        self.current_timer = "0.000s"
        self.motor_speed = ctk.IntVar(value=cube_data["motor_speed"])
        self.motor_delay = ctk.IntVar(value=cube_data["motor_delay"])
        self.entry_history = []
        self.entry_history_index = 1

        # ---- Define GUI layout ----
        # Header
        # self.label = ctk.CTkLabel(self, text="e", )
        # self.label.pack(expand=True, fill="both")

        # camera ui
        self.camera_frame = ctk.CTkFrame(self, border_width=3)
        self.camera_frame.pack(side="right", fill="both")
        # top camera
        self.top_container = ctk.CTkFrame(self.camera_frame, width=500, corner_radius=0)
        self.top_container.pack(expand=True, fill="both", padx=3, pady=(3, 0))
        self.top_frame = ctk.CTkFrame(self.top_container, height=30)
        self.top_frame.place(relx=0.5, rely=0.5, anchor="center")  # CENTERED
        self.top_title = ctk.CTkLabel(self.top_frame, text="Top Camera", font=("Arial", 20, "bold"))
        self.top_title.pack(pady=(0, 2))
        self.top_camera_label = ctk.CTkLabel(self.top_frame, text="")
        self.top_camera_label.pack()

        # camera controls
        self.cam_controls_container = ctk.CTkFrame(self.camera_frame, height=46, border_width=3, bg_color="#474747")
        self.cam_controls_container.pack(fill="x")
        # inner frame
        self.cam_controls_inner = ctk.CTkFrame(self.cam_controls_container, fg_color="transparent")
        self.cam_controls_inner.place(relx=0.5, rely=0.5, anchor="center")
        # swap cameras button
        self.button = ctk.CTkButton(self.cam_controls_inner, text="⬆⬇ Swap", command=self.swap_cameras, border_width=2)
        self.button.pack(side="left", padx=10)
        # save box coords button
        self.button2 = ctk.CTkButton(self.cam_controls_inner, text="Save quads", command=self.write_box_coords, border_width=2)
        self.button2.pack(side="right", padx=10)
        # show colour info button
        self.button1 = ctk.CTkSwitch(self.cam_controls_inner, text="Show analysis", variable=self.show_colour_info, onvalue=True, offvalue=False)
        self.button1.pack(side="right", padx=10)

        # bottom Camera
        self.bottom_container = ctk.CTkFrame(self.camera_frame, corner_radius=0)
        self.bottom_container.pack(expand=True, fill="both", padx=3, pady=(0, 3))
        self.bottom_frame = ctk.CTkFrame(self.bottom_container, height=30)
        self.bottom_frame.place(relx=0.5, rely=0.5, anchor="center")
        self.bottom_title = ctk.CTkLabel(self.bottom_frame, text="Bottom Camera", font=("Arial", 20, "bold"))
        self.bottom_title.pack(pady=(0, 2))
        self.bottom_camera_label = ctk.CTkLabel(self.bottom_frame, text="")
        self.bottom_camera_label.pack()
        # bind mouse left click to move vertices
        self.bottom_camera_label.bind("<ButtonPress-1>", lambda e: self.set_left_click(True))
        self.bottom_camera_label.bind("<ButtonRelease-1>", lambda e: self.set_left_click(False))
        self.bottom_camera_label.bind("<Button-1>", lambda e: self.cam_clicked(e, self.camB, "left"))
        self.top_camera_label.bind("<ButtonPress-1>", lambda e: self.set_left_click(True))
        self.top_camera_label.bind("<ButtonRelease-1>", lambda e: self.set_left_click(False))
        self.top_camera_label.bind("<Button-1>", lambda e: self.cam_clicked(e, self.camT, "left"))
        # bind mouse right click to move entire boxes
        self.bottom_camera_label.bind("<ButtonPress-3>", lambda e: self.set_right_click(True))
        self.bottom_camera_label.bind("<ButtonRelease-3>", lambda e: self.set_right_click(False))
        self.bottom_camera_label.bind("<Button-3>", lambda e: self.cam_clicked(e, self.camB, "right"))
        self.top_camera_label.bind("<ButtonPress-3>", lambda e: self.set_right_click(True))
        self.top_camera_label.bind("<ButtonRelease-3>", lambda e: self.set_right_click(False))
        self.top_camera_label.bind("<Button-3>", lambda e: self.cam_clicked(e, self.camT, "right"))


        # --- Cube Controls ---
        self.controls_frame = ctk.CTkFrame(self)
        self.controls_frame.pack(side="left", fill="both", expand=True)
        # cube testing functions
        self.inner_frame1 = ctk.CTkFrame(self.controls_frame, border_width=3)
        self.inner_frame1.pack(fill="both", pady=(80, 30), padx=10)
        self.inner_frame1_title = ctk.CTkLabel(self.inner_frame1, text="Testing functions", font=("Arial", 20, "bold"))
        self.inner_frame1_title.pack(pady=5)
        # hsv calibration button
        self.button = ctk.CTkButton(self.inner_frame1, text="Calibrate colours", command=self.calibrate_colour_values, border_width=2)
        self.button.pack(pady=10, padx=(30, 0), side="left")
        # tester button
        self.button4 = ctk.CTkButton(self.inner_frame1, text="Run tests", command=self.tester, border_width=2)
        self.button4.pack(pady=10, padx=(0, 30), side="right")
        # motor speed and delay sliders
        self.inner_frame2 = ctk.CTkFrame(self.controls_frame, border_width=3)
        self.inner_frame2.pack(fill="x", pady=30, padx=10)
        self.inner_frame2_title = ctk.CTkLabel(self.inner_frame2, text="Motor values", font=("Arial", 20, "bold"))
        self.inner_frame2_title.pack(pady=5)
        # motor speed
        speed_slider_frame = ctk.CTkFrame(self.inner_frame2)
        speed_slider_frame.pack(fill="x", pady=10, padx=10)
        speed_slider_title = ctk.CTkLabel(speed_slider_frame, text="Speed", font=("Arial", 20, "bold"))
        speed_slider_title.pack(padx=8, pady=5, side="left")
        self.slider1 = ctk.CTkSlider(speed_slider_frame, from_=SPEED_LIMITS[0], to=SPEED_LIMITS[1],
                                     variable=self.motor_speed, command=self.set_motor_speed_text,
                                     number_of_steps=abs(SPEED_LIMITS[1]-SPEED_LIMITS[0])//10, width=180)
        self.slider1.pack(padx=8, side="left")
        self.speed_slider_amount = ctk.CTkLabel(speed_slider_frame, text="100%", font=("Arial", 20, "bold"))
        self.speed_slider_amount.pack(padx=8, side="right")
        self.set_motor_speed_text(self.motor_speed.get())
        self.slider1.bind("<ButtonRelease-1>", self.update_motor_speeds)
        # motor delay
        delay_slider_frame = ctk.CTkFrame(self.inner_frame2)
        delay_slider_frame.pack(fill="x", pady=(5, 10), padx=10)
        delay_slider_title = ctk.CTkLabel(delay_slider_frame, text="Delay ", font=("Arial", 20, "bold"))
        delay_slider_title.pack(padx=8, pady=5, side="left")
        self.slider2 = ctk.CTkSlider(delay_slider_frame, from_=DELAY_LIMITS[0], to=DELAY_LIMITS[1],
                                     variable=self.motor_delay, command=self.set_motor_delay_text,
                                     number_of_steps=abs(DELAY_LIMITS[0]-DELAY_LIMITS[1])//10, width=180)
        self.slider2.pack(padx=8, side="left")
        self.delay_slider_amount = ctk.CTkLabel(delay_slider_frame, text="100ms", font=("Arial", 20, "bold"))
        self.delay_slider_amount.pack(padx=8, side="right")
        self.set_motor_delay_text(self.motor_delay.get())
        self.slider2.bind("<ButtonRelease-1>", self.update_motor_speeds)

        # cube actions
        self.inner_frame3 = ctk.CTkFrame(self.controls_frame, border_width=3)
        self.inner_frame3.pack(fill="x", pady=(30, 10), padx=10)
        self.inner_frame3_title = ctk.CTkLabel(self.inner_frame3, text="Cube actions", font=("Arial", 20, "bold"))
        self.inner_frame3_title.pack(pady=5)
        # send commands to cube entry
        self.entry = ctk.CTkEntry(self.inner_frame3, width=300, placeholder_text="Execute moves")
        self.entry.pack(padx=10, pady=10)
        self.entry.bind("<Return>", self.submit_cube_moves)
        self.entry.bind("<Down>", lambda e: self.entry_history_lookup(1))
        self.entry.bind("<Up>", lambda e: self.entry_history_lookup(-1))
        # randomly scramble cube button
        self.button3 = ctk.CTkButton(self.inner_frame3, text="Randomly scramble", command=self.scramble_cube, width=220, border_width=2)
        self.button3.pack(padx=10, pady=10)
        # solve cube button
        self.button = ctk.CTkButton(self.inner_frame3, text="Solve cube", command=self.solve_cube, height=45, width=220, fg_color="orange", hover_color="darkorange", text_color="black", border_width=2, font=("Arial", 20, "bold"))
        self.button.pack(padx=10, pady=10)
        self.button.pack(padx=10, pady=10)

        # timer
        self.timer_frame = ctk.CTkFrame(self.controls_frame, border_width=3)
        self.timer_frame.pack(fill="x", pady=0, padx=10)
        self.timer_label = ctk.CTkLabel(self.timer_frame, text=self.current_timer, font=("Arial", 80, "bold"), text_color="green")
        self.timer_label.pack(pady=10)
        self.timer_label.pack()
        self.timer_running = False


        # ---- Create camera objects ----
        self.camB, self.camT = connect_to_cameras(cube_data, self.bottom_camera_label, self.top_camera_label)

        # launch main frame update loops
        self.frame_update_loop(self.camB)
        self.frame_update_loop(self.camT)
        print("Cameras launched")

        # ---- Connect to arduino ----
        self.cube = Cube.Cube()
        # set motor speed values
        if self.cube.arduino is not None:
            self.update_motor_speeds()

    def start_timer(self):
        self.start_time = monotonic()
        self.timer_running = True
        self.update_timer()

    def stop_timer(self):
        self.timer_running = False

    def update_timer(self):
        if not self.timer_running:
            return  # stop updating timer

        elapsed = monotonic() - self.start_time

        secs = int(elapsed)
        ms = int((elapsed * 1000) % 1000)
        self.current_timer = f"{secs}.{ms:03}s"
        self.timer_label.configure(text=self.current_timer)

        self.after(1, self.update_timer)  # update every 1ms

    def set_motor_speed_text(self, v):
        self.speed_slider_amount.configure(text=f"{int((SPEED_LIMITS[0] - v) / abs(SPEED_LIMITS[0]-SPEED_LIMITS[1]) * 100)}%")

    def set_motor_delay_text(self, v):
        self.delay_slider_amount.configure(text=f"{int(v)}ms")

    def update_motor_speeds(self, e=None):
        if self.cube.arduino is None: return

        res = self.cube.arduinoWriteRead(f"{self.motor_speed.get()} {self.motor_delay.get()}")
        print(res)

        # save motor values to json
        cube_data = Cube.read_from_json()
        cube_data["motor_speed"] = self.motor_speed.get()
        cube_data["motor_delay"] = self.motor_delay.get()
        Cube.write_to_json(cube_data)

    def set_left_click(self, state):
        self.left_mouse_down = state

    def set_right_click(self, state):
        self.right_mouse_down = state

    def find_closest_vertex(self, box_coords, mouse_x, mouse_y):
        best_dist = 10000
        closest_box = closest_vertex = None
        # loop through all boxes
        for box_ind, box in enumerate(box_coords):
            # loop through all vertices in box
            for vert_ind, vert in enumerate(box):
                curr_dist = abs(mouse_x - vert[0]) + abs(mouse_y - vert[1])
                if curr_dist < best_dist:
                    best_dist = curr_dist
                    closest_box = box_ind
                    closest_vertex = vert_ind

        return closest_box, closest_vertex

    def cam_clicked(self, event, cam: Camera.Camera, mouse_button, closest_box=None, closest_vertex=None):
        # return if ui is disabled is colour data bot being shown
        if self.ui_disabled or not self.show_colour_info.get():
            return

        # return if mouse button isn't held down anymore
        if ((not self.left_mouse_down and mouse_button == "left") or
            (not self.right_mouse_down and mouse_button == "right")):
            return

        # get current mouse position
        mouse_x = int((cam.label.winfo_pointerx() - cam.label.winfo_rootx())/self.camera_scale)
        mouse_y = int((cam.label.winfo_pointery() - cam.label.winfo_rooty())/self.camera_scale)

        # find the closest box if it hasn't been provided
        if closest_box is None or closest_vertex is None:
            closest_box, closest_vertex = self.find_closest_vertex(cam.box_coords, mouse_x, mouse_y)

        if mouse_button == "left":
            # move vertex to mouse position for left button press
            new_x = int(np.clip(0, mouse_x, cam.width - 1))
            new_y = int(np.clip(0, mouse_y, cam.height - 1))
            cam.box_coords[closest_box][closest_vertex] = [new_x, new_y]
        else:
            # entire box (box centre) to mouse position for right button press
            # calculate quad centre
            centre_x = sum([a for a, b in cam.box_coords[closest_box]])//4
            centre_y = sum([b for a, b in cam.box_coords[closest_box]])//4
            # calculate displacement vector
            vector_x = mouse_x - centre_x
            vector_y = mouse_y - centre_y
            # shift each vertex by that vector
            for vert_ind, vert in enumerate(cam.box_coords[closest_box]):
                new_x = int(np.clip(0, vert[0] + vector_x, cam.width - 1))
                new_y = int(np.clip(0, vert[1] + vector_y, cam.height - 1))
                cam.box_coords[closest_box][vert_ind] = [new_x, new_y]


        # run again after some delay, but with the closest box & vertex already set
        self.after(self.camera_delay, lambda: self.cam_clicked(event, cam, mouse_button, closest_box, closest_vertex))

    def swap_cameras(self):
        # swap cap variables of each camera object
        self.camT.cap, self.camB.cap = self.camB.cap, self.camT.cap

        # swap device ids in the json
        cube_data = Cube.read_from_json()
        cube_data["camera_ids"] = cube_data["camera_ids"][::-1]

        # save json
        Cube.write_to_json(cube_data)

    def disable_ui(self, val):
        self.ui_disabled = val

    def write_box_coords(self):
        # read the json file
        cube_data = Cube.read_from_json()

        # modify the camera coords
        cube_data["bottom_camera_boxes"] = self.camB.box_coords
        cube_data["top_camera_boxes"] = self.camT.box_coords

        # save data to cube_data.json file
        Cube.write_to_json(cube_data)

        print("Box coords saved.")

    def send_to_arduino(self, command, callback=None):
        # disable UI
        self.disable_ui(True)

        # strip command
        old_command = command
        if "Solve: " in command:
            command = command[command.find("Solve: ") + 7:]

        # async arduino wait
        def wait_for_response():
            response = self.cube.arduinoWriteRead(command) + ". Command: " + old_command
            self.after(0, lambda: self.on_response(response, callback))

        # create thread to wait for arduino response and then call on_response function
        threading.Thread(target=wait_for_response, daemon=True).start()

    def on_response(self, response, callback):
        self.stop_timer()
        self.disable_ui(False)
        print(response)

        if callback is not None:
            callback(response)


    def submit_cube_moves(self, event=None):
        # return if ui is disabled
        if self.ui_disabled:
            return

        # get text from entry
        text = self.entry.get().strip().upper()
        self.entry_history.insert(0, text)
        self.entry_history_index = 0


        # test text validity
        text_split = text.split(" ")
        if not text or not((len(text_split) == 2 and text_split[0].isnumeric() and text_split[1].isnumeric()) or
                all((c[0] in "UDLRFB") and (len(c) == 1 or (len(c) == 2 and c[1] in "\'2")) for c in
                    (text_split[:-1] if text_split[-1].isnumeric() else text_split))):
            print("Invalid command")
            return

        # multiply moves if last word is a number
        if not text_split[0].isnumeric() and text_split[-1].isnumeric():
            text = " ".join(text_split[:-1] * int(text_split[-1]))

        # delete entered text
        self.entry.delete(0, "end")

        # send moves to arduino
        self.send_to_arduino(text)

    def entry_history_lookup(self, direction):
        if len(self.entry_history) == 0:
            return

        self.entry_history_index += direction
        if self.entry_history_index < 0:
            self.entry_history_index = 0
        elif self.entry_history_index >= len(self.entry_history)-1:
            self.entry_history_index = len(self.entry_history) - 1

        text = self.entry_history[self.entry_history_index]

        self.entry.delete(0, "end")
        self.entry.insert(0, text)


    def scramble_cube(self, callback=None):
        # return if ui is disabled
        if self.ui_disabled:
            return None

        scramble = Cube.getRandomScramble()
        print("Cube scramble:", scramble)

        self.send_to_arduino(scramble, callback)

        return scramble

    def analyse_image(self, cam: Camera.Camera, frame):
        # get median hsv for each piece
        median_hsv_colours = cam.get_median_hsv_colours(frame)
        # classify hsv colours
        piece_colours = Camera.classify_hsv_colours(median_hsv_colours)
        # figure out hidden corner colours
        hidden_corners = cam.get_hidden_corner_colours(piece_colours)

        return median_hsv_colours, piece_colours, hidden_corners

    def write_data_on_image(self, cam: Camera.Camera, frame, median_hsv_colours, piece_colours, hidden_corners):
        # draw boxes on image
        frame = cam.draw_boxes(frame)
        # # write piece colours text on image
        frame = cam.write_colour_values(frame, median_hsv_colours, piece_colours)
        # # write hidden corner colours on image
        for i, (x, y) in enumerate(cam.hidden_corner_text_coords):
            if hidden_corners[i] is None: continue
            frame = cv2.putText(frame, f"{Camera.COLOUR_NAMES[hidden_corners[i]]}", (x, y),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.75, Camera.BOX_COLOUR, 2, 2)
        return frame

    def error_check(self, curr_hsv, reference_hsv, cam, id_, ac):
        if reference_hsv and abs(curr_hsv[0] - next(iter(reference_hsv))[0]) > 30:
            print(cam, id_, "error found", curr_hsv, ac)
            return False
        return True

    def calibrate_colour_values(self):
        # return if ui is disabled
        if self.ui_disabled:
            return

        # --- cube must be in a solved state ---
        #        low hue red, orange, yellow, green, blue, high hue red
        hsv_colours = [set(), set(), set(), set(), set(), set()]  # to store collected colour data
        white_colours = set()
        # create virtual copy
        mc = magiccube.Cube(3, "".join(c * 9 for c in "WOGRBY"))
        # generate random scramble
        scramble = Cube.getRandomScramble()
        # scramble virtual cube
        mc.rotate(scramble)
        # scramble physical cube
        self.cube.arduinoWriteRead(scramble)
        # do some random moves and get colour data after each one
        for _ in range(10):
            # choose some random moves
            move = Cube.get_random_moves(4, double_moves=True)
            # execute it virtually
            mc.rotate(move)
            # execute it physically
            self.cube.arduinoWriteRead(move)
            sleep(0.05)
            # convert magiccube to TwoPhase index format
            cubestring = Cube.magiccubeToTwoPhase(mc)
            # read colour data
            self.camB.get_frame()  # dump buffered frame
            self.camB.get_frame()
            frameB = self.camB.get_frame()
            # Image.fromarray(frame).show()
            camB_median_hsv_colours = self.camB.get_median_hsv_colours(frameB)
            self.camT.get_frame()  # dump buffered frame
            self.camT.get_frame()
            frameT = self.camT.get_frame()
            # Image.fromarray(frame).show()
            camT_median_hsv_colours = self.camT.get_median_hsv_colours(frameT)
            # convert between camera data and cube positions
            aB, aT = [], []
            for median_hsv_colours, conv, a in ((camB_median_hsv_colours, Cube.camB_conv, "b"), (camT_median_hsv_colours, Cube.camT_conv, "t")):
                for i in range(len(median_hsv_colours)):
                    hsv_value = median_hsv_colours[i]
                    actual_colour = "RLDFBU".find(cubestring[conv[i]])


                    if actual_colour == 5:
                        # if white - add it to the white ranges
                        white_colours.add(hsv_value)
                    elif actual_colour == 0 and hsv_value[0] > 100:
                        # if red with a high hue - add it to the end
                        if self.error_check(hsv_value, hsv_colours[-1], a, i, actual_colour): hsv_colours[-1].add(hsv_value)
                    else:
                        # else - add it to the proper place
                        if self.error_check(hsv_value, hsv_colours[actual_colour], a, i, actual_colour): hsv_colours[actual_colour].add(hsv_value)

            # display B image
            # frame = self.write_data_on_image(self.camT, frameT, aT, [None] * len(aT), [None]*3)
            # Image.fromarray(frame).show()

        print("White colours:", white_colours)
        print(*hsv_colours, sep="\n")

        # add in dummy high hue red if non were found
        if not hsv_colours[-1]: hsv_colours[-1].add((175, 255, 100))

        # remove highest and lowest 3 hue values from each set
        for i in range(len(hsv_colours)):
            if len(hsv_colours[i]) <= 6: continue
            sorted_range = sorted(hsv_colours[i].copy())
            for j in range(3):
                hsv_colours[i].remove(sorted_range[j])
                hsv_colours[i].remove(sorted_range[-j-1])
        print("After removing:")
        print(*hsv_colours, sep="\n")

        # find min and max HSV all colours
        hsv_ranges = [get_min_and_max_hsv(col) for col in hsv_colours]
        white_hsv_ranges = get_min_and_max_hsv(white_colours)
        print("HSV ranges:", *hsv_ranges, sep="\n")
        print("White HSV ranges:", white_hsv_ranges)

        # calculate hue ranges
        new_hue_ranges = [0]
        for col_ind in range(1, 6):
            # get hue in between current min and previous max
            new_hue_ranges.append((hsv_ranges[col_ind][0][0] + hsv_ranges[col_ind-1][0][1]) // 2)
        new_hue_ranges.append(181)  # append hue limit for high hue reds
        print("New hue ranges:", new_hue_ranges)

        # get white limits
        white_s_max = white_hsv_ranges[1][1] + 5
        white_v_min = white_hsv_ranges[2][0] - 5
        print(f"White limits: s <= {white_s_max}  &  v >= {white_v_min}")

        # find overlapping reds and oranges
        reds_that_could_be_oranges = []
        for red in hsv_colours[0]:
            # if a red values hue is higher than the lowest oranges hue
            if red[0] >= hsv_ranges[1][0][0]:
                reds_that_could_be_oranges.append(red)
        if reds_that_could_be_oranges:
            bad_reds_hsv_ranges = get_min_and_max_hsv(reds_that_could_be_oranges)
            print("bad red colours:", reds_that_could_be_oranges)
            print(f"For 1 <= hue <= {bad_reds_hsv_ranges[0][1]} -> red if value <= {bad_reds_hsv_ranges[2][1]}")
        else:
            print("No bad red colours found!")

        # update stored values

        # update current values

        # solve the cube
        solve = Cube.twophaseToNormal(sv.solve(Cube.magiccubeToTwoPhase(mc), 0, 0.1))
        print(solve)
        self.send_to_arduino(solve)

    def frame_update_loop(self, cam: Camera.Camera):
        frame = None
        if cam: frame = cam.get_frame()

        if frame is not None:
            # show colour info on camera frame
            if self.show_colour_info.get():
                median_hsv_colours, piece_colours, hidden_corners = self.analyse_image(cam, frame)
                frame = self.write_data_on_image(cam, frame, median_hsv_colours, piece_colours, hidden_corners)
            img = Image.fromarray(frame)
        else:
            img = no_camera_image

        # display image in GUI
        ctk_img = ctk.CTkImage(light_image=img, size=(int(img.width * self.camera_scale),
                                                      int(img.height * self.camera_scale)))
        cam.label.configure(image=ctk_img)
        cam.label.image = ctk_img

        # Call again after set delay
        self.after(self.camera_delay, lambda: self.frame_update_loop(cam))

    def get_colour_data_from_cams(self):
        # get frame from each camera
        B_frame = self.camB.get_frame()
        T_frame = self.camT.get_frame()
        if B_frame is None or T_frame is None:
            print("Camera frame failed")
            return None, None

        # get colour data from camera frames
        B_data = self.analyse_image(self.camB, B_frame)
        T_data = self.analyse_image(self.camT, T_frame)

        return B_data, T_data

    def solve_cube(self, callback=None):
        if self.camT.cap is None or self.camB.cap is None:
            print("Cameras not connected")
            if callback is not None: callback(None)
            return None

        # return if ui is disabled
        if self.ui_disabled:
            return None

        # set start time
        self.start_timer()
        # attempt to solve many times
        for attempt in range(200):
            # get colour data from camera frames
            B_data, T_data = self.get_colour_data_from_cams()
            # set cubestate
            self.cube.set_cubestate(B_data[1], B_data[2], T_data[1], T_data[2])
            # try to solve
            solve = self.cube.solve_cube()
            if solve == "":
                print("Cube already solved!")
                self.stop_timer()
                if callback is not None: callback(solve)
                return solve
            elif not solve.startswith("Error"):
                solve_result = f"Attempt {attempt+1}. Solve: {solve}"
                self.send_to_arduino(solve_result, callback=callback)
                return solve

        self.stop_timer()
        print("Couldn't solve cube")
        if callback is not None: callback(None)
        return None

    def save_test_data(self, test_doc, data):
        with open(test_doc, "a", newline='') as file:
            writer = csv.writer(file)
            writer.writerow(map(str, data))
            file.close()

    def tester(self, i = 0, limit = 100, data_file=None):
        # repeatedly scramble and solve the cube and save the data
        if i == limit:
            # calculate averages
            with open(data_file, "r", newline='') as file:
                reader = csv.DictReader(file)
                successes = []
                times = []
                attempts = []
                moves = []
                turns = []
                tps = []
                for row in reader:
                    successes.append(1 if row['Success'] == "True" else 0)
                    if row['Success'] == "True":
                        successes.append(1)
                        times.append(float(row['Time']))
                        attempts.append(int(row['Attempt']))
                        moves.append(int(row['Moves']))
                        turns.append(int(row['Turns']))
                        tps.append(float(row['TPS']))
                    else:
                        successes.append(0)
                file.close()

            success_rate = f"{sum(successes) / len(successes) * 100:.2f}%"
            avg_time = round(sum(times) / len(times), 3)
            avg_attempt = round(sum(attempts) / len(attempts), 1)
            avg_moves = round(sum(moves) / len(moves), 1)
            avg_turns = round(sum(turns) / len(turns), 1)
            avg_tps = round(sum(tps) / len(tps), 2)

            # write averages
            with open(data_file, "a", newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["", "", "", success_rate, avg_time, avg_attempt, avg_moves, avg_turns, avg_tps])
                file.close()

            return

        if data_file is None:
            # create new data file
            data_file = f"Test_data\\test_{int(time())}.csv"
            with open(data_file, "w", newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Test #", "Scramble", "Solution", "Success", "Time", "Attempt", "Moves", "Turns", "TPS"])

                file.close()

        scramble = None

        def after_scramble(scramble_response):
            print("Scrambled:", scramble)
            print("Scramble response:", scramble_response)

            def tester_received_response(response):
                # write results to file
                print("Solve response:", response)
                print("Actual time taken", self.current_timer)
                was_solved = not(response is None or response.startswith("Error"))

                def run_next_test(failed_response = None):
                    # save results to test data file
                    if response is not None:
                        time_taken, moves, tps, attempt, solution = response.split(". ")
                        time_taken = self.current_timer.rstrip("s")
                        moves, turns = moves.lstrip("Moves: ").split()
                        turns = turns.strip("()")
                        tps = tps.lstrip("TPS: ")
                        attempt = attempt.lstrip("Command: Attempt: ")
                        solution = solution.lstrip("Solve: ")
                    else:
                        time_taken = moves = turns = tps = attempt = ""
                        solution = failed_response[failed_response.find("Command: ") + 9:]

                    #["Test #", "Scramble", "Solution", "Success", "Time", "Attempt", "Moves", "Turns", "TPS"]
                    data =  [i, scramble, solution, was_solved, time_taken, attempt, moves, turns, tps]
                    self.save_test_data(data_file, data)

                    self.after(100, lambda: self.tester(i + 1, limit, data_file))

                if not was_solved:
                    # solve cube manually
                    self.cube.state = Cube.scrambleCube(scramble)
                    self.send_to_arduino(self.cube.solve_cube(), run_next_test)
                else:
                    run_next_test()

            # refresh cam frames
            self.camB.get_frame()
            self.camT.get_frame()
            # try to solve
            print("Starting solve")
            self.after(100, lambda: self.solve_cube(callback=tester_received_response))


        # randomly scramble
        scramble = self.scramble_cube(after_scramble)






    def on_close(self):
        # release cameras
        if self.camB.cap:
            self.camB.release()
            print("Bottom camera disconnected")
        if self.camT.cap:
            self.camT.release()
            print("Top camera disconnected")

        # release arduino
        if self.cube.arduino:
            self.cube.release()
            print("Arduino disconnected")

        # destroy GUI app
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
