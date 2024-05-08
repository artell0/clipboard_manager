import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog, Label, Entry, Button, Toplevel, Scrollbar, Frame, Listbox, Text, Menu, Radiobutton, Checkbutton, IntVar
import json
import os
import threading
from datetime import datetime
import pyperclip
from PIL import Image, ImageTk


# Configuration for history size, timestamp visibility, and filter settings
config_file = "config.json"
if os.path.exists(config_file):
    with open(config_file, "r") as file:
        config = json.load(file)
else:
    config = {"history_size": 10, "show_timestamps": True, "filter_type": "All"}


# Load or initialize history
history_file = "clipboard_history.json"
if os.path.exists(history_file):
    with open(history_file, "r") as file:
        history = json.load(file)
else:
    history = []


def save_config():
    with open(config_file, "w") as file:
        json.dump(config, file)


def categorize_content(content):
    if content.startswith("http://") or content.startswith("https://"):
        return "URL"
    elif content.endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp")):
        return "Image File"
    elif content.endswith((".txt", ".pdf", ".doc", ".docx", ".md")):
        return "Document"
    elif content.endswith((".xlsx", ".xls")):
        return "Spreadsheet"
    elif content.endswith((".wav", ".mp3",)):
        return "Audio File"
    elif content.endswith((".mp4", ".mov", ".mkv")):
        return "Video File"
    else:
        return "Text"


def update_history(content, app):
    category = categorize_content(content)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    item = {"content": content, "category": category, "timestamp": timestamp}
    history.insert(0, item)  # Insert at the beginning for newest first
   
    # Maintain history size
    if len(history) > config["history_size"]:
        history.pop(-1)  # Remove the oldest item
   
    # Save history to file
    with open(history_file, "w") as file:
        json.dump(history, file)
   
    # Update GUI
    if app:
        app.update_listbox()
        if not app.lock_selection_var.get():
            app.selected_index = 0  # Reset selection if not locked
            app.listbox.selection_set(0)


def monitor_clipboard(app):
    last_value = ""
    while True:
        current_value = pyperclip.paste()
        if current_value != last_value:
            last_value = current_value
            print("Clipboard changed:", current_value)
            update_history(current_value, app)


class ClipboardApp:
    def __init__(self, master):
        self.master = master
        master.title("Enhanced Clipboard Manager")
       
        # Setup menu
        self.menu = Menu(master)
        master.config(menu=self.menu)
        self.file_menu = Menu(self.menu)
        self.menu.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Save History", command=self.save_history)
        self.file_menu.add_command(label="Load History", command=self.load_history)


        # Track selected index
        self.selected_index = 0
       
        # Bind Ctrl+V for pasting
        master.bind('<Control-v>', self.paste_item)


        # Additional UI elements for paste planning
        self.paste_plan_var = tk.StringVar(value="stay")
        self.paste_plan_frame = Frame(master)
        self.paste_plan_frame.pack(fill=tk.X)
        self.stay_radio = Radiobutton(self.paste_plan_frame, text="Stay", variable=self.paste_plan_var, value="stay")
        self.stay_radio.pack(side=tk.LEFT)
        self.up_radio = Radiobutton(self.paste_plan_frame, text="Up", variable=self.paste_plan_var, value="up")
        self.up_radio.pack(side=tk.LEFT)
        self.down_radio = Radiobutton(self.paste_plan_frame, text="Down", variable=self.paste_plan_var, value="down")
        self.down_radio.pack(side=tk.LEFT)
       
        # Checkbox to lock the selection
        self.lock_selection_var = IntVar()
        self.lock_selection_check = Checkbutton(self.paste_plan_frame, text="Lock Selection", variable=self.lock_selection_var)
        self.lock_selection_check.pack(side=tk.LEFT)


        # Collapsible text area for notes or drafting
        self.text_frame = Frame(master, height=100)
        self.text_area = Text(self.text_frame)
        self.text_area.pack(fill=tk.BOTH, expand=True)
        self.toggle_text_button = Button(master, text="Toggle Text Area", command=self.toggle_text_area)
        self.toggle_text_button.pack()


        # Listbox to display clipboard items
        self.listbox = Listbox(master, height=15, width=50)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
       
        # Scrollbar for the listbox
        self.scrollbar = Scrollbar(master, orient="vertical", command=self.listbox.yview)
        self.scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self.listbox.config(yscrollcommand=self.scrollbar.set)
       
        # Bind double-click event for editing
        self.listbox.bind('<Double-1>', self.edit_item)
       
        # Search bar for filtering history
        self.search_var = tk.StringVar()
        self.search_bar = Entry(master, textvariable=self.search_var)
        self.search_bar.pack()
        self.search_var.trace("w", lambda name, index, mode, sv=self.search_var: self.update_listbox())
       
        # Image preview area
        self.image_label = Label(master)
        self.image_label.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
       
        # Buttons for various actions
        self.clear_button = tk.Button(master, text="Clear History", command=self.clear_history)
        self.clear_button.pack(side=tk.BOTTOM, padx=10, pady=10)
       
        self.settings_button = tk.Button(master, text="Settings", command=self.open_settings)
        self.settings_button.pack(side=tk.BOTTOM, padx=10, pady=10)
       
        self.exit_button = tk.Button(master, text="Exit", command=master.quit)
        self.exit_button.pack(side=tk.BOTTOM, padx=10, pady=10)
       
        # Track selected index
        self.selected_index = 0


        # Bind Ctrl+V for pasting
        master.bind('<Control-v>', self.paste_item)


        # Update the listbox with current history (moved to the end)
        self.update_listbox()


    def toggle_text_area(self):
        if self.text_frame.winfo_viewable():
            self.text_frame.pack_forget()
        else:
            self.text_frame.pack(fill=tk.BOTH, expand=True)


    def update_listbox(self):
        search_term = self.search_var.get().lower()
        self.listbox.delete(0, tk.END)
        for item in history:
            if search_term in item['content'].lower():
                display_text = f"{item['category']}: {item['content'][:30]}... {item['timestamp'] if config['show_timestamps'] else ''}"
                self.listbox.insert(tk.END, display_text)
                if item['category'] == 'Image File':
                    self.display_image(item['content'])


        # Ensure selection is within bounds after updating
        if self.selected_index >= self.listbox.size():
            self.selected_index = self.listbox.size() - 1


        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(self.selected_index)


    def paste_item(self, event=None):
        if history:
            # Get the index of the currently selected item
            self.selected_index = self.listbox.curselection()[0]
            item_to_paste = history[self.selected_index]
            pyperclip.copy(item_to_paste['content'])


            # Update selection based on paste plan
            if self.paste_plan_var.get() == "up" and self.selected_index > 0:
                self.selected_index -= 1
            elif self.paste_plan_var.get() == "down" and self.selected_index < self.listbox.size() - 1:
                self.selected_index += 1


            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(self.selected_index)


    def update_listbox(self):
        search_term = self.search_var.get().lower()
        self.listbox.delete(0, tk.END)
        for item in history:
            if search_term in item['content'].lower():
                display_text = f"{item['category']}: {item['content'][:30]}... {item['timestamp'] if config['show_timestamps'] else ''}"
                self.listbox.insert(tk.END, display_text)
                if item['category'] == 'Image File':
                    self.display_image(item['content'])


        # Update selection based on paste plan and lock selection
        if not self.lock_selection_var.get():
            self.selected_index = 0
        else:
            if self.paste_plan_var.get() == "up" and self.selected_index > 0:
                self.selected_index -= 1
            elif self.paste_plan_var.get() == "down" and self.selected_index < self.listbox.size() - 1:
                self.selected_index += 1


        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(self.selected_index)


    def paste_item(self, event=None):
        if history:
            item_to_paste = history[self.selected_index]
            pyperclip.copy(item_to_paste['content'])


            # Update selection based on paste plan
            if self.paste_plan_var.get() == "up" and self.selected_index > 0:
                self.selected_index -= 1
            elif self.paste_plan_var.get() == "down" and self.selected_index < self.listbox.size() - 1:
                self.selected_index += 1


            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(self.selected_index)


    def display_image(self, image_path):
        try:
            img = Image.open(image_path)
            img.thumbnail((100, 100))
            photo = ImageTk.PhotoImage(img)
            self.image_label.config(image=photo)
            self.image_label.image = photo  # keep a reference!
        except Exception as e:
            print(e)  # Log or handle error appropriately


    def update_history(self, content, app):
        category = categorize_content(content)


        # Update GUI
        if app:
            app.update_listbox()
            # Only reset selection if not locked and a new item is added
            if not app.lock_selection_var.get() and content not in [item['content'] for item in history]:
                app.selected_index = 0  # Reset selection if not locked and new item
                app.listbox.selection_set(0)


    def edit_item(self, event):
        try:
            index = self.listbox.curselection()[0]
            item = history[index]
        except IndexError:
            return  # No item selected
       
        edit_window = Toplevel(self.master)
        edit_window.title("Edit Item")
       
        text_editor = Text(edit_window, wrap="word", height=10, width=50)
        text_editor.pack(padx=10, pady=10)
        text_editor.insert('1.0', item['content'])
       
        def save_edit():
            edited_content = text_editor.get('1.0', 'end-1c')
            item['content'] = edited_content
            update_history(item['content'], self)  # This will update the item and refresh the list
            edit_window.destroy()
       
        save_button = Button(edit_window, text="Save", command=save_edit)
        save_button.pack()


    def clear_history(self):
        global history
        history = []
        with open(history_file, "w") as file:
            json.dump(history, file)
        self.update_listbox()


    def open_settings(self):
        self.settings_window = Toplevel(self.master)
        self.settings_window.title("Settings")
       
        Label(self.settings_window, text="History Size:").pack()
       
        self.history_size_entry = Entry(self.settings_window)
        self.history_size_entry.pack()
        self.history_size_entry.insert(0, str(config["history_size"]))
       
        Button(self.settings_window, text="Save", command=self.save_settings).pack()


    def paste_item(self, event=None):
        if history:
            # Get the index of the currently selected item (no change here)
            self.selected_index = self.listbox.curselection()[0]
            item_to_paste = history[self.selected_index]
            pyperclip.copy(item_to_paste['content'])


            # Update selection based on paste plan ONLY if not locked
            if not self.lock_selection_var.get():
                if self.paste_plan_var.get() == "up" and self.selected_index > 0:
                    self.selected_index -= 1
                elif self.paste_plan_var.get() == "down" and self.selected_index < self.listbox.size() - 1:
                    self.selected_index += 1


            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(self.selected_index)


    def save_settings(self):
        try:
            history_size = int(self.history_size_entry.get())
            config["history_size"] = history_size
            save_config()
            self.settings_window.destroy()
            messagebox.showinfo("Settings Updated", "History size updated successfully!")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid integer for history size.")


    def save_history(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if filepath:
            with open(filepath, "w") as file:
                json.dump(history, file)
            messagebox.showinfo("Save Successful", "History saved successfully!")


    def load_history(self):
        filepath = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if filepath:
            with open(filepath, "r") as file:
                global history
                history = json.load(file)
            self.update_listbox()
            messagebox.showinfo("Load Successful", "History loaded successfully!")


if __name__ == "__main__":
    root = tk.Tk()
    app = ClipboardApp(root)
    threading.Thread(target=monitor_clipboard, args=(app,), daemon=True).start()
    root.mainloop()

