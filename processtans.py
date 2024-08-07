import tkinter as tk
from tkinter import ttk, messagebox
import psutil
import json
import os
import subprocess
import PIL
from PIL import Image, ImageTk

# Paths
JSON_FOLDER = 'process'
IMG_FOLDER = os.path.join(JSON_FOLDER, 'imgs')
DEFAULT_JSON_PATH = os.path.join(JSON_FOLDER, 'default.json')
DEFAULT_ICON_PATH = os.path.join(IMG_FOLDER, 'default.png')
APP_ICON_PATH = os.path.join(IMG_FOLDER, '!APP.png')
os.makedirs(JSON_FOLDER, exist_ok=True)
os.makedirs(IMG_FOLDER, exist_ok=True)

# Functions
def get_processes():
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'status']):
        try:
            processes.append(proc.info)
        except psutil.NoSuchProcess:
            pass
    return processes

def get_json_for_process(process_name):
    json_path = os.path.join(JSON_FOLDER, f"{process_name}.json")
    if os.path.exists(json_path):
        with open(json_path, 'r') as file:
            return json.load(file)
    else:
        with open(DEFAULT_JSON_PATH, 'r') as file:
            return json.load(file)

def get_process_image(process_name, json_data):
    icon_path = os.path.join(IMG_FOLDER, f"{process_name}.png")
    
    # Check if the json specifies a custom image and if it exists
    custom_image_path = os.path.join(IMG_FOLDER, json_data['image'])
    if json_data['image'] != 'default.png' and os.path.exists(custom_image_path):
        return custom_image_path

    # If custom image does not exist, check if generated icon exists
    if not os.path.exists(icon_path):
        if json_data['image'] == 'default.png':
            # Generate the combined image
            app_icon = Image.open(APP_ICON_PATH).resize((64, 64), PIL.Image.Resampling.LANCZOS)
            default_image = Image.open(DEFAULT_ICON_PATH)
            combined_image = default_image.copy()
            combined_image.paste(app_icon, (int((default_image.width - 70) / 2), int((default_image.height + 90) / 2)), app_icon)
            combined_image.save(icon_path)
        else:
            # If a custom image path is provided but not found, fall back to default image
            icon_path = DEFAULT_ICON_PATH
    
    return icon_path


def kill_process(pid):
    psutil.Process(pid).kill()

def suspend_process(pid):
    psutil.Process(pid).suspend()

def open_process_folder(process_name):
    try:
        subprocess.Popen(f'explorer /select,{process_name}')
    except Exception as e:
        messagebox.showerror("Error", f"Could not open folder: {e}")

def show_process_window(pid):
    try:
        process = psutil.Process(pid)
        if process.status() == psutil.STATUS_RUNNING:
            subprocess.Popen(f'tasklist /fi "PID eq {pid}"', shell=True)
    except Exception as e:
        messagebox.showerror("Error", f"Could not show process window: {e}")


# Main Application Class
class ProcessManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Process Manager")
        self.geometry("300x500")
        self.processes = get_processes()

        # Main window widgets
        self.label = tk.Label(self, text="Select your process.")
        self.label.pack(pady=10)

        self.process_listbox = tk.Listbox(self)
        self.process_listbox.pack(expand=True, fill=tk.BOTH)
        self.process_listbox.bind('<<ListboxSelect>>', self.on_process_select)

        self.scrollbar = tk.Scrollbar(self.process_listbox)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.process_listbox.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.process_listbox.yview)
        self.refresh_button = tk.Button(self, text="Refresh", command=self.refresh_process_list)
        self.refresh_button.pack(pady=10)
        self.populate_process_list()


    def refresh_process_list(self):
        self.process_listbox.delete(0, tk.END)
        self.processes = get_processes()
        self.populate_process_list()


    def populate_process_list(self):
        for proc in self.processes:
            self.process_listbox.insert(tk.END, proc['name'])

    def on_process_select(self, event):
        selected_index = self.process_listbox.curselection()
        if selected_index:
            process_name = self.process_listbox.get(selected_index)
            process_info = next((proc for proc in self.processes if proc['name'] == process_name), None)
            if process_info:
                ProcessDetailWindow(self, process_info)

class ProcessDetailWindow(tk.Toplevel):
    def __init__(self, parent, process_info):
        super().__init__(parent)
        self.title(process_info['name'])
        self.geometry("300x500")
        self.resizable(False, False)
        self.process_info = process_info
        self.json_data = get_json_for_process(process_info['name'])
        self.icon_path = get_process_image(process_info['name'], self.json_data)

        self.create_widgets()

    def create_widgets(self):
        header = tk.Label(self, text=self.json_data['name'] if self.json_data['name'] != 'Unnamed Process-tan' else self.process_info['name'])
        header.pack(pady=10)

        subtext = tk.Label(self, text=self.json_data['description'] if self.json_data['description'] != 'No description available.' else self.get_process_description())
        subtext.pack(pady=5)

        self.image_label = tk.Label(self)
        self.image_label.pack(pady=10)
        self.load_image()

        self.status_label = tk.Label(self, text=self.get_process_status())
        self.status_label.pack(pady=10)

        button_frame = tk.Frame(self)
        button_frame.pack(pady=10)

        kill_button = tk.Button(button_frame, text="Kill", command=self.kill_process)
        kill_button.pack(side=tk.LEFT, padx=5)

        suspend_button = tk.Button(button_frame, text="Suspend", command=self.suspend_process)
        suspend_button.pack(side=tk.LEFT, padx=5)

        open_folder_button = tk.Button(button_frame, text="Open Folder", command=self.open_folder)
        open_folder_button.pack(side=tk.LEFT, padx=5)

        show_button = tk.Button(button_frame, text="Show", command=self.show_process_window)
        show_button.pack(side=tk.LEFT, padx=5)

        priority_button = tk.Button(button_frame, text=f"Priority: {self.get_process_priority()}", state=tk.DISABLED)
        priority_button.pack(side=tk.LEFT, padx=5)

    def load_image(self):
        img = Image.open(self.icon_path)
        img = ImageTk.PhotoImage(img)
        self.image_label.configure(image=img)
        self.image_label.image = img

    def get_process_description(self):
        try:
            proc = psutil.Process(self.process_info['pid'])
            return proc.exe()
        except Exception as e:
            return "No description available."

    def get_process_status(self):
        status = self.process_info['status']
        if status == psutil.STATUS_RUNNING:
            return f"{self.process_info['name']} is idle."
        elif status == psutil.STATUS_STOPPED:
            return f"{self.process_info['name']} is unresponsive at the moment."
        elif status == psutil.STATUS_SUSPENDED:
            return f"Something happened to {self.process_info['name']}!"
        else:
            return f"{self.process_info['name']} status: {status}"

    def get_process_priority(self):
        try:
            proc = psutil.Process(self.process_info['pid'])
            return proc.nice()
        except Exception as e:
            return "Unknown"

    def kill_process(self):
        try:
            kill_process(self.process_info['pid'])
            self.status_label.config(text=f"{os.getlogin()} killed {self.process_info['name']}.")
            self.disable_buttons()
            self.image_label.pack_forget()
        except Exception as e:
            messagebox.showerror("Error", f"Could not kill process: {e}")

    def suspend_process(self):
        try:
            suspend_process(self.process_info['pid'])
            self.status_label.config(text=f"{self.process_info['name']} is suspended.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not suspend process: {e}")

    def open_folder(self):
        try:
            open_process_folder(self.process_info['name'])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder: {e}")

    def show_process_window(self):
        try:
            show_process_window(self.process_info['pid'])
        except Exception as e:
            messagebox.showerror("Error", f"Could not show process window: {e}")

    def disable_buttons(self):
        for widget in self.winfo_children():
            if isinstance(widget, tk.Button) and widget['state'] != tk.DISABLED:
                widget['state'] = tk.DISABLED

if __name__ == "__main__":
    # Create default JSON if not exists
    if not os.path.exists(DEFAULT_JSON_PATH):
        default_data = {
            "name": "Unnamed Process",
            "description": "No description available.",
            "image": "default.png"
        }
        with open(DEFAULT_JSON_PATH, 'w') as file:
            json.dump(default_data, file, indent=4)

    app = ProcessManagerApp()
    app.mainloop()
