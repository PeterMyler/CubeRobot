import cv2
import customtkinter as ctk
from PIL import Image, ImageTk

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.geometry("800x800")
        # self.resizable(False, False)

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


        # Buttons
        self.controls_frame = ctk.CTkFrame(self)
        self.controls_frame.pack(side="left", fill="both", expand=True)
        self.inner_frame = ctk.CTkFrame(self.controls_frame)
        self.inner_frame.place(relx=0.5, rely=0, anchor="n")
        self.button = ctk.CTkButton(self.inner_frame, text="Capture1", command=self.capture, width=300)
        self.button.pack(pady=10, padx=10)
        self.button1 = ctk.CTkButton(self.inner_frame, text="Capture2", command=self.capture)
        self.button1.pack(pady=10, padx=10)
        self.button2 = ctk.CTkButton(self.inner_frame, text="Capture3", command=self.capture)
        self.button2.pack(pady=10, padx=10)

        # Open camera
        self.capB = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        # apply camera settings
        self.capB.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # 640x480
        self.capB.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.capB.set(cv2.CAP_PROP_EXPOSURE, -1)
        self.capB.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        # launch camera
        self.update_frame()



    def update_frame(self):
        ret, frame = self.capB.read()
        frame = cv2.rotate(frame, cv2.ROTATE_180)  # flip image upsidedown

        if ret and frame is not None:
            # Convert BGR → RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Convert to PIL image
            img = Image.fromarray(frame)

            # Convert to Tkinter image
            scale = 0.7
            ctk_img = ctk.CTkImage(light_image=img, size=(int(img.width * scale), int(img.height * scale)))
            self.top_camera_label.configure(image=ctk_img)
            self.top_camera_label.image = ctk_img

            ctk_img2 = ctk.CTkImage(light_image=img, size=(int(img.width * scale), int(img.height * scale)))
            self.bottom_camera_label.configure(image=ctk_img2)
            self.bottom_camera_label.image = ctk_img2



        else:
            print("Camera frame failed")

        # Call again after 10ms
        self.after(10, self.update_frame)

    def on_close(self):
        self.capB.release()
        # self.capT.release()
        self.destroy()

    def capture(self):
        print("Button")


app = App()
app.protocol("WM_DELETE_WINDOW", app.on_close)
app.mainloop()