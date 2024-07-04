import tkinter as tk
from tkinter import messagebox, filedialog, Menu, Toplevel, ttk, simpledialog
import json
import os
import shutil
import py7zr
import zipfile
import requests
import webbrowser  # Added for hyperlink functionality
import platform

# Global variable for language
current_language = "English"

# Function to switch language to French
def switch_to_french():
    global current_language
    current_language = "French"
    update_translations()

# Function to switch language to English
def switch_to_english():
    global current_language
    current_language = "English"
    update_translations()

# Function to get the translated text based on current language
def get_translation(label):
    if current_language == "French":
        translation = get_translation_from_file(label)
        if translation:
            return translation
    # Default to English label if not in French or translation not found
    return label

# Function to retrieve translation from fr.txt
def get_translation_from_file(label):
    translation_file = "lang/fr.txt"
    if os.path.exists(translation_file):
        with open(translation_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    parts = line.split(" = ")
                    if len(parts) == 2 and parts[0].strip('"') == label.strip('"'):
                        return parts[1].strip().strip('"')
    return None

# Example usage in your application
def main_application_logic():
    # Example usage of get_translation
    label = "Select Compressed File"
    translated_label = get_translation(label)
    select_button = tk.Button(root, text=translated_label, command=select_file)
    select_button.pack()

# Example function for reading fr.txt and updating translations
def update_translations():
    global translations
    translations = {}
    translation_file = "lang/fr.txt"
    if os.path.exists(translation_file):
        with open(translation_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    parts = line.split(" = ")
                    if len(parts) == 2:
                        label = parts[0].strip('"')
                        translation = parts[1].strip().strip('"')
                        translations[label] = translation

# Call update_translations when switching to French
switch_to_french()
update_translations()

# Call switch_to_english when switching to English
switch_to_english()

# Global variable to track the preferences window
pref_window = None
language_var = None  # Define language_var as a global variable
dark_mode = False  # Initialize dark mode variable

# Function to check for updates
def check_for_updates():
    repo_owner = "your-github-username"
    repo_name = "your-repo-name"
    api_url = f"https://api.github.com/repos/zekticezy/fruitpacker/releases/latest"

    try:
        response = requests.get(api_url)
        response.raise_for_status()
        latest_release = response.json()
        latest_version = latest_release['tag_name']
        
        with open("current_version.txt", "r") as version_file:
            current_version = version_file.read().strip()
        
        if latest_version != current_version:
            update_prompt = messagebox.askyesno("Update Available", f"A new version ({latest_version}) is available. Would you like to update?")
            if update_prompt:
                update_url = latest_release['assets'][0]['browser_download_url']
                download_and_install_update(update_url, latest_version)
    except Exception as e:
        messagebox.showerror("Update Check Failed", f"Failed to check for updates: {e}")

def download_and_install_update(url, version):
    response = requests.get(url)
    file_name = url.split("/")[-1]
    with open(file_name, "wb") as file:
        file.write(response.content)
    
    # Assuming the update is a zip file, extract it and replace current files
    with zipfile.ZipFile(file_name, 'r') as zip_ref:
        zip_ref.extractall()
    
    with open("current_version.txt", "w") as version_file:
        version_file.write(version)
    
    messagebox.showinfo("Update Complete", "The application has been updated. Please restart the application to apply the changes.")

# Function to handle the compressed file selection
def select_file():
    file_path = filedialog.askopenfilename(
        title="Select a compressed file",
        filetypes=[("Compressed files", "*.zip *.7z")]
    )
    if file_path:
        file_label.config(text=f"Selected file: {file_path}")
    else:
        file_label.config(text="No file selected")

# Function to open the preferences window
def open_preferences():
    global pref_window, language_var, dark_mode
    
    if pref_window and pref_window.winfo_exists():
        pref_window.lift()
        return
    
    pref_window = Toplevel(root)
    pref_window.title("Preferences")
    pref_window.geometry("800x600")
    pref_window.iconbitmap('img/fruitpacker.ico')

    # Center the preferences window
    pref_window.update_idletasks()
    width = pref_window.winfo_width()
    height = pref_window.winfo_height()
    x = (pref_window.winfo_screenwidth() // 2) - (width // 2)
    y = (pref_window.winfo_screenheight() // 2) - (height // 2)
    pref_window.geometry('{}x{}+{}+{}'.format(width, height, x, y))

    # Create a notebook widget (tabs)
    notebook = ttk.Notebook(pref_window)
    notebook.pack(fill=tk.BOTH, expand=True)

    # Folders tab
    folders_frame = tk.Frame(notebook)
    notebook.add(folders_frame, text="Folders")

    # Create a canvas and scrollbar for folders frame
    canvas_folders = tk.Canvas(folders_frame)
    canvas_folders.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar_folders = ttk.Scrollbar(folders_frame, orient=tk.VERTICAL, command=canvas_folders.yview)
    scrollbar_folders.pack(side=tk.RIGHT, fill=tk.Y)

    canvas_folders.configure(yscrollcommand=scrollbar_folders.set)
    canvas_folders.bind('<Configure>', lambda e: canvas_folders.configure(scrollregion=canvas_folders.bbox("all")))

    # Create a frame inside the canvas for folders
    scrollable_frame_folders = tk.Frame(canvas_folders)
    canvas_folders.create_window((0, 0), window=scrollable_frame_folders, anchor=tk.NW)

    # Add widgets to the scrollable frame for folders
    folder_labels = []

    for i, folder_name in enumerate(folder_names):
        folder_button = tk.Button(scrollable_frame_folders, text=f"Select {folder_name}", command=lambda i=i: select_folder(i+1, folder_labels))
        folder_button.grid(row=i, column=0, pady=5)
        
        folder_label = tk.Label(scrollable_frame_folders, text=f"{folder_name}: Not selected")
        folder_label.grid(row=i, column=1, pady=5)
        folder_labels.append(folder_label)

    # Load saved preferences if available
    load_preferences(folder_labels)

    # Add custom folder button
    add_custom_button = tk.Button(folders_frame, text="Add Custom Folder", command=lambda: add_custom_folder(pref_window, scrollable_frame_folders, folder_labels))
    add_custom_button.pack(pady=10)

    # Save preferences button
    save_button = tk.Button(folders_frame, text="Save Preferences", command=lambda: save_preferences(folder_labels))
    save_button.pack(pady=10)

    # Appearance tab
    appearance_frame = tk.Frame(notebook)
    notebook.add(appearance_frame, text="Appearance")

    global dark_mode_checkbox
    dark_mode_checkbox = tk.Checkbutton(appearance_frame, text="Dark Mode: Off", command=toggle_dark_mode)
    dark_mode_checkbox.pack(pady=10)

    sync_with_os_theme()  # Sync dark mode with OS theme initially

    # Language tab
    language_frame = tk.Frame(notebook)
    notebook.add(language_frame, text="Language")

    # Initialize language_var as a global variable
    global language_var
    language_var = tk.StringVar(language_frame)

    language_label = tk.Label(language_frame, text="Select Language:")
    language_label.pack(pady=10)

    language_dropdown = ttk.OptionMenu(language_frame, language_var, "", "English", "French")
    language_dropdown.pack(pady=10)

    # Link to translation portal
    translation_link = tk.Label(language_frame, text="Contribute your translations!", fg="blue", cursor="hand2")
    translation_link.pack(pady=10)
    translation_link.bind("<Button-1>", lambda e: webbrowser.open("https://your-translation-portal.com"))

    # Bindings
    pref_window.protocol("WM_DELETE_WINDOW", lambda: on_close_pref_window(pref_window))

# Function to handle closing of preferences window
def on_close_pref_window(window):
    if messagebox.askokcancel("Close Preferences", "Are you sure you want to close the preferences?"):
        window.destroy()

# Function to select a folder
def select_folder(index, folder_labels):
    folder_path = filedialog.askdirectory(title=f"Select Folder {index}")
    if folder_path:
        folder_labels[index-1].config(text=f"Folder {index}: {folder_path}")
    else:
        folder_labels[index-1].config(text=f"Folder {index}: Not selected")

# Function to add a custom folder
def add_custom_folder(pref_window, scrollable_frame, folder_labels):
    custom_label = simple_dialog(pref_window, "Custom Folder Label", "Enter a label for your custom folder:")
    if not custom_label:
        return

    tags = simple_dialog(pref_window, "File Tags", "Enter tags for files (comma-separated):")
    if not tags:
        return

    folder_path = filedialog.askdirectory(title=f"Select {custom_label}")
    if not folder_path:
        return

    # Update UI
    custom_label_text = f"{custom_label}: {folder_path} (Tags: {tags})"
    custom_label_widget = tk.Label(scrollable_frame, text=custom_label_text)
    custom_label_widget.grid(row=len(folder_labels), column=1, pady=5)
    folder_labels.append(custom_label_widget)

    # Save custom folder to preferences with tags
    save_preferences(folder_labels)

def simple_dialog(parent, title, prompt):
    response = simpledialog.askstring(title, prompt, parent=parent)
    return response

def save_preferences(folder_labels):
    preferences = {
        "language": language_var.get(),
        "dark_mode": dark_mode
    }
    
    for i, label in enumerate(folder_labels):
        label_text = label.cget("text")
        folder_name = label_text.split(": ", 1)[0]
        folder_path = label_text.split(": ", 1)[1].split(" (Tags: ")[0]
        preferences[folder_name] = {"path": folder_path, "tags": []}
        
        # Extract tags if available
        if " (Tags: " in label_text:
            tags = label_text.split(" (Tags: ")[1][:-1].split(", ")
            preferences[folder_name]["tags"] = tags
    
    with open("preferences.json", "w") as pref_file:
        json.dump(preferences, pref_file, indent=4)
    
    messagebox.showinfo("Preferences", "Preferences saved successfully!")

def load_preferences(folder_labels):
    try:
        with open("preferences.json", "r") as pref_file:
            preferences = json.load(pref_file)
            
            # Load language preference
            if "language" in preferences:
                language_var.set(preferences["language"])  # Set language_var
                
            # Load dark mode preference
            if "dark_mode" in preferences:
                global dark_mode
                dark_mode = preferences["dark_mode"]
                update_dark_mode_checkbox()

            # Load folders and appearance preferences (existing implementation)

    except FileNotFoundError:
        pass

def toggle_dark_mode():
    global dark_mode
    dark_mode = not dark_mode
    update_dark_mode_checkbox()
    # You can add more code here to update your application's appearance based on dark mode status

def update_dark_mode_checkbox():
    if dark_mode:
        dark_mode_checkbox.config(text="Dark Mode: On")
    else:
        dark_mode_checkbox.config(text="Dark Mode: Off")

def sync_with_os_theme():
    global dark_mode
    if platform.system() == "Darwin":  # macOS
        dark_mode = False  # Disable dark mode on macOS for now
    elif platform.system() == "Windows":
        dark_mode = True  # Enable dark mode on Windows

    update_dark_mode_checkbox()

def extract_and_sort():
    file_path = file_label.cget("text").split(": ", 1)[1]
    if file_path == "No file selected":
        messagebox.showwarning("Warning", "No compressed file selected!")
        return

    try:
        with open("preferences.json", "r") as pref_file:
            preferences = json.load(pref_file)
    except FileNotFoundError:
        messagebox.showwarning("Warning", "Please set preferences before extraction.")
        return

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

    progress_window = Toplevel(root)
    progress_window.title("Extraction Progress")
    progress_window.geometry("1000x500")
    progress_window.iconbitmap('img/fruitpacker.ico')

    progress_bar = ttk.Progressbar(progress_window, orient='horizontal', length=800, mode='determinate')
    progress_bar.pack(pady=10)

    file_listbox = tk.Listbox(progress_window, width=100, height=15)
    file_listbox.pack(pady=10)

    unmoved_files = []

    def handle_unmoved_files(unmoved_files, preferences):
        unmoved_window = Toplevel(root)
        unmoved_window.title("Unmoved Files")
        unmoved_window.geometry("800x400")
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

    def determine_target_folder(filename, preferences):
        for i, folder_name in enumerate(folder_names):
            if folder_name.split(" ")[0].lower() in filename.lower():
                return preferences.get(folder_name, None)
        return None

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
                handle_file(file, lambda f, d: archive.extract(f, d), total_files, i)

    progress_bar.pack_forget()

    if unmoved_files:
        handle_unmoved_files(unmoved_files, preferences)

    messagebox.showinfo("Success", "Files have been extracted and sorted successfully!")
    
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
file_menu.add_command(label="Open", command=select_file, accelerator="Ctrl+O")
file_menu.add_separator()
file_menu.add_command(label="Exit", command=root.quit)

# Create a Settings menu with Preferences option
settings_menu = Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Settings", menu=settings_menu)
settings_menu.add_command(label="Preferences", command=open_preferences, accelerator="Ctrl+P")

# Create a label for displaying selected file
file_label = tk.Label(root, text="No file selected", pady=10)
file_label.pack()

# Create a button to trigger file selection
select_button = tk.Button(root, text="Select Compressed File", command=select_file)
select_button.pack()

# Create a button to trigger extraction and sorting
extract_button = tk.Button(root, text="Extract and Sort", command=extract_and_sort)
extract_button.pack(pady=10)

# Add keyboard shortcuts for opening files and preferences
root.bind('<Control-o>', lambda event: select_file())
root.bind('<Control-p>', lambda event: open_preferences())

# Run the Tkinter main loop
root.mainloop()
