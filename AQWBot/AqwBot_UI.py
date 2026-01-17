import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
import time
import random
import json
import os
import pyautogui
import pygetwindow
import win32gui
import win32con
import schedule
from datetime import datetime

# --- Constants & Default Data ---
CONFIG_FILE = "quest_configs.json"

DEFAULT_QUESTS = {
    "Default Quest": {
        "interval_minutes": 2.0,
        "coordinates": [(360, 340), (385, 920), (1085, 610), (850, 700)]
    }
}

SKILL_KEYS = {
    "auto": '1', "skill1": '2', "skill2": '3', "skill3": '4', "skill4": '5',
}

SKILL_CONFIGS = {
    "Archmage": {"skill2": 2.5, "skill1": 2.5},
    "VHL": {"skill4": 9, "skill2": 3, "skill3": 3, "skill1": 3},
    "LOO": {"skill4": 2, "skill3": 5, "skill2": 7, "skill1": 5},
}

class AQWBotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AQW Bot Helper")
        self.root.geometry("500x620")
        
        #Bot state variables
        self.running = False
        self.bot_thread = None
        self.target_window = None
        self.target_handle = None

        self.last_skill_timestamps = {}
        self.last_quest_time = 0

        # Load Quest Configs
        self.quest_data = self.load_quest_configs()
        self.current_skill_config = {}
        self.current_quest_config = {}

        # --- UI Elements ---
        # 1. Target Selection (Always Visible)
        frame_top = tk.Frame(root)
        frame_top.pack(fill="x", padx=10, pady=10)
        
        tk.Label(frame_top, text="Target Window:").pack(side=tk.LEFT)
        self.lbl_target = tk.Label(frame_top, text="Not Selected", fg="red", font=("Arial", 10, "bold"))
        self.lbl_target.pack(side=tk.LEFT, padx=10)
        
        self.btn_select_target = tk.Button(frame_top, text="Select (3s)", command=self.start_selection_countdown, bg="#ddd")
        self.btn_select_target.pack(side=tk.RIGHT)

        # 2. Tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=5)

        # Tab 1: Main Controls
        self.tab_main = tk.Frame(self.notebook)
        self.notebook.add(self.tab_main, text="Bot Controls")
        self.setup_main_tab()

        # Tab 2: Quest Editor
        self.tab_editor = tk.Frame(self.notebook)
        self.notebook.add(self.tab_editor, text="Quest Editor")
        self.setup_editor_tab()

        # 3. Logging Area (Bottom)
        tk.Label(root, text="Log:").pack(anchor="w", padx=10)
        self.log_text = tk.Text(root, height=8, state=tk.DISABLED, font=("Consolas", 9))
        self.log_text.pack(fill="x", padx=10, pady=(0, 10))

    def load_quest_configs(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    return json.load(f)
            except:
                return DEFAULT_QUESTS.copy()
        return DEFAULT_QUESTS.copy()

    def save_quest_configs(self):
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.quest_data, f, indent=4)
            self.log("Quest configurations saved.")
        except Exception as e:
            self.log(f"Error saving config: {e}")

    # --- GUI Setup Helpers ---
    def setup_main_tab(self):
        frame = tk.Frame(self.tab_main, padx=20, pady=20)
        frame.pack(fill="both", expand=True)
        
        # Class Selection
        tk.Label(frame, text="Select Class Mode:").pack(anchor="w")
        self.var_class = tk.StringVar(value="Archmage")
        cb_class = ttk.Combobox(frame, textvariable=self.var_class, values=list(SKILL_CONFIGS.keys()), state="readonly")
        cb_class.pack(fill="x", pady=(0, 15))
        cb_class.bind("<<ComboboxSelected>>", self.on_config_change)
        
        # Quest Selection
        tk.Label(frame, text="Select Quest Profile:").pack(anchor="w")
        self.var_quest = tk.StringVar(value=list(self.quest_data.keys())[0])
        self.cb_quest = ttk.Combobox(frame, textvariable=self.var_quest, values=list(self.quest_data.keys()), state="readonly")
        self.cb_quest.pack(fill="x", pady=(0, 15))
        self.cb_quest.bind("<<ComboboxSelected>>", self.on_config_change)
        
        # Toggle Questing - NEW FEATURE
        self.var_quest_enabled = tk.BooleanVar(value=True)
        self.chk_quest_enabled = tk.Checkbutton(frame, text="Enable Quest Turn-in", variable=self.var_quest_enabled)
        self.chk_quest_enabled.pack(anchor="w", pady=(0, 15))

        # Status
        self.lbl_status = tk.Label(frame, text="STOPPED", fg="red", font=("Arial", 14, "bold"))
        self.lbl_status.pack(pady=20)
        
        # Buttons
        btn_frame = tk.Frame(frame)
        btn_frame.pack(pady=10)
        
        self.btn_start = tk.Button(btn_frame, text="START", bg="green", fg="white", width=12, height=2, command=self.start_bot)
        self.btn_start.pack(side=tk.LEFT, padx=10)
        
        self.btn_stop = tk.Button(btn_frame, text="STOP", bg="red", fg="white", width=12, height=2, command=self.stop_bot, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=10)

    def setup_editor_tab(self):
        frame = tk.Frame(self.tab_editor, padx=10, pady=10)
        frame.pack(fill="both", expand=True)
        
        # Top Controls: Profile Management
        top_frame = tk.Frame(frame)
        top_frame.pack(fill="x", pady=5)
        
        tk.Label(top_frame, text="Edit Profile:").pack(side=tk.LEFT)
        self.var_editor_quest = tk.StringVar()
        self.cb_editor = ttk.Combobox(top_frame, textvariable=self.var_editor_quest, values=list(self.quest_data.keys()), state="readonly")
        self.cb_editor.pack(side=tk.LEFT, padx=5, expand=True, fill="x")
        self.cb_editor.bind("<<ComboboxSelected>>", self.load_editor_data)
        
        tk.Button(top_frame, text="+ New", command=self.create_new_profile, width=6).pack(side=tk.RIGHT)
        tk.Button(top_frame, text="- Del", command=self.delete_profile, width=6).pack(side=tk.RIGHT, padx=2)

        # Interval Settings
        int_frame = tk.Frame(frame)
        int_frame.pack(fill="x", pady=10)
        tk.Label(int_frame, text="Interval (minutes):").pack(side=tk.LEFT)
        self.var_interval = tk.DoubleVar(value=2.0)
        tk.Entry(int_frame, textvariable=self.var_interval, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(int_frame, text="Save Changes", command=self.save_editor_changes, bg="#ddffdd").pack(side=tk.RIGHT)

        # Coordinate List
        tk.Label(frame, text="Coordinates (Relative to Window):").pack(anchor="w")
        self.list_coords = tk.Listbox(frame, height=8)
        self.list_coords.pack(fill="both", expand=True, pady=5)
        
        # Coord Actions
        act_frame = tk.Frame(frame)
        act_frame.pack(fill="x", pady=5)
        
        self.btn_capture = tk.Button(act_frame, text="Capture Point (3s)", command=self.capture_coordinate, bg="#eebb99")
        self.btn_capture.pack(side=tk.LEFT, fill="x", expand=True, padx=2)
        
        tk.Button(act_frame, text="Remove Selected", command=self.remove_coordinate).pack(side=tk.LEFT, fill="x", expand=True, padx=2)

    # --- Window Selection Logic ---
    def start_selection_countdown(self):
        self.btn_select_target.config(state=tk.DISABLED, text="Click Window (3)")
        self.root.after(1000, lambda: self.countdown(2))

    def countdown(self, n):
        if n > 0:
            self.btn_select_target.config(text=f"Click Window ({n})")
            self.root.after(1000, lambda: self.countdown(n-1))
        else:
            self.capture_target_window()

    def capture_target_window(self):
        try:
            win = pygetwindow.getActiveWindow()
            if win:
                self.target_window = win
                self.target_handle = win._hWnd
                self.lbl_target.config(text=f"{win.title[:20]}...", fg="green")
                self.log(f"Target captured: {win.title}")
            else:
                self.log("No active window found.")
        except Exception as e:
            self.log(f"Error capturing window: {e}")
        finally:
            self.btn_select_target.config(state=tk.NORMAL, text="Select (3s)")

    # --- Logic: Quest Editor ---
    def create_new_profile(self):
        name = simpledialog.askstring("New Profile", "Enter name for new quest profile:")
        if name:
            if name in self.quest_data:
                messagebox.showerror("Error", "Profile already exists.")
                return
            self.quest_data[name] = {"interval_minutes": 2.0, "coordinates": []}
            self.refresh_combo_boxes()
            self.cb_editor.set(name)
            self.load_editor_data()
            self.save_quest_configs()

    def delete_profile(self):
        name = self.var_editor_quest.get()
        if not name: return
        if messagebox.askyesno("Confirm", f"Delete profile '{name}'?"):
            del self.quest_data[name]
            self.refresh_combo_boxes()
            if self.quest_data:
                self.cb_editor.current(0)
                self.load_editor_data()
            self.save_quest_configs()

    def refresh_combo_boxes(self):
        names = list(self.quest_data.keys())
        self.cb_quest['values'] = names
        self.cb_editor['values'] = names

    def load_editor_data(self, event=None):
        name = self.var_editor_quest.get()
        if name in self.quest_data:
            data = self.quest_data[name]
            self.var_interval.set(data.get("interval_minutes", 2.0))
            self.list_coords.delete(0, tk.END)
            for coord in data.get("coordinates", []):
                self.list_coords.insert(tk.END, f"({coord[0]}, {coord[1]})")

    def save_editor_changes(self):
        name = self.var_editor_quest.get()
        if name in self.quest_data:
            # Coordinates are updated in real-time in the list variable, 
            # we just need to ensure interval is saved
            try:
                self.quest_data[name]["interval_minutes"] = float(self.var_interval.get())
                self.save_quest_configs()
                self.log(f"Saved changes to '{name}'")
            except ValueError:
                messagebox.showerror("Error", "Interval must be a number.")

    def capture_coordinate(self):
        if not self.target_window:
            messagebox.showerror("Error", "Select Target Window first!")
            return
        
        self.btn_capture.config(text="CLICK SPOT NOW (3)", state=tk.DISABLED)
        self.root.after(1000, lambda: self.capture_countdown(2))

    def capture_countdown(self, n):
        if n > 0:
            self.btn_capture.config(text=f"CLICK SPOT NOW ({n})")
            self.root.after(1000, lambda: self.capture_countdown(n-1))
        else:
            # Record Position
            try:
                mx, my = pyautogui.position()
                # Calculate relative
                rel_x = mx - self.target_window.left
                rel_y = my - self.target_window.top
                
                # Add to data
                name = self.var_editor_quest.get()
                if name in self.quest_data:
                    self.quest_data[name]["coordinates"].append((rel_x, rel_y))
                    self.load_editor_data() # Refresh list
                    self.save_quest_configs()
                    self.log(f"Recorded point: {rel_x}, {rel_y}")
            except Exception as e:
                self.log(f"Capture error: {e}")
            finally:
                self.btn_capture.config(text="Capture Point (3s)", state=tk.NORMAL)

    def remove_coordinate(self):
        sel = self.list_coords.curselection()
        if not sel: return
        idx = sel[0]
        name = self.var_editor_quest.get()
        if name in self.quest_data:
            del self.quest_data[name]["coordinates"][idx]
            self.load_editor_data()
            self.save_quest_configs()

    # --- Bot Logic ---
    def on_config_change(self, event=None):
        if self.running:
            self.stop_bot()
            self.log("Configuration changed. Bot stopped.")

    def start_bot(self):
        if self.running: return
        if not self.target_handle:
            messagebox.showerror("Error", "Please select a target window.")
            return
        
        # Load Configs
        class_name = self.var_class.get()
        quest_name = self.var_quest.get()
        
        self.current_skill_config = SKILL_CONFIGS.get(class_name, {})
        self.current_quest_config = self.quest_data.get(quest_name, {})
        
        # Reset Timers
        self.last_skill_timestamps = {k:0 for k in self.current_skill_config}
        self.last_quest_time = time.time() # Start timer now (Wait 1 interval before first turn in?) 
        # Or if you want immediate turn in: self.last_quest_time = 0
        
        self.running = True
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.lbl_status.config(text="RUNNING", fg="green")

        status_q = quest_name if self.var_quest_enabled.get() else "DISABLED"
        self.log(f"Started: {class_name} | Quest: {status_q}")
        
        self.bot_thread = threading.Thread(target=self.bot_loop, daemon=True)
        self.bot_thread.start()

    def stop_bot(self):
        self.running = False
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        self.lbl_status.config(text="STOPPED", fg="red")
        self.log("Bot stopped.")

    def log(self, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{timestamp}] {msg}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def bot_loop(self):
        while self.running:
            try:
                now = time.time()
                
                # 1. Skills
                for skill, cooldown in self.current_skill_config.items():
                    if not self.running: break
                    last = self.last_skill_timestamps.get(skill, 0)
                    if now - last >= cooldown:
                        # Send Input
                        win32gui.PostMessage(self.target_handle, win32con.WM_KEYDOWN, ord(SKILL_KEYS[skill]), 0)
                        win32gui.PostMessage(self.target_handle, win32con.WM_KEYUP, ord(SKILL_KEYS[skill]), 0)
                        self.last_skill_timestamps[skill] = now
                        self.log(f"Used {skill}")
                        time.sleep(random.uniform(0.1, 0.3))
                        break # Only one skill per tick

                # 2. Quests (Only if checkbox is enabled)
                if self.var_quest_enabled.get():
                    q_interval = self.current_quest_config.get("interval_minutes", 2) * 60
                    if now - self.last_quest_time >= q_interval:
                        self.perform_quest_turn_in()
                        self.last_quest_time = time.time()

                time.sleep(1) # Main loop tick
                
            except Exception as e:
                self.log(f"Loop Error: {e}")
                self.stop_bot()
                break

    def perform_quest_turn_in(self):
        self.log("Starting Quest Turn-in...")
        coords = self.current_quest_config.get("coordinates", [])
        if not coords:
            self.log("No coordinates in quest profile.")
            return

        try:
            # We need absolute coordinates for PyAutoGUI
            win_left = self.target_window.left
            win_top = self.target_window.top
            
            for (rx, ry) in coords:
                if not self.running: break
                
                # Calculate absolute
                abs_x = win_left + rx
                abs_y = win_top + ry
                
                pyautogui.click(abs_x, abs_y)
                time.sleep(1) # Wait between clicks
                
            self.log("Quest Turn-in Complete.")
            
        except Exception as e:
            self.log(f"Quest Error: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AQWBotApp(root)
    root.mainloop()