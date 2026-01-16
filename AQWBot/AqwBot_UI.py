import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import random
import pyautogui
import pygetwindow
import win32gui
import win32con
import schedule
from datetime import datetime

# --- Your Original Data ---
skill_keys = {
    "auto": '1',
    "skill1": '2',
    "skill2": '3',
    "skill3": '4',
    "skill4": '5',
}

# Skill configurations
skill_configs = {
    "Archmage": {
        "skill3": 2.5,
        "skill2": 2.5,
        "skill1": 2.5,
    },
    "VHL": {
        "skill4": 9,
        "skill2": 3,
        "skill3": 3,
        "skill1": 3,
    },
    "LOO": {
        "skill4": 2,
        "skill3": 5,
        "skill2": 7,
        "skill1": 5,
    }
}

coordinates_quest = [(360, 340), (385, 920), (1085, 610), (850, 700)]
QUEST_INTERVAL = 1

class AQWBotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AQW Bot Helper")
        self.root.geometry("400x420")
        
        #Bot state variables
        self.running = False
        self.bot_thread = None
        self.last_used_timestamps={}
        self.current_config={}
        self.target_window = None
        self.target_handle = None

        # --- UI Elements ---
        # Target Window Selection
        tk.Label(root, text="Step 1: Select Game Window").pack(pady=(15, 5))
        self.select_btn = tk.Button(root, text="Select Active Window (3s Delay)", 
                                    command=self.start_selection_countdown, width=30)
        self.select_btn.pack(pady=5)
        self.target_label = tk.Label(root, text="No window selected", fg="gray")
        self.target_label.pack(pady=5)

        tk.Frame(root, height=2, bd=1, relief="sunken").pack(fill="x", padx=20, pady=10)

        # Class/Skill Selector
        tk.Label(root, text="Step 2: Select Class Mode").pack(pady=(5, 5))
        self.class_var = tk.StringVar(value="Archmage")
        self.class_combo = ttk.Combobox(root, textvariable=self.class_var)
        self.class_combo['values'] = list(skill_configs.keys())
        self.class_combo.pack(pady=5)
        self.class_combo.bind("<<ComboboxSelected>>", self.on_class_change)

        # Status Label
        self.status_label = tk.Label(root, text="Status: Stopped", fg="red", font=("Helvetica", 10, "bold"))
        self.status_label.pack(pady=20)

        # Start/Stop Buttons
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=10)

        self.start_btn = tk.Button(btn_frame, text="START BOT", bg="green", fg="white", width=15, 
                                   command=self.start_bot, state=tk.DISABLED)
        self.start_btn.pack(side=tk.LEFT, padx=10)

        self.stop_btn = tk.Button(btn_frame, text="STOP", bg="red", fg="white", width=15, 
                                  command=self.stop_bot, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=10)

        # Log/Info area
        self.log_text = tk.Text(root, height=5, width=45, state=tk.DISABLED)
        self.log_text.pack(pady=10)

        # Initialize schedule
        schedule.every(2).minutes.do(self.turn_in_quest)

    def log(self, message):
        """Helper to print to the GUI log"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def on_class_change(self, event=None):
        mode = self.class_var.get()
        if self.running:
            self.stop_bot()
            self.log(f"Class changed to {mode}. Bot stopped.")
        else:
            self.log(f"Switched mode to: {mode}")

    # --- Window Selection Logic ---
    def start_selection_countdown(self):
        self.select_btn.config(state=tk.DISABLED)
        self.countdown_step(3)

    def countdown_step(self, count):
        if count > 0:
            self.select_btn.config(text=f"Click Game Window Now! ({count})")
            # Schedule next step in 1 second
            self.root.after(1000, self.countdown_step, count - 1)
        else:
            self.capture_active_window()

    def capture_active_window(self):
        try:
            # Grab whatever window is currently active
            window = pygetwindow.getActiveWindow()
            if window:
                self.target_window = window
                self.target_handle = window._hWnd
                
                title_display = window.title if window.title else "Untitled Window"
                self.target_label.config(text=f"Selected: {title_display}\nHandle: {self.target_handle}", fg="blue")
                self.select_btn.config(text="Select Active Window (3s Delay)", state=tk.NORMAL)
                self.start_btn.config(state=tk.NORMAL) # Enable start button now
                self.log(f"Window captured: {title_display}")
            else:
                self.log("Failed to capture window.")
                self.select_btn.config(text="Retry Selection", state=tk.NORMAL)
        except Exception as e:
            self.log(f"Selection Error: {e}")
            self.select_btn.config(text="Retry Selection", state=tk.NORMAL)

    # --- Bot Logic ---
    def start_bot(self):
        if self.running: return
        if not self.target_handle:
            messagebox.showerror("Error", "Please select a target window first.")
            return

        self.running = True
        self.start_btn.config(state=tk.DISABLED)
        self.select_btn.config(state=tk.DISABLED) # Lock selection while running
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="Status: RUNNING", fg="green")
        
        # Reset timestamps
        mode = self.class_var.get()
        self.current_config = skill_configs[mode]
        self.last_used_timestamps = {skill: 0 for skill in self.current_config}
        self.log(f"Started bot with class: {mode}")
        # Start Thread
        self.bot_thread = threading.Thread(target=self.bot_loop, daemon=True)
        self.bot_thread.start()

    def stop_bot(self):
        self.running = False
        self.start_btn.config(state=tk.NORMAL)
        self.select_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Status: Stopped", fg="red")
        self.log("Bot stopping...")

    def send_skill_input(self):
        current_time = time.time()
        skill_used = False

        for skill, cooldown in self.current_config.items():
            last_used = self.last_used_timestamps.get(skill, 0)
            if current_time - last_used >= cooldown:
                if skill_used: break
                skill_used = True
                
                try:
                    # Send inputs directly to the captured handle
                    win32gui.PostMessage(self.target_handle, win32con.WM_KEYDOWN, ord(skill_keys[skill]), 0)
                    win32gui.PostMessage(self.target_handle, win32con.WM_KEYUP, ord(skill_keys[skill]), 0)
                    self.last_used_timestamps[skill] = current_time

                    timestamp_str = datetime.now().strftime("%H:%M:%S")
                    self.log(f"[{timestamp_str}] Used {skill}")

                except Exception as e:
                    self.log(f"Input Error: {e}")
                42344
                time.sleep(random.uniform(0.1, 0.3))

    def turn_in_quest(self):
        if not self.running: return
        self.log("Turning in quests...")
        try:
            # Check if window still exists/is valid
            if not self.target_window.isActive:
                # Optional: Force focus if you want, but might be annoying
                # self.target_window.activate() 
                pass

            # Calculate absolute screen coordinates based on window position
            base_x = self.target_window.left
            base_y = self.target_window.top
            
            for coord in coordinates_quest:
                if not self.running: break
                abs_x = base_x + coord[0]
                abs_y = base_y + coord[1]
                
                pyautogui.click(abs_x, abs_y)
                time.sleep(QUEST_INTERVAL)
        except Exception as e:
            self.log(f"Quest Error: {e}")

    def bot_loop(self):
        while self.running:
            try:
                self.send_skill_input()
                schedule.run_pending()
                time.sleep(0.5) 
            except Exception as e:
                self.log(f"Loop Error: {e}")
                self.stop_bot()
                break

if __name__ == "__main__":
    root = tk.Tk()
    app = AQWBotApp(root)
    root.mainloop()