import tkinter as tk
from tkinter import messagebox, filedialog, Menu, Toplevel, ttk
import json
import zipfile
import os
import py7zr
import shutil

# Function to handle the compressed file selection
def select_file(event=None):
    file_path = filedialog.askopenfilename(
        title="Select a compressed file",
        filetypes=[("Compressed files", "*.zip *.7z")]
    )
    if file_path:
        file_label.config(text=f"Selected file: {file_path}")
    else:
        file_label.config(text="No file selected")

# Function to handle folder selection in the preferences window
def select_folder(folder_num, folder_labels):
    folder_path = filedialog.askdirectory(
        title=f"Select {folder_names[folder_num-1]}"
    )
    if folder_path:
        folder_labels[folder_num-1].config(text=f"{folder_names[folder_num-1]}: {folder_path}")
    else:
        folder_labels[folder_num-1].config(text=f"{folder_names[folder_num-1]}: Not selected")

# Function to open the preferences window
def open_preferences():
    pref_window = Toplevel(root)
    pref_window.title("Preferences")
    pref_window.geometry("800x600")  # Set the dimensions to 800x600

    # Calculate center coordinates
    window_width = 800
    window_height = 600
    screen_width = pref_window.winfo_screenwidth()
    screen_height = pref_window.winfo_screenheight()
    x_cordinate = int((screen_width/2) - (window_width/2))
    y_cordinate = int((screen_height/2) - (window_height/2))
    pref_window.geometry("{}x{}+{}+{}".format(window_width, window_height, x_cordinate, y_cordinate))

    # Set icon for preferences window
    pref_window.iconbitmap('img/fruitpacker.ico')

    # Create a canvas and scrollbar
    canvas = tk.Canvas(pref_window)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar = ttk.Scrollbar(pref_window, orient=tk.VERTICAL, command=canvas.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    # Create a frame inside the canvas
    scrollable_frame = tk.Frame(canvas)
    canvas.create_window((0, 0), window=scrollable_frame, anchor=tk.NW)

    # Add widgets to the scrollable frame
    folder_labels = []

    for i in range(16):
        folder_button = tk.Button(scrollable_frame, text=f"Select {folder_names[i]}", command=lambda i=i: select_folder(i+1, folder_labels))
        folder_button.grid(row=i, column=0, pady=5)
        
        folder_label = tk.Label(scrollable_frame, text=f"{folder_names[i]}: Not selected")
        folder_label.grid(row=i, column=1, pady=5)
        folder_labels.append(folder_label)

    # Load saved preferences if available
    load_preferences(folder_labels)

    # Save preferences button
    save_button = tk.Button(pref_window, text="Save Preferences", command=lambda: save_preferences(folder_labels))
    save_button.pack(pady=10)

# Function to save preferences to a file
def save_preferences(folder_labels):
    preferences = {}
    for i, label in enumerate(folder_labels):
        folder_path = label.cget("text").split(": ", 1)[1]
        preferences[folder_names[i]] = folder_path
    
    with open("preferences.json", "w") as pref_file:
        json.dump(preferences, pref_file)
    messagebox.showinfo("Preferences", "Preferences saved successfully!")

# Function to load preferences from a file
def load_preferences(folder_labels):
    try:
        with open("preferences.json", "r") as pref_file:
            preferences = json.load(pref_file)
        for i, label in enumerate(folder_labels):
            folder_path = preferences.get(folder_names[i], "Not selected")
            label.config(text=f"{folder_names[i]}: {folder_path}")
    except FileNotFoundError:
        pass

# Function to extract and sort the compressed file
def extract_and_sort():
    file_path = file_label.cget("text").split(": ", 1)[1]
    if file_path == "No file selected":
        messagebox.showwarning("Warning", "No compressed file selected!")
        return

    try:
        with open("preferences.json", "r") as pref_file:
            preferences = json.load(pref_file)
    except FileNotFoundError:
        messagebox.showwarning("Warning", "No preferences found! Please set your folder preferences.")
        return

    # Ensure that required folders are selected
    folder_1 = preferences.get(folder_names[0], "")
    folder_2 = preferences.get(folder_names[1], "")
    if not folder_1 or not folder_2:
        messagebox.showwarning("Warning", f"Please select folders for {folder_names[0]} and {folder_names[1]} files.")
        return

    # Open a new window for progress bar and file list
    progress_window = Toplevel(root)
    progress_window.title("Extraction Progress")
    progress_window.geometry("1000x500")

    # Set icon for progress window
    progress_window.iconbitmap('img/fruitpacker.ico')

    # Create a progress bar
    progress_bar = ttk.Progressbar(progress_window, orient='horizontal', length=800, mode='determinate')
    progress_bar.pack(pady=10)

    # Create a listbox to display files being extracted
    file_listbox = tk.Listbox(progress_window, width=100, height=15)
    file_listbox.pack(pady=10)

    # Create a list to store files that couldn't be moved
    unmoved_files = []

    def handle_file(file_info_or_name, extract_func, total_files, i):
        filename = file_info_or_name.filename if isinstance(file_info_or_name, zipfile.ZipInfo) else file_info_or_name
        target_folder = determine_target_folder(filename, preferences)
        if target_folder:
            dest_path = os.path.join(target_folder, filename)
            if os.path.exists(dest_path):
                messagebox.showwarning("Duplicate File", f"Duplicate file found: {filename}")
            else:
                extract_func(file_info_or_name, target_folder)
        else:
            unmoved_files.append(filename)
        progress_bar['value'] = (i + 1) / total_files * 100
        file_listbox.insert(tk.END, f"Extracting and moving: {filename}")
        progress_window.update_idletasks()

    if file_path.endswith('.zip'):
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            total_files = len(zip_ref.infolist())
            for i, file_info in enumerate(zip_ref.infolist()):
                handle_file(file_info, lambda f, d: zip_ref.extract(f, d), total_files, i)
    elif file_path.endswith('.7z'):
        with py7zr.SevenZipFile(file_path, mode='r') as archive:
            all_files = archive.getnames()
            total_files = len(all_files)
            for i, file in enumerate(all_files):
                handle_file(file, lambda f, d: archive.extract(d, targets=[f]), total_files, i)

    progress_bar.pack_forget()

    # Handle unmoved files
    if unmoved_files:
        handle_unmoved_files(unmoved_files, preferences)

    messagebox.showinfo("Success", "Files have been extracted and sorted successfully!")

def handle_unmoved_files(unmoved_files, preferences):
    unmoved_window = Toplevel(root)
    unmoved_window.title("Unmoved Files")
    unmoved_window.geometry("800x400")

    # Set icon for unmoved files window
    unmoved_window.iconbitmap('img/fruitpacker.ico')

    listbox = tk.Listbox(unmoved_window, width=100, height=15)
    listbox.pack(pady=10)

    for file in unmoved_files:
        listbox.insert(tk.END, file)

    def select_folders_for_unmoved_files():
        selected_folders = {}
        for file in unmoved_files:
            folder_path = filedialog.askdirectory(title=f"Select folder for {file}")
            if folder_path:
                selected_folders[file] = folder_path

        for file, folder in selected_folders.items():
            shutil.move(file, folder)

        unmoved_window.destroy()

    select_button = tk.Button(unmoved_window, text="Select Folders for Unmoved Files", command=select_folders_for_unmoved_files)
    select_button.pack(pady=10)

# Function to determine the target folder based on filename
def determine_target_folder(filename, preferences):
    for i, folder_name in enumerate(folder_names):
        if folder_name.split(" ")[0].lower() in filename.lower():
            return preferences.get(folder_name, None)
    return None

# List of folder names
folder_names = [
    "808s Folder",
    "Hi-Hats Folder",
    "Open Hats Folder",
    "Claps Folder",
    "Vox Folder",
    "SFX Folder",
    "Samples Folder",
    "Kicks Folder",
    "Snares Folder",
    "Risers Folder",
    "Percs Folder",
    "One Shots Folder",
    "Fills Folder",
    "Crashes Folder",
    "Rim Shots Folder",
    "Chants Folder"
]

# Create the main window
root = tk.Tk()
root.title("zekkie's Fruitpacker")

# Set the dimensions and position of the main window
window_width = 1000
window_height = 650
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x_cordinate = int((screen_width/2) - (window_width/2))
y_cordinate = int((screen_height/2) - (window_height/2))
root.geometry("{}x{}+{}+{}".format(window_width, window_height, x_cordinate, y_cordinate))

# Set the icon for the main window and taskbar
root.iconbitmap('img/fruitpacker.ico')

# Create a menu bar
menu_bar = Menu(root)
root.config(menu=menu_bar)

# Create a File menu with Open and Exit options
file_menu = Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Open", command=select_file)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=root.quit)

# Create a Settings menu with Preferences option
settings_menu = Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Settings", menu=settings_menu)
settings_menu.add_command(label="Preferences", command=open_preferences)

# Create a label for displaying selected file
file_label = tk.Label(root, text="No file selected", pady=10)
file_label.pack()

# Create a button to trigger file selection
select_button = tk.Button(root, text="Select Compressed File", command=select_file)
select_button.pack()

# Create a button to trigger extraction and sorting
extract_button = tk.Button(root, text="Extract and Sort", command=extract_and_sort)
extract_button.pack(pady=10)

# Run the Tkinter main loop
root.mainloop()
