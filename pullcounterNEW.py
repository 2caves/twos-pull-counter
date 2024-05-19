from PIL import Image, ImageTk
import cv2
import pyautogui
import numpy as np
import time
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
import threading
import wx
import configparser
import os.path
import sys

pulls=0

def save_config():
    global pulls
    config = configparser.ConfigParser()
    config['DEFAULT'] = {
        'reference_image_path': ref_image_label.cget("text"),
        'output_file_path': output_file_path,
        'capture_area_coordinates': capture_area_label.cget("text"),
        'similarity percentage': similarity_slider.get(),
        'last_pull_count': pulls
    }
    try:
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save configuration: {str(e)}")

def load_config():
    global beginning_pull, cx, cy, cw, ch, custom_count, pulls
    config = configparser.ConfigParser()
    try:
        config.read('config.ini')
    except configparser.Error as e:
        messagebox.showerror("Error", f"Failed to load configuration: {str(e)}")
        return

    if 'DEFAULT' in config:
        ref_image_path = config['DEFAULT'].get('reference_image_path', '')
        if ref_image_path:
            beginning_pull = ref_image_path
            print('Ref image loaded from config')
            ref_image_label.config(text=ref_image_path)
        else:
            beginning_pull = None
            ref_image_label.config(text='Reference Image: Not Loaded')

        output_file_label.config(text=config['DEFAULT'].get('output_file_path', ''))
        capture_area_label.config(text=config['DEFAULT'].get('capture_area_coordinates', ''))
        capture_area_text = capture_area_label.cget("text")

        last_pull_count = config['DEFAULT'].get('last_pull_count', None)
        if last_pull_count is not None:
            try:
                pulls = int(last_pull_count)
            except ValueError:
                pulls = 0
            pulls_label.config(text="Pulls: " + config['DEFAULT'].get('last_pull_count', ''))
            custom_count = pulls
        else:
            pulls = 0
            custom_count = 0

        similarity_percentage = config['DEFAULT'].get('similarity percentage', '')
        if similarity_percentage:
            similarity_slider.set(int(similarity_percentage))
        print("Capture Area Text:", capture_area_text)
        try:
            cx, cy, cw, ch = map(int, capture_area_text.split(','))
            print("cx, cy, cw, ch:", cx, cy, cw, ch)
        except ValueError:
            print("Error parsing capture area coordinates")
    else:
        ref_image_label.config(text='')
        output_file_label.config(text='')
        capture_area_label.config(text='')
        similarity_slider.set(int(40))

# Ref image handling
def select_reference_image():
    global beginning_pull
    file_path = filedialog.askopenfilename()
    beginning_pull = file_path
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

# .ico relative path
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Initialize GUI
root = tk.Tk()
root.title("Two's Pull Counter")
root.configure(bg='#1d1d23')
icon_path=resource_path('twowtf32.ico')
root.iconbitmap(icon_path)

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
window_width = int(screen_width * 0.3)
window_height = int(screen_height * 0.3)
root.geometry(f"{window_width}x{window_height}")

beginning_pull = None
output_file_path = "pull_count.txt"
pull_counter_active = False

def scale_reference_image(reference_image, cx, cy, cw, ch):
    capture_area_width = cw
    capture_area_height = ch

    reference_image_width = reference_image.shape[1]
    reference_image_height = reference_image.shape[0]

    # Check if the reference image dimensions are smaller than the capture area
    if reference_image_width > capture_area_width or reference_image_height > capture_area_height:
        scale_x = capture_area_width / reference_image_width
        scale_y = capture_area_height / reference_image_height

        scale_factor = min(scale_x, scale_y)

        # Resize
        scaled_reference_image = cv2.resize(reference_image, None, fx=scale_factor, fy=scale_factor)
        return scaled_reference_image
    else:
        return reference_image

def check_for_pull(image):
    global sim_value, beginning_pull, pull_counter_active, scaled_reference_image
    if beginning_pull is None:
        messagebox.showwarning("Warning", "Reference image not loaded")
        pull_counter_active = False
        update_button_label()
        return 0
    else:
        try:
            reference_image = cv2.imread(beginning_pull)
            if reference_image is None:
                messagebox.showwarning("Warning", "Failed to load reference image")
                pull_counter_active = False
                update_button_label()
                return 0
            
            scaled_reference_image = scale_reference_image(reference_image, cx, cy, cw, ch)
            
            print(f"cx,cy,cw,ch at matching: {cx,cy,cw,ch}")
            print(f"image shape:{image.shape}")
            print(f"reference image shape:{scaled_reference_image.shape}")
            
            result = cv2.matchTemplate(image, scaled_reference_image, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            return max_val
        except Exception as e:
            messagebox.showwarning("Warning", f"Error loading reference image: {str(e)}")
            pull_counter_active = False
            update_button_label()
            return 0
        
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

def set_custom_pull_count():
    global pulls, custom_count
    custom_count = simpledialog.askinteger("Set Pull Count", "Enter the number of pulls:", minvalue=0)
    if custom_count is not None:
        pulls = custom_count
        pulls_label.config(text=f"Pulls: {pulls}")
        update_pull_count_file(pulls)

def start_stop_counting():
    global pull_counter_active, pulls
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
    global pull_counter_active, pulls, sim_value, custom_count
    pulls = 0
    update_button_label()

    while pull_counter_active:
        if not os.path.exists(beginning_pull):
            pull_counter_active = False
            messagebox.showwarning("Warning", f"Please ensure reference image file path exists")
        if beginning_pull is not None and output_file_path and 'cx' in globals() and 'cy' in globals() and 'cw' in globals() and 'ch' in globals():
            screenshot = pyautogui.screenshot(region=(cx, cy, cw, ch))
            frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

            sim_value = similarity_slider.get() / 100.0

            similarity = check_for_pull(frame)
            if similarity > sim_value:
                time.sleep(3)
                pulls = custom_count
                pulls += 1
                custom_count += 1
                pulls_label.config(text=f"Pulls: {pulls}")
                update_pull_count_file(pulls)
            time.sleep(1)
        else:
            pull_counter_active = False

def reset_pull_count():
    global pulls, custom_count
    if messagebox.askokcancel("Reset Pulls?", "Are you sure you want to reset your pulls?"):
        pulls_label.config(text=f"Pulls: 0")
        custom_count = 0
        update_pull_count_file(0)


def on_closing():
    global pull_counter_active, pulls
    if messagebox.askokcancel("Quit", "Are you sure you want to quit?"):
        pull_counter_active = False
        save_config()
        root.destroy()

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
if similarity_slider is None:
    similarity_slider.set(40)
similarity_slider.grid(row=3, column=0, pady=5, padx=10, sticky='w')

start_stop_button = tk.Button(root, text="Start", command=start_stop_counting, width=12, height=2, font=("Arial", 12))
start_stop_button.grid(row=4, column=0, pady=10, padx=10, sticky='nsew')

reset_pulls_button = tk.Button(root, text="Reset Pull Count", command=reset_pull_count)
reset_pulls_button.grid(row=5, column=0, pady=5, padx=10, sticky='nsew')

set_custom_pull_button = tk.Button(root, text="Set Custom Pull Count", command=set_custom_pull_count)
set_custom_pull_button.grid(row=5, column=3, padx=10, sticky='nsew')

pulls_label = tk.Label(root, text="Pulls: 0", font=("Arial", 24))
pulls_label.grid(row=4, column=3, pady=20, padx=10, sticky='nsew')

load_config()

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()