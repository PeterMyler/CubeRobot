import cv2
import threading
from PIL import Image
import customtkinter as ctk
import twophase.solver as sv  # to solve the cube
import magiccube  # to virtually represent a cube
from time import process_time, sleep

import Camera  # import custom camera script
import Cube  # import custom cube script

def connect_to_cameras(b_id: int, t_id: int, b_label: ctk.CTkLabel, t_label: ctk.CTkLabel):
    # Bottom camera
    camB = Camera.Camera(b_id, flip_upsidedown=True, name="Bottom", box_coords="camB_boxes.txt")
    camB.label = b_label
    camB.hidden_corner_indexes = ((18, 9), (12, 6), (0, 14))
    camB.hidden_corner_text_coords = ((530, 400), (300, 20), (20, 420))
    # Top camera
    camT = Camera.Camera(t_id, name="Top", box_coords="camT_boxes.txt")
    camT.label = t_label
    camT.hidden_corner_indexes = ((7, 4), (20, 13), (1, 14))
    camT.hidden_corner_text_coords = ((20, 40), (550, 40), (300, 465))

    return camB, camT

def get_min_and_max_hsv(col):
    return [(min(col,key=lambda l:l[n])[n], max(col,key=lambda l:l[n])[n]) for n in range(3)]


# main GUI app
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("800x800")
        self.resizable(False, False)

        # init variables
        self.mouse_held = False
        self.camera_delay = 33  # in ms
        self.show_colour_info = ctk.BooleanVar(value=False)
        self.camera_scale = 0.7
        self.ui_disabled = False

        # ---- Define GUI layout ----
        # Header
        # self.label = ctk.CTkLabel(self, text="e", )
        # self.label.pack(expand=True, fill="both")
        # main camera frame
        self.camera_frame = ctk.CTkFrame(self)
        self.camera_frame.pack(side="right", fill="both")
        # Top Camera
        self.top_container = ctk.CTkFrame(self.camera_frame, width=500)
        self.top_container.pack(expand=True, fill="both")
        self.top_frame = ctk.CTkFrame(self.top_container)
        self.top_frame.place(relx=0.5, rely=0.5, anchor="center")  # CENTERED
        self.top_title = ctk.CTkLabel(self.top_frame, text="Top Camera", font=("Arial", 20, "bold"))
        self.top_title.pack(pady=(0, 2))
        self.top_camera_label = ctk.CTkLabel(self.top_frame, text="")
        self.top_camera_label.pack()
        # Bottom Camera
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
        # frames
        self.controls_frame = ctk.CTkFrame(self)
        self.controls_frame.pack(side="left", fill="both", expand=True)
        self.inner_frame = ctk.CTkFrame(self.controls_frame)
        self.inner_frame.place(relx=0.5, rely=0, anchor="n")
        # swap cameras button
        self.button = ctk.CTkButton(self.inner_frame, text="Swap cameras", command=self.swap_cameras)
        self.button.pack(pady=10, padx=10)
        # hsv calibration button
        self.button = ctk.CTkButton(self.inner_frame, text="Calibrate cameras", command=self.calibrate_colour_values)
        self.button.pack(pady=10, padx=10)
        # solve cube button
        self.button = ctk.CTkButton(self.inner_frame, text="Solve cube", command=self.solve_cube, width=300, fg_color="orange")
        self.button.pack(pady=10, padx=10)
        self.button.pack(pady=10, padx=10)
        # show colour info button
        self.button1 = ctk.CTkSwitch(self.inner_frame, text="Show colour info", variable=self.show_colour_info, onvalue=True, offvalue=False)
        self.button1.pack(pady=10, padx=10)
        # save box coords button
        self.button2 = ctk.CTkButton(self.inner_frame, text="Save box coords", command=self.write_box_coords)
        self.button2.pack(pady=10, padx=10)
        # randomly scramble cube button
        self.button2 = ctk.CTkButton(self.inner_frame, text="Randomly scramble cube", command=self.scramble_cube)
        self.button2.pack(pady=10, padx=10)
        # send commands to cube entry
        self.entry = ctk.CTkEntry(self.inner_frame, width=300)
        self.entry.pack(padx=20, pady=20)
        self.entry.bind("<Return>", self.submit_cube_moves)


        # ---- Create camera objects ----
        self.camB, self.camT = connect_to_cameras(1, 0, self.bottom_camera_label, self.top_camera_label)

        # launch main frame update loops
        self.frame_update_loop(self.camB)
        self.frame_update_loop(self.camT)
        print("Cameras launched")

        # ---- Connect to arduino ----
        self.cube = Cube.Cube()
        if self.cube is None:
            print("Failed to create cube")
            exit(1)

    def set_mouse(self, state):
        self.mouse_held = state

    def toggle_show_colour_info(self):
        self.show_colour_info = not self.show_colour_info

    def cam_clicked(self, event, cam_name, best_i=None):
        # return if ui is disabled
        if self.ui_disabled:
            return

        # return if mouse 1 isn't held down anymore
        if not self.mouse_held:
            return

        # m_x, m_y = int(event.x/0.7), int(event.y/0.7)
        if cam_name == "Top":
            curr_box_coords = self.camT.box_coords
            curr_label = self.top_camera_label
        else:
            curr_box_coords = self.camB.box_coords
            curr_label = self.bottom_camera_label

        # get current mouse position
        m_x = int((curr_label.winfo_pointerx() - curr_label.winfo_rootx())/self.camera_scale)
        m_y = int((curr_label.winfo_pointery() - curr_label.winfo_rooty())/self.camera_scale)

        # find the closest box if it hasn't been provided
        if best_i is None:
            best_dist = 10000
            best_i = None
            for i, box in enumerate(curr_box_coords):
                curr_dist = abs(m_x - box[0]) + abs(m_y - box[1])
                if curr_dist < best_dist:
                    best_dist = curr_dist
                    best_i = i

        # move box to mouse position
        curr_box_coords[best_i] = [m_x, m_y]
        # run again set delay
        self.after(self.camera_delay, lambda: self.cam_clicked(event, cam_name, best_i))

    def swap_cameras(self):
        # swap cap variables of each camera object
        self.camT.cap, self.camB.cap = self.camB.cap, self.camT.cap

    def disable_ui(self, val):
        self.ui_disabled = val

    def write_box_coords(self):
        with open("camB_boxes.txt", "w") as f:
            for box_x, box_y in self.camB.box_coords:
                f.write(f"{box_x} {box_y}\n")
            f.close()

        with open("camT_boxes.txt", "w") as f:
            for box_x, box_y in self.camT.box_coords:
                f.write(f"{box_x} {box_y}\n")
            f.close()

        print("Box coords saved.")

    def send_to_arduino(self, command):
        # disable UI
        self.disable_ui(True)

        # async arduino wait
        def wait_for_response():
            response = self.cube.arduinoWriteRead(command)
            self.after(0, self.on_response, response)

        # create thread to wait for arduino response and then call on_response function
        threading.Thread(target=wait_for_response, daemon=True).start()

    def on_response(self, response):
        # enable UI
        self.disable_ui(False)

        # display response
        print(response)


    def submit_cube_moves(self, event=None):
        # return if ui is disabled
        if self.ui_disabled:
            return

        # get text from entry
        text = self.entry.get().strip().upper()
        print(text)

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

    def scramble_cube(self):
        # return if ui is disabled
        if self.ui_disabled:
            return None

        # scramble = self.cube.scramble_cube(use_precalculated=True)
        scramble = Cube.getRandomScramble()
        print("Cube scramble:", scramble)

        self.send_to_arduino(scramble)

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
        # write piece colours text on image
        frame = cam.write_colour_values(frame, median_hsv_colours, piece_colours)
        # write hidden corner colours on image
        for i, (x, y) in enumerate(cam.hidden_corner_text_coords):
            if hidden_corners[i] is None: continue
            frame = cv2.putText(frame, f"{Camera.COLOUR_NAMES[hidden_corners[i]]}", (x, y),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.75, Camera.BOX_COLOUR, 2, 2)
        return frame

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
        # scramble physical cube
        # scramble = self.scramble_cube()
        # scramble virtual cube
        # mc.rotate(scramble)
        # do 50 random moves and get colour data after each one
        for _ in range(10):
            # choose a random move
            move = Cube.get_random_move(double_moves=False)
            # execute it virtually
            mc.rotate(move)
            # execute it physically
            self.cube.arduinoWriteRead(move)
            sleep(0.2)
            # convert magiccube to TwoPhase index format
            cubestring = Cube.magiccubeToTwoPhase(mc)
            # read colour data
            self.camB.get_frame()  # dump buffered frame
            frame = self.camB.get_frame()
            # Image.fromarray(frame).show()
            camB_median_hsv_colours = self.camB.get_median_hsv_colours(frame)
            self.camT.get_frame()  # dump buffered frame
            frame = self.camT.get_frame()
            # Image.fromarray(frame).show()
            camT_median_hsv_colours = self.camT.get_median_hsv_colours(frame)
            # convert between camera data and cube positions
            for median_hsv_colours, conv in ((camB_median_hsv_colours, Cube.camB_conv), (camT_median_hsv_colours, Cube.camT_conv)):
                for i in range(len(median_hsv_colours)):
                    hsv_value = median_hsv_colours[i]
                    actual_colour = "RLDFBU".find(cubestring[conv[i]])

                    if actual_colour == 5:
                        # if white - add it to the white ranges
                        white_colours.add(hsv_value)
                    elif actual_colour == 0 and hsv_value[0] > 100:
                        # if red with a high hue - add it to the end
                        hsv_colours[-1].add(hsv_value)
                    else:
                        # else - add it to the proper place
                        hsv_colours[actual_colour].add(hsv_value)
            # break

        print(*hsv_colours, sep="\n")

        # add in dummy high hue red if non were found
        if not hsv_colours[-1]: hsv_colours[-1].add((175, 255, 100))
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
        print("bad red colours:", reds_that_could_be_oranges)


        # solve the cube
        solve = Cube.twophaseToNormal(sv.solve(Cube.magiccubeToTwoPhase(mc), 0, 0.1))
        print(solve)
        self.send_to_arduino(solve)

    def frame_update_loop(self, cam: Camera.Camera):
        frame = cam.get_frame()
        if not frame is None:
            # show colour info on camera frame
            if self.show_colour_info.get():
                median_hsv_colours, piece_colours, hidden_corners = self.analyse_image(cam, frame)
                frame = self.write_data_on_image(cam, frame, median_hsv_colours, piece_colours, hidden_corners)

            # display image in GUI
            img = Image.fromarray(frame)
            ctk_img = ctk.CTkImage(light_image=img, size=(int(img.width * self.camera_scale),
                                                          int(img.height * self.camera_scale)))
            cam.label.configure(image=ctk_img)
            cam.label.image = ctk_img
        else:
            print("Camera frame failed")

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

    def solve_cube(self):
        # return if ui is disabled
        if self.ui_disabled:
            return

        # get colour data from camera frames
        B_data, T_data = self.get_colour_data_from_cams()

        self.cube.set_cubestate(B_data[1], B_data[2], T_data[1], T_data[2])
        solve = self.cube.solve_cube()
        if solve:
            print("Solve:", solve)
            self.send_to_arduino(solve)

    def on_close(self):
        # release & delete cameras
        self.camB.release()
        self.camT.release()
        print("Cameras disconnected")
        # release & delete arduino cube
        self.cube.release()
        print("Arduino disconnected")
        # destroy GUI app
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()