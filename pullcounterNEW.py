from PIL import Image, ImageTk
import cv2
import pyautogui
import numpy as np
import time
import tkinter as tk
from tkinter import messagebox, filedialog
import threading
import wx

def on_closing():
    global pull_counter_active
    if messagebox.askokcancel("Quit", "Are you sure you want to quit?"):
        pull_counter_active = False
        root.destroy()

# Ref image handling
def select_reference_image():
    global beginning_pull
    file_path = filedialog.askopenfilename()
    beginning_pull = cv2.imread(file_path)
    ref_image_label.config(text=f"{file_path}")

# Output file handling
def select_output_file():
    global output_file_path
    output_file_path = filedialog.asksaveasfilename(defaultextension=".txt")
    output_file_label.config(text=f"{output_file_path}")

# Capture area handling
def select_capture_area():
    cx = cy = cw = ch = None
    class TransparentFrame(wx.Frame):
        def __init__(self):
            super(TransparentFrame, self).__init__(None, wx.ID_ANY, style=wx.FRAME_SHAPED)
            self.SetTransparent(150) 
            self.Maximize()

            self.start_pos = None
            self.end_pos = None
            self.rect_started = False

            self.Bind(wx.EVT_LEFT_DOWN, self.on_mouse_pressed)
            self.Bind(wx.EVT_LEFT_UP, self.on_mouse_released)
            self.Bind(wx.EVT_MOTION, self.on_mouse_dragged)
            self.Bind(wx.EVT_PAINT, self.on_paint)
            self.Bind(wx.EVT_KEY_DOWN, self.on_key_pressed)

        def on_mouse_pressed(self, event):
            self.start_pos = event.GetPosition()
            self.rect_started = True

        def on_mouse_released(self, event):
            self.rect_started = False
            if self.start_pos is not None and self.end_pos is not None:
                global cx, cy, cw, ch
                start_x, start_y = self.start_pos
                width = abs(self.end_pos.x - start_x)
                height = abs(self.end_pos.y - start_y)
                cx, cy, cw, ch = start_x, start_y, width, height
                capture_area_label.config(text=f"{cx}, {cy}, {cw}, {ch}")
                self.Close()

        def on_mouse_dragged(self, event):
            if event.Dragging() and event.LeftIsDown() and self.rect_started:
                self.end_pos = event.GetPosition()
                self.Refresh()

        def on_paint(self, event):
            if self.start_pos is not None and self.end_pos is not None:
                dc = wx.PaintDC(self)
                dc.SetPen(wx.Pen(wx.Colour(0, 255, 0), width=1, style=wx.PENSTYLE_SOLID))
                start_x, start_y = self.start_pos
                width = abs(self.end_pos.x - start_x)
                height = abs(self.end_pos.y - start_y)
                dc.DrawRectangle(start_x, start_y, width, height)
        
        def on_key_pressed(self, event):
            if event.GetKeyCode() == wx.WXK_ESCAPE:
                self.Close()

    class CaptureApp(wx.App):
        def OnInit(self):
            frame = TransparentFrame()
            frame.Show()
            return True

    capture_app = CaptureApp()
    capture_app.MainLoop()

# Initialize GUI
root = tk.Tk()
root.title("Two's Pull Counter")
root.configure(bg='#1d1d23')
root.iconbitmap(r"B:\twowtf32.ico")

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
window_width = int(screen_width * 0.3)
window_height = int(screen_height * 0.3)
root.geometry(f"{window_width}x{window_height}")

beginning_pull = None
output_file_path = "pull_count.txt"

pull_counter_active = False

def check_for_pull(image):
    global sim_value
    result = cv2.matchTemplate(image, beginning_pull, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    
    # Display the screenshot in a new window
    '''if max_val > sim_value: 
        display_screenshot(image)'''

    return max_val

def display_screenshot(image):
    screenshot_window = tk.Toplevel(root)
    screenshot_window.title("Screenshot Capture")

    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(image_rgb)
    img = ImageTk.PhotoImage(img)

    screenshot_label = tk.Label(screenshot_window, image=img)
    screenshot_label.image = img
    screenshot_label.pack()

def update_pull_count_file(pulls):
    with open(output_file_path, 'w') as file:
        file.write(f"Pulls: {pulls}")

button_color = 'SystemButtonFace'

def update_button_label():
    if beginning_pull is not None and output_file_path:
        if 'cx' in globals() and 'cy' in globals() and 'cw' in globals() and 'ch' in globals():
            if pull_counter_active:
                start_stop_button.config(text="Stop Counting", bg="#a13230")
            else:
                start_stop_button.config(text="Start Counting", bg="SystemButtonFace")
        else:
            start_stop_button.config(text="Start Counting", bg="SystemButtonFace")
            missing_requirements = ["Capture area not defined"]
            message = "\n".join(missing_requirements)
            messagebox.showwarning("Warning", f"Please fulfill the following requirements:\n\n{message}")
    else:
        start_stop_button.config(text="Start Counting", bg="SystemButtonFace")
        missing_requirements = []
        if beginning_pull is None:
            missing_requirements.append("Reference image not loaded")
        if not output_file_path:
            missing_requirements.append("Output file path not defined")
        message = "\n".join(missing_requirements)
        messagebox.showwarning("Warning", f"Please fulfill the following requirements:\n\n{message}")

def start_stop_counting():
    global pull_counter_active
    if beginning_pull is not None and output_file_path:
        if not pull_counter_active:
            if 'cx' in globals() and 'cy' in globals() and 'cw' in globals() and 'ch' in globals():
                pull_counter_active = True
                start_counting_thread = threading.Thread(target=count_pulls)
                start_counting_thread.start()
        else:
            pull_counter_active = False
    update_button_label()

def count_pulls():
    global pull_counter_active, pulls, sim_value
    pulls = 0
    update_button_label()

    while pull_counter_active:
        if beginning_pull is not None and output_file_path and 'cx' in globals() and 'cy' in globals() and 'cw' in globals() and 'ch' in globals():
            screenshot = pyautogui.screenshot(region=(cx, cy, cw, ch))
            frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

            sim_value = similarity_slider.get() / 100.0

            similarity = check_for_pull(frame)
            if similarity > sim_value:
                time.sleep(3)
                pulls += 1
                pulls_label.config(text=f"Pulls: {pulls}")
                update_pull_count_file(pulls)
            time.sleep(0.5)
        else:
            pull_counter_active = False


def reset_pull_count():
    global pulls
    if messagebox.askokcancel("Reset Pulls?", "Are you sure you want to reset your pulls?"):
        pulls_label.config(text=f"Pulls: 0")
        update_pull_count_file(0)

select_ref_image_button = tk.Button(root, text="Select Reference Image", command=select_reference_image)
select_ref_image_button.grid(row=0, column=0, pady=5, padx=10, sticky='w')

ref_image_label = tk.Label(root, text="Reference Image: Not Loaded", bg='#1d1d23', fg='white')
ref_image_label.grid(row=0, column=1, pady=5, padx=10, sticky='w')

select_output_file_button = tk.Button(root, text="Set Output File", command=select_output_file)
select_output_file_button.grid(row=1, column=0, pady=5, padx=10, sticky='w')

output_file_label = tk.Label(root, text="Output File: Not Set", bg='#1d1d23', fg='white')
output_file_label.grid(row=1, column=1, pady=5, padx=10, sticky='w')

select_capture_area_button = tk.Button(root, text="Select Capture Area", command=select_capture_area)
select_capture_area_button.grid(row=2, column=0, pady=5, padx=10, sticky='w')

capture_area_label = tk.Label(root, text="Capture Area: Not Defined", bg='#1d1d23', fg='white')
capture_area_label.grid(row=2, column=1, pady=5, padx=10, sticky='w')

similarity_slider = tk.Scale(root, from_=0, to=100, orient='horizontal', label='Similarity (%)', resolution='1')
similarity_slider.set(40)
similarity_slider.grid(row=3, column=0, pady=5, padx=10, sticky='w')

start_stop_button = tk.Button(root, text="Start", command=start_stop_counting, width=12, height=2, font=("Arial", 12))
start_stop_button.grid(row=4, column=0, pady=10, padx=10, sticky='nsew')

reset_pulls_button = tk.Button(root, text="Reset Pull Count", command=reset_pull_count)
reset_pulls_button.grid(row=5, column=0, pady=5, padx=10, sticky='nsew')

pulls_label = tk.Label(root, text="Pulls: 0", font=("Arial", 24))
pulls_label.grid(row=4, column=3, pady=20, padx=10, sticky='nsew')

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()