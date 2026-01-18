import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
import time
import random
import json
import os
import pyautogui
import pygetwindow
import win32gui, win32api
import win32con
import schedule
import ctypes
from datetime import datetime

# --- Constants & Default Data ---
QUEST_CONFIG_FILE = "quest_configs.json"
SKILL_LOC_FILE = "skill_locations.json"
CLASS_CONFIG_FILE = "class_configs.json"

DEFAULT_QUESTS = {
    "Default Quest": {
        "interval_minutes": 2.0,
        "coordinates": [(360, 340), (385, 920), (1085, 610), (850, 700)]
    }
}

# Default Classes (Created if config file doesn't exist)
DEFAULT_CLASSES = {
    "Archmage": {
        "auto": {"cd": 2.5, "use": False},
        "skill1": {"cd": 2.5, "use": True},
        "skill2": {"cd": 2.5, "use": True},
        "skill3": {"cd": 2.5, "use": False},
        "skill4": {"cd": 2.5, "use": False}
    },
    "VHL": {
        "auto": {"cd": 2.0, "use": False},
        "skill1": {"cd": 3.0, "use": True},
        "skill2": {"cd": 3.0, "use": True},
        "skill3": {"cd": 3.0, "use": True},
        "skill4": {"cd": 9.0, "use": True}
    },
    "Revenant": {
        "auto": {"cd": 2.0, "use": False},
        "skill1": {"cd": 4.0, "use": True},
        "skill2": {"cd": 4.0, "use": True},
        "skill3": {"cd": 4.0, "use": True},
        "skill4": {"cd": 9.0, "use": True}
    },
    "LOO": {
        "auto": {"cd": 2.0, "use": True},
        "skill1": {"cd": 5.0, "use": False},
        "skill2": {"cd": 7.0, "use": False},
        "skill3": {"cd": 5.0, "use": True},
        "skill4": {"cd": 4.0, "use": True}
    }
}

# Standard layout of skills we need to track
REQUIRED_SKILLS = ["auto", "skill1", "skill2", "skill3", "skill4"]

class AQWBotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AQW Background Bot v4.0 (Clicker Edition)")
        self.root.geometry("800x1050")
        
        #Bot state variables
        self.running = False
        self.bot_thread = None
        self.target_handle = None

        self.last_skill_timestamps = {}
        self.last_quest_time = 0

        # Load Data
        self.quest_data = self.load_json(QUEST_CONFIG_FILE, DEFAULT_QUESTS)
        self.class_data = self.load_json(CLASS_CONFIG_FILE, DEFAULT_CLASSES)
        self.skill_locations = self.load_json(SKILL_LOC_FILE, {}) # Format: {"auto": [x, y], ...}

        self.current_skill_config = {}
        self.current_quest_config = {}

        # --- UI Elements ---
       # 1. Target Selection
        frame_top = tk.Frame(root, relief="groove", bd=2)
        frame_top.pack(fill="x", padx=10, pady=10)
        
        tk.Label(frame_top, text="Target Window:").pack(side=tk.LEFT, padx=5)
        self.lbl_target = tk.Label(frame_top, text="Not Selected", fg="red", font=("Arial", 9, "bold"))
        self.lbl_target.pack(side=tk.LEFT, padx=5)
        
        self.btn_select_target = tk.Button(frame_top, text="Select (3s)", command=self.start_selection_countdown, bg="#ddd")
        self.btn_select_target.pack(side=tk.RIGHT, padx=5, pady=5)

        # 2. Tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=5)
        
        # Tab 1: Main Controls
        self.tab_main = tk.Frame(self.notebook)
        self.notebook.add(self.tab_main, text="Bot Controls")
        self.setup_main_tab()
        
        # Tab 2: Class Editor (NEW)
        self.tab_class_editor = tk.Frame(self.notebook)
        self.notebook.add(self.tab_class_editor, text="Class Editor")
        self.setup_class_tab()
        
        # Tab 3: Skill Locations
        self.tab_skills = tk.Frame(self.notebook)
        self.notebook.add(self.tab_skills, text="Skill Locations")
        self.setup_loc_tab()
        
        # Tab 4: Quest Editor
        self.tab_editor = tk.Frame(self.notebook)
        self.notebook.add(self.tab_editor, text="Quest Editor")
        self.setup_quest_tab()

        # 3. Logging Area
        tk.Label(root, text="Log:").pack(anchor="w", padx=10)
        self.log_text = tk.Text(root, height=8, state=tk.DISABLED, font=("Consolas", 9))
        self.log_text.pack(fill="x", padx=10, pady=(0, 10))

    # --- File I/O ---
    def load_json(self, filename, default):
        if os.path.exists(filename):
            try:
                with open(filename, "r") as f:
                    return json.load(f)
            except:
                return default.copy()
        return default.copy()

    def save_json(self, filename, data):
        try:
            with open(filename, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            self.log(f"Error saving {filename}: {e}")

    # --- GUI Setup: Main ---
    def setup_main_tab(self):
        frame = tk.Frame(self.tab_main, padx=20, pady=20)
        frame.pack(fill="both", expand=True)
        
        # Class Selection
        tk.Label(frame, text="Select Class Mode:").pack(anchor="w")
        self.var_class = tk.StringVar()
        self.cb_class = ttk.Combobox(frame, textvariable=self.var_class, state="readonly")
        self.cb_class.pack(fill="x", pady=(0, 15))
        # Populate values
        self.cb_class['values'] = list(self.class_data.keys())
        if self.class_data: self.cb_class.current(0)

        # Quest Selection
        tk.Label(frame, text="Select Quest Profile:").pack(anchor="w")
        self.var_quest = tk.StringVar()
        self.cb_quest = ttk.Combobox(frame, textvariable=self.var_quest, state="readonly")
        self.cb_quest['values'] = list(self.quest_data.keys())
        if self.quest_data: self.cb_quest.current(0)
        self.cb_quest.pack(fill="x", pady=(0, 5))
        
        # Toggle Questing
        self.var_quest_enabled = tk.BooleanVar(value=True)
        self.chk_quest_enabled = tk.Checkbutton(frame, text="Enable Quest Turn-in", variable=self.var_quest_enabled)
        self.chk_quest_enabled.pack(anchor="w", pady=(0, 15))
        
        # Status
        self.lbl_status = tk.Label(frame, text="STOPPED", fg="red", font=("Arial", 14, "bold"))
        self.lbl_status.pack(pady=10)
        
        # Buttons
        btn_frame = tk.Frame(frame)
        btn_frame.pack(pady=10)
        
        self.btn_start = tk.Button(btn_frame, text="START", bg="green", fg="white", width=12, height=2, command=self.start_bot)
        self.btn_start.pack(side=tk.LEFT, padx=10)
        
        self.btn_stop = tk.Button(btn_frame, text="STOP", bg="red", fg="white", width=12, height=2, command=self.stop_bot, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=10)

    # --- UI: Class Editor (NEW) ---
    def setup_class_tab(self):
        frame = tk.Frame(self.tab_class_editor, padx=20, pady=20)
        frame.pack(fill="both", expand=True)
        
        # Top: Select Class to Edit
        top_frame = tk.Frame(frame)
        top_frame.pack(fill="x", pady=5)
        
        tk.Label(top_frame, text="Edit Class:").pack(side=tk.LEFT)
        self.var_edit_class_name = tk.StringVar()
        self.cb_edit_class = ttk.Combobox(top_frame, textvariable=self.var_edit_class_name, state="readonly")
        self.cb_edit_class.pack(side=tk.LEFT, padx=5, expand=True, fill="x")
        self.cb_edit_class.bind("<<ComboboxSelected>>", self.load_class_editor_data)
        
        tk.Button(top_frame, text="+ New", command=self.create_new_class, width=6).pack(side=tk.RIGHT)
        tk.Button(top_frame, text="- Del", command=self.delete_class, width=6).pack(side=tk.RIGHT, padx=2)
        
        tk.Frame(frame, height=2, bd=1, relief="sunken").pack(fill="x", pady=15)

        # Editor Grid
        self.class_editor_vars = {} # Stores BooleanVar and DoubleVar for each skill
        
        grid_frame = tk.Frame(frame)
        grid_frame.pack(fill="x")
        
        tk.Label(grid_frame, text="Enabled", font=("Arial", 9, "bold")).grid(row=0, column=1, padx=5)
        tk.Label(grid_frame, text="Cooldown (s)", font=("Arial", 9, "bold")).grid(row=0, column=2, padx=5)

        for i, skill in enumerate(REQUIRED_SKILLS):
            row = i + 1
            tk.Label(grid_frame, text=skill.capitalize(), width=10, anchor="w").grid(row=row, column=0, pady=5)
            
            # Use Checkbox
            use_var = tk.BooleanVar(value=True)
            chk = tk.Checkbutton(grid_frame, variable=use_var)
            chk.grid(row=row, column=1)
            
            # Cooldown Entry
            cd_var = tk.DoubleVar(value=2.5)
            ent = tk.Entry(grid_frame, textvariable=cd_var, width=8)
            ent.grid(row=row, column=2)
            
            self.class_editor_vars[skill] = {"use": use_var, "cd": cd_var}

        # Save Button
        tk.Button(frame, text="Save Class Changes", command=self.save_class_changes, bg="#ddffdd", height=2).pack(fill="x", pady=20)

        # --- FIX: Initialize the dropdown and load data immediately ---
        class_names = list(self.class_data.keys())
        self.cb_edit_class['values'] = class_names
        if class_names:
            self.cb_edit_class.current(0)
            # Only load data AFTER the grid variables (self.class_editor_vars) are created above
            self.load_class_editor_data()

    # --- GUI Setup: Skill Setup (NEW) ---
    def setup_loc_tab(self):
        frame = tk.Frame(self.tab_skills, padx=20, pady=20)
        frame.pack(fill="both", expand=True)
        
        tk.Label(frame, text="Record the screen location of each skill.", font=("Arial", 10)).pack(pady=(0,15))
        
        # Grid for skill buttons
        self.skill_status_labels = {}
        self.skill_record_btns = {}
        
        grid_frame = tk.Frame(frame)
        grid_frame.pack(fill="x")
        
        # Friendly names map
        display_names = {
            "auto": "Auto Attack (1)",
            "skill1": "Skill 1 (2)",
            "skill2": "Skill 2 (3)",
            "skill3": "Skill 3 (4)",
            "skill4": "Skill 4 (5)"
        }
        
        for i, skill_key in enumerate(REQUIRED_SKILLS):
            row = i
            # Name
            tk.Label(grid_frame, text=display_names[skill_key], width=15, anchor="w").grid(row=row, column=0, pady=5)
            
            # Status
            coords = self.skill_locations.get(skill_key, None)
            status_text = f"Loc: {coords}" if coords else "Not Set"
            fg_color = "black" if coords else "red"
            
            lbl = tk.Label(grid_frame, text=status_text, width=15, fg=fg_color)
            lbl.grid(row=row, column=1, pady=5)
            self.skill_status_labels[skill_key] = lbl
            
            # Button
            btn = tk.Button(grid_frame, text="Record", command=lambda s=skill_key: self.record_skill_loc(s))
            btn.grid(row=row, column=2, pady=5, padx=5)
            self.skill_record_btns[skill_key] = btn

    # --- GUI Setup: Quest Editor ---
    def setup_quest_tab(self):
        frame = tk.Frame(self.tab_editor, padx=10, pady=10)
        frame.pack(fill="both", expand=True)
        
        top_frame = tk.Frame(frame)
        top_frame.pack(fill="x", pady=5)
        
        tk.Label(top_frame, text="Profile:").pack(side=tk.LEFT)
        self.var_editor_quest = tk.StringVar()
        self.cb_editor = ttk.Combobox(top_frame, textvariable=self.var_editor_quest, values=list(self.quest_data.keys()), state="readonly")
        self.cb_editor.pack(side=tk.LEFT, padx=5, expand=True, fill="x")
        self.cb_editor.bind("<<ComboboxSelected>>", self.load_quest_editor_data)
        
        tk.Button(top_frame, text="+ New", command=self.create_new_profile, width=6).pack(side=tk.RIGHT)
        tk.Button(top_frame, text="- Del", command=self.delete_profile, width=6).pack(side=tk.RIGHT, padx=2)

        # Interval
        int_frame = tk.Frame(frame)
        int_frame.pack(fill="x", pady=10)
        tk.Label(int_frame, text="Interval (min):").pack(side=tk.LEFT)
        self.var_interval = tk.DoubleVar(value=2.0)
        tk.Entry(int_frame, textvariable=self.var_interval, width=8).pack(side=tk.LEFT, padx=5)
        tk.Button(int_frame, text="Save Interval", command=self.save_quest_changes, bg="#ddffdd").pack(side=tk.RIGHT)

        tk.Label(frame, text="Quest Click Points:").pack(anchor="w")
        self.list_coords = tk.Listbox(frame, height=8)
        self.list_coords.pack(fill="both", expand=True, pady=5)
        
        act_frame = tk.Frame(frame)
        act_frame.pack(fill="x", pady=5)
        
        self.btn_capture = tk.Button(act_frame, text="Capture Point (3s)", command=self.capture_quest_coordinate, bg="#eebb99")
        self.btn_capture.pack(side=tk.LEFT, fill="x", expand=True, padx=2)
        tk.Button(act_frame, text="Remove Sel", command=self.remove_quest_coordinate).pack(side=tk.LEFT, fill="x", expand=True, padx=2)

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

    # --- Logic: Class Editor ---
    def create_new_class(self):
        name = simpledialog.askstring("New Class", "Enter name for new class:")
        if name:
            if name in self.class_data:
                messagebox.showerror("Error", "Class already exists")
                return
            
            # Create default structure for new class
            self.class_data[name] = {s: {"cd": 2.5, "use": True} for s in REQUIRED_SKILLS}
            self.refresh_class_combos()
            self.cb_edit_class.set(name)
            self.load_class_editor_data()
            self.save_json(CLASS_CONFIG_FILE, self.class_data)

    def delete_class(self):
        name = self.var_edit_class_name.get()
        if name in self.class_data:
            if messagebox.askyesno("Confirm", f"Delete class '{name}'?"):
                del self.class_data[name]
                self.refresh_class_combos()
                if self.class_data:
                    self.cb_edit_class.current(0)
                    self.load_class_editor_data()
                self.save_json(CLASS_CONFIG_FILE, self.class_data)

    def refresh_class_combos(self):
        names = list(self.class_data.keys())
        self.cb_class['values'] = names
        self.cb_edit_class['values'] = names
        if names:
            self.cb_edit_class.set(names[0])
            self.load_class_editor_data() # Refresh editor fields

    def load_class_editor_data(self, event=None):
        name = self.var_edit_class_name.get()
        if name in self.class_data:
            data = self.class_data[name]
            
            for skill in REQUIRED_SKILLS:
                skill_data = data.get(skill, {"cd": 2.5, "use": True})
                self.class_editor_vars[skill]["use"].set(skill_data.get("use", True))
                self.class_editor_vars[skill]["cd"].set(skill_data.get("cd", 2.5))

    def save_class_changes(self):
        name = self.var_edit_class_name.get()
        if name in self.class_data:
            new_data = {}
            try:
                for skill in REQUIRED_SKILLS:
                    use = self.class_editor_vars[skill]["use"].get()
                    cd = self.class_editor_vars[skill]["cd"].get()
                    new_data[skill] = {"cd": cd, "use": use}
                
                self.class_data[name] = new_data
                self.save_json(CLASS_CONFIG_FILE, self.class_data)
                self.log(f"Saved changes to class '{name}'")
            except Exception as e:
                self.log(f"Error saving class: {e}")

    # --- Logic: Skill Recorder ---
    def record_skill_loc(self, skill_key):
        if not self.target_handle:
            messagebox.showerror("Error", "Select Target Window first!")
            return
        
        btn = self.skill_record_btns[skill_key]
        btn.config(text="CLICK NOW (3)", state=tk.DISABLED)
        self.root.after(1000, lambda: self.skill_countdown(2, skill_key))

    def skill_countdown(self, n, skill_key):
        btn = self.skill_record_btns[skill_key]
        if n > 0:
            btn.config(text=f"CLICK NOW ({n})")
            self.root.after(1000, lambda: self.skill_countdown(n-1, skill_key))
        else:
            # Capture
            try:
                mx, my = win32api.GetCursorPos()
                client_point = win32gui.ScreenToClient(self.target_handle, (mx, my))
                cx, cy = client_point
                
                # Save
                self.skill_locations[skill_key] = [cx, cy]
                self.save_json(SKILL_LOC_FILE, self.skill_locations)
                
                # Update UI
                self.skill_status_labels[skill_key].config(text=f"Loc: [{cx}, {cy}]", fg="blue")
                self.log(f"Recorded {skill_key} at {cx},{cy}")
                
            except Exception as e:
                self.log(f"Record Error: {e}")
            finally:
                btn.config(text="Record", state=tk.NORMAL)

    # --- Logic: Quest Editor ---
    def create_new_profile(self):
        name = simpledialog.askstring("New Profile", "Enter name:")
        if name and name not in self.quest_data:
            self.quest_data[name] = {"interval_minutes": 2.0, "coordinates": []}
            self.refresh_quest_combos()
            self.cb_editor.set(name)
            self.load_quest_editor_data()
            self.save_json(QUEST_CONFIG_FILE, self.quest_data)

    def delete_profile(self):
        name = self.var_editor_quest.get()
        if name in self.quest_data:
            del self.quest_data[name]
            self.refresh_quest_combos()
            if self.quest_data:
                self.cb_editor.current(0)
                self.load_quest_editor_data()
            self.save_json(QUEST_CONFIG_FILE, self.quest_data)

    def refresh_quest_combos(self):
        names = list(self.quest_data.keys())
        self.cb_quest['values'] = names
        self.cb_editor['values'] = names

    def load_quest_editor_data(self, event=None):
        name = self.var_editor_quest.get()
        if name in self.quest_data:
            data = self.quest_data[name]
            self.var_interval.set(data.get("interval_minutes", 2.0))
            self.list_coords.delete(0, tk.END)
            for coord in data.get("coordinates", []):
                self.list_coords.insert(tk.END, f"({coord[0]}, {coord[1]})")

    def save_quest_changes(self):
        name = self.var_editor_quest.get()
        if name in self.quest_data:
            try:
                self.quest_data[name]["interval_minutes"] = float(self.var_interval.get())
                self.save_json(QUEST_CONFIG_FILE, self.quest_data)
                self.log(f"Saved changes to '{name}'")
            except ValueError: pass

    def capture_quest_coordinate(self):
        if not self.target_handle:
            messagebox.showerror("Error", "Select Target Window first!")
            return
        self.btn_capture.config(text="CLICK SPOT (3)", state=tk.DISABLED)
        self.root.after(1000, lambda: self.quest_countdown(2))

    def quest_countdown(self, n):
        if n > 0:
            self.btn_capture.config(text=f"CLICK SPOT ({n})")
            self.root.after(1000, lambda: self.quest_countdown(n-1))
        else:
            try:
                mx, my = win32api.GetCursorPos()
                client_point = win32gui.ScreenToClient(self.target_handle, (mx, my))
                cx, cy = client_point
                name = self.var_editor_quest.get()
                if name in self.quest_data:
                    self.quest_data[name]["coordinates"].append([cx, cy])
                    self.load_quest_editor_data()
                    self.save_json(QUEST_CONFIG_FILE, self.quest_data)
                    self.log(f"Recorded Quest Point: {cx}, {cy}")
            except Exception as e:
                self.log(f"Capture error: {e}")
            finally:
                self.btn_capture.config(text="Capture Point (3s)", state=tk.NORMAL)

    def remove_quest_coordinate(self):
        sel = self.list_coords.curselection()
        if not sel: return
        idx = sel[0]
        name = self.var_editor_quest.get()
        if name in self.quest_data:
            del self.quest_data[name]["coordinates"][idx]
            self.load_quest_editor_data()
            self.save_json(QUEST_CONFIG_FILE, self.quest_data)

    # --- Bot Logic ---
    def make_lparam(self, x, y):
        return (y << 16) | (x & 0xFFFF)

    def send_background_click(self, x, y):
        try:
            lparam = self.make_lparam(x, y)
            win32gui.PostMessage(self.target_handle, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lparam)
            time.sleep(0.05) 
            win32gui.PostMessage(self.target_handle, win32con.WM_LBUTTONUP, 0, lparam)
        except Exception as e:
            self.log(f"Click Error: {e}")

    def start_bot(self):
        if self.running: return
        if not self.target_handle:
            messagebox.showerror("Error", "Please select a target window.")
            return
        
        # Verify Skills are set
        missing = [s for s in REQUIRED_SKILLS if s not in self.skill_locations]
        if missing:
            messagebox.showerror("Missing Skills", f"Please record locations for: {', '.join(missing)}")
            return
        
        # Load Configs using selected class
        class_name = self.var_class.get()
        if not class_name or class_name not in self.class_data:
            messagebox.showerror("Error", "Invalid Class Selection")
            return
        
        self.current_skill_config = self.class_data[class_name]
        self.current_quest_config = self.quest_data.get(self.var_quest.get(), {})
        
        self.last_skill_timestamps = {k:0 for k in REQUIRED_SKILLS}
        self.last_quest_time = time.time()
        
        self.running = True
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.lbl_status.config(text="RUNNING", fg="green")
        self.log(f"Started: {class_name}")
        
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
                
                # 1. Skills Logic
                for skill_name in REQUIRED_SKILLS:
                    if not self.running: break
                    
                    # New Config Check: Does the skill exist in this class AND is it enabled?
                    skill_settings = self.current_skill_config.get(skill_name, {})
                    if not skill_settings.get("use", True):
                        continue # Skip disabled skills
                    
                    # Cooldown Check
                    cooldown = skill_settings.get("cd", 2.5)
                    last = self.last_skill_timestamps.get(skill_name, 0)
                    
                    if now - last >= cooldown:
                        if skill_name in self.skill_locations:
                            loc = self.skill_locations[skill_name]
                            self.send_background_click(loc[0], loc[1])
                            
                            self.last_skill_timestamps[skill_name] = now
                            self.log(f"Clicked {skill_name}")
                            time.sleep(random.uniform(0.1, 0.3))
                            break # Limit 1 skill per cycle
                
                # 2. Quests
                if self.var_quest_enabled.get():
                    q_interval = self.current_quest_config.get("interval_minutes", 2) * 60
                    if now - self.last_quest_time >= q_interval:
                        self.perform_quest_turn_in()
                        self.last_quest_time = time.time()

                time.sleep(0.5)
                
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

        for point in coords:
            if not self.running: break
            self.send_background_click(point[0], point[1])
            time.sleep(1)
            
        self.log("Quest Turn-in Complete.")

if __name__ == "__main__":
    root = tk.Tk()
    app = AQWBotApp(root)
    root.mainloop()