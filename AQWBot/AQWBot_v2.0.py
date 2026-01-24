import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import os
from datetime import datetime
from PIL import ImageStat # Needed for testing in UI

from BotModules.aqw_config import *
from BotModules.window_manager import WindowManager
from BotModules.bot_engine import BotEngine
from BotModules.ui_utils import SnippingTool

class AQWBotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AQW Bot v2.1 Text detection")
        self.root.geometry("700x780")
        
        # --- Modules ---
        self.cfg = ConfigManager()
        self.wm = WindowManager()
        self.bot = BotEngine(self.wm, self.log)
        
        # --- Data ---
        data = self.cfg.load_all()
        self.quest_data = data["quests"]
        self.class_data = data["classes"]
        self.bot.skill_locations = data["skills"]
        self.bot.drop_list = data["drops"]
        self.bot.drop_ui = data["drop_ui"]
        
        # --- UI Setup ---
        self.setup_ui()

    def setup_ui(self):
        # Target Header
        top = tk.Frame(self.root, relief="groove", bd=2)
        top.pack(fill="x", padx=10, pady=10)
        tk.Label(top, text="Target:").pack(side=tk.LEFT, padx=5)
        self.lbl_target = tk.Label(top, text="None", fg="red")
        self.lbl_target.pack(side=tk.LEFT)
        self.btn_sel = tk.Button(top, text="Select (3s)", command=self.select_target)
        self.btn_sel.pack(side=tk.RIGHT)

        # Tabs
        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(expand=True, fill="both", padx=10)
        
        # 1. Main Tab
        self.tab_main = tk.Frame(self.tabs); self.tabs.add(self.tab_main, text="Controls")
        self.ui_main_tab()
        
        # 2. Class Editor
        self.tab_class = tk.Frame(self.tabs); self.tabs.add(self.tab_class, text="Classes")
        self.ui_class_tab()
        
        # 3. Locations
        self.tab_loc = tk.Frame(self.tabs); self.tabs.add(self.tab_loc, text="Locations")
        self.ui_loc_tab()
        
        # 4. Drops
        self.tab_drop = tk.Frame(self.tabs); self.tabs.add(self.tab_drop, text="Drops")
        self.ui_drop_tab()
        
        # 5. Quests
        self.tab_quest = tk.Frame(self.tabs); self.tabs.add(self.tab_quest, text="Quests")
        self.ui_quest_tab()

        # Log
        self.log_text = tk.Text(self.root, height=8, state=tk.DISABLED)
        self.log_text.pack(fill="x", padx=10, pady=10)

    # --- UI Builders ---
    def ui_main_tab(self):
        f = tk.Frame(self.tab_main, padx=20, pady=20); f.pack(fill="both")
        
        tk.Label(f, text="Class:").pack(anchor="w")
        self.cb_class = ttk.Combobox(f, values=list(self.class_data.keys()), state="readonly")
        self.cb_class.pack(fill="x", pady=5)
        if self.class_data: self.cb_class.current(0)
        
        tk.Label(f, text="Quest:").pack(anchor="w")
        self.cb_quest = ttk.Combobox(f, values=list(self.quest_data.keys()), state="readonly")
        self.cb_quest.pack(fill="x", pady=5)
        if self.quest_data: self.cb_quest.current(0)
        
        self.var_q_en = tk.BooleanVar(value=True)
        tk.Checkbutton(f, text="Enable Quests", variable=self.var_q_en).pack(anchor="w")
        
        self.var_d_en = tk.BooleanVar(value=True)
        tk.Checkbutton(f, text="Enable Drops", variable=self.var_d_en).pack(anchor="w")
        
        self.lbl_status = tk.Label(f, text="STOPPED", fg="red", font=("Arial", 14))
        self.lbl_status.pack(pady=20)
        
        tk.Button(f, text="START", bg="green", fg="white",width=12, height=2, command=self.start).pack(side=tk.LEFT, padx=10)
        tk.Button(f, text="STOP", bg="red", fg="white",width=12, height=2, command=self.stop).pack(side=tk.LEFT, padx=10)

    def ui_class_tab(self):
        f = tk.Frame(self.tab_class, padx=20, pady=20); f.pack(fill="both")
        
        top = tk.Frame(f); top.pack(fill="x")
        self.cb_edit_class = ttk.Combobox(top, values=list(self.class_data.keys()), state="readonly")
        self.cb_edit_class.pack(side=tk.LEFT, expand=True, fill="x")
        self.cb_edit_class.bind("<<ComboboxSelected>>", self.load_class_data)
        
        tk.Button(top, text="+", width=3, command=self.add_class).pack(side=tk.RIGHT)
        tk.Button(top, text="-", width=3, command=self.del_class).pack(side=tk.RIGHT)
        
        self.class_vars = {}
        grid = tk.Frame(f, pady=10); grid.pack(fill="x")
        
        for i, skill in enumerate(REQUIRED_SKILLS):
            tk.Label(grid, text=skill).grid(row=i, column=0)
            use = tk.BooleanVar(value=True)
            tk.Checkbutton(grid, variable=use).grid(row=i, column=1)
            cd = tk.DoubleVar(value=2.5)
            tk.Entry(grid, textvariable=cd, width=5).grid(row=i, column=2)
            self.class_vars[skill] = {"use": use, "cd": cd}
        
        tk.Button(f, text="Save", command=self.save_class).pack(fill="x", pady=10)
        if self.class_data: self.cb_edit_class.current(0); self.load_class_data()

    def ui_loc_tab(self):
        f = tk.Frame(self.tab_loc, padx=20, pady=20); f.pack(fill="both")
        self.loc_lbls = {}
        self.loc_btns = {}
        for skill in REQUIRED_SKILLS:
            row = tk.Frame(f); row.pack(fill="x", pady=2)
            tk.Label(row, text=skill, width=10).pack(side=tk.LEFT)
            lbl = tk.Label(row, text=str(self.bot.skill_locations.get(skill, "Not Set")), fg="blue")
            lbl.pack(side=tk.LEFT, padx=10)
            self.loc_lbls[skill] = lbl
            btn = tk.Button(row, text="Rec", command=lambda s=skill: self.rec_loc(s))
            btn.pack(side=tk.RIGHT)
            self.loc_btns[skill] = btn

    def ui_drop_tab(self):
        f = tk.Frame(self.tab_drop, padx=10, pady=10)
        f.pack(fill="both")
        
        setup_frame = tk.LabelFrame(f, text="1. Fixed Slot Setup", padx=5, pady=5)
        setup_frame.pack(fill="x", pady=5)
        
        tk.Label(setup_frame, text="Setup for the BOTTOM drop slot.", fg="gray").pack()
        # Row 1: ROI
        r1 = tk.Frame(setup_frame); r1.pack(fill="x", pady=2)
        tk.Label(r1, text="1. Scan Area (ROI):").pack(side=tk.LEFT)
        self.lbl_roi = tk.Label(r1, text=str(self.bot.drop_ui.get("roi", "Not Set")), fg="blue")
        self.lbl_roi.pack(side=tk.LEFT, padx=5)
        tk.Button(r1, text="Set (TL -> BR)", command=self.set_drop_roi).pack(side=tk.RIGHT)

        # Row 2: Sensitivity (Threshold)
        r2 = tk.Frame(setup_frame); r2.pack(fill="x", pady=5)
        tk.Label(r2, text="2. Text Sensitivity:").pack(side=tk.LEFT)
        self.var_thresh = tk.DoubleVar(value=self.bot.drop_ui.get("threshold", 15.0))
        tk.Entry(r2, textvariable=self.var_thresh, width=5).pack(side=tk.LEFT, padx=5)
        tk.Button(r2, text="Test Detection Now", command=self.test_text_detection).pack(side=tk.RIGHT)
        tk.Button(r2, text="Save Thresh", command=self.save_thresh).pack(side=tk.RIGHT, padx=5)

        # Row 3: Buttons
        r3 = tk.Frame(setup_frame); r3.pack(fill="x", pady=5)
        tk.Button(r3, text="3. Rec Accept Click", command=self.rec_accept_pt).pack(side=tk.LEFT, fill="x", expand=True, padx=2)
        tk.Button(r3, text="4. Rec Decline Click", command=self.rec_decline_pt).pack(side=tk.LEFT, fill="x", expand=True, padx=2)
        
        self.lbl_btns_status = tk.Label(setup_frame, text=f"Acc:{self.bot.drop_ui.get('accept')} | Dec:{self.bot.drop_ui.get('decline')}")
        self.lbl_btns_status.pack(fill="x")

        # Drop List
        list_frame = tk.LabelFrame(f, text="Wanted Items", padx=5, pady=5)
        list_frame.pack(fill="both", expand=True, pady=5)
        
        self.lst_drops = tk.Listbox(list_frame, height=6)
        self.lst_drops.pack(fill="both", expand=True)
        self.refresh_drops()
        
        tk.Button(list_frame, text="Add Item Text Image (Cap)", command=self.add_drop).pack(fill="x", pady=5)
        tk.Button(list_frame, text="Remove Selected", command=self.rem_drop).pack(fill="x")

    def test_text_detection(self):
        roi = self.bot.drop_ui.get("roi")
        if not roi:
            self.log("ROI not set!")
            return
        
        img = self.wm.capture_client_area()
        if img:
            crop_box = (roi[0], roi[1], roi[2], roi[3])
            roi_img = img.crop(crop_box).convert('L')
            stats = ImageStat.Stat(roi_img)
            score = stats.stddev[0]
            thresh = self.var_thresh.get()
            
            res = "TEXT DETECTED" if score > thresh else "EMPTY"
            self.log(f"Score: {score:.2f} (Thresh: {thresh}) -> {res}")

    def save_thresh(self):
        self.bot.drop_ui["threshold"] = self.var_thresh.get()
        self.cfg.save_json(DROP_UI_FILE, self.bot.drop_ui)
        self.log(f"Threshold saved: {self.var_thresh.get()}")

    def set_drop_roi(self):
        self.log("Click TOP-LEFT of the Bottom Slot in 3s...")
        self.root.after(3000, lambda: self._rec_roi_step(1))

    def _rec_roi_step(self, step):
        pt = self.wm.get_mouse_client_coords()
        if step == 1:
            self.temp_roi = [pt[0], pt[1], 0, 0]
            self.log("Recorded TL. Click BOTTOM-RIGHT in 3s...")
            self.root.after(3000, lambda: self._rec_roi_step(2))
        else:
            self.temp_roi[2] = pt[0]
            self.temp_roi[3] = pt[1]
            self.bot.drop_ui["roi"] = self.temp_roi
            self.cfg.save_json(DROP_UI_FILE, self.bot.drop_ui)
            self.lbl_roi.config(text=str(self.temp_roi))
            self.log("ROI Saved.")

    def rec_accept_pt(self):
        self.log("Hover & Click where ACCEPT button appears (3s)...")
        self.root.after(3000, lambda: self._save_btn_pt("accept"))

    def rec_decline_pt(self):
        self.log("Hover & Click where DECLINE button appears (3s)...")
        self.root.after(3000, lambda: self._save_btn_pt("decline"))

    def _save_btn_pt(self, key):
        pt = self.wm.get_mouse_client_coords()
        self.bot.drop_ui[key] = [pt[0], pt[1]]
        self.cfg.save_json(DROP_UI_FILE, self.bot.drop_ui)
        self.lbl_btns_status.config(text=f"Acc:{self.bot.drop_ui.get('accept')} | Dec:{self.bot.drop_ui.get('decline')}")
        self.log(f"{key} pos saved.")

    def ui_quest_tab(self):
        f = tk.Frame(self.tab_quest, padx=10, pady=10); f.pack(fill="both")
        
        top = tk.Frame(f); top.pack(fill="x")
        self.cb_edit_quest = ttk.Combobox(top, values=list(self.quest_data.keys()), state="readonly")
        self.cb_edit_quest.pack(side=tk.LEFT, expand=True, fill="x")
        self.cb_edit_quest.bind("<<ComboboxSelected>>", self.load_quest_data)
        tk.Button(top, text="+", width=3, command=self.add_quest).pack(side=tk.RIGHT)
        tk.Button(top, text="-", width=3, command=self.del_quest).pack(side=tk.RIGHT)
        
        self.q_int = tk.DoubleVar(value=2.0)
        tk.Entry(f, textvariable=self.q_int).pack(fill="x", pady=5)
        
        self.lst_qpts = tk.Listbox(f, height=6); self.lst_qpts.pack(fill="both", pady=5)
        
        tk.Button(f, text="Capture Point", command=self.rec_qpt).pack(fill="x")
        tk.Button(f, text="Remove Point", command=self.rem_qpt).pack(fill="x")
        tk.Button(f, text="Save", command=self.save_quest).pack(fill="x", pady=5)
        if self.quest_data: self.cb_edit_quest.current(0); self.load_quest_data()

    # --- Actions ---
    def log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{ts}] {msg}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def select_target(self):
        self.btn_sel.config(text="Wait (3)")
        self.root.after(3000, self._do_select)

    def _do_select(self):
        handle, title = self.wm.find_target_window()
        self.lbl_target.config(text=f"{title[:15]} ({handle})", fg="green" if handle else "red")
        self.btn_sel.config(text="Select (3s)")
        self.log(f"Selected: {title}")

    def start(self):
        if not self.wm.target_handle: return messagebox.showerror("Err", "No Target")
        cname = self.cb_class.get()
        qname = self.cb_quest.get()
        
        self.bot.active_class_config = self.class_data[cname]
        self.bot.active_quest_config = self.quest_data[qname]
        self.bot.enable_quests = self.var_q_en.get()
        self.bot.enable_drops = self.var_d_en.get()
        self.bot.drop_ui["threshold"] = self.var_thresh.get() # Sync UI thresh to bot

        self.bot.start()
        self.lbl_status.config(text="RUNNING", fg="green")

    def stop(self):
        self.bot.stop()
        self.lbl_status.config(text="STOPPED", fg="red")

    # --- Wrappers for Class/Quest/Drop Editing ---
    # (Simplified versions of previous logic using helper methods)
    def load_class_data(self, e=None):
        data = self.class_data[self.cb_edit_class.get()]
        for k, v in self.class_vars.items():
            v["use"].set(data[k]["use"])
            v["cd"].set(data[k]["cd"])

    def save_class(self):
        name = self.cb_edit_class.get()
        new_d = {k: {"use": v["use"].get(), "cd": v["cd"].get()} for k,v in self.class_vars.items()}
        self.class_data[name] = new_d
        self.cfg.save_json(CLASS_CONFIG_FILE, self.class_data)
        self.log("Class Saved")

    def add_class(self):
        n = simpledialog.askstring("New", "Name:")
        if n and n not in self.class_data:
            self.class_data[n] = DEFAULT_CLASSES["Archmage"]
            self.cb_class['values'] = list(self.class_data.keys())
            self.cb_edit_class['values'] = list(self.class_data.keys())

    def del_class(self):
        del self.class_data[self.cb_edit_class.get()]
        self.cb_class['values'] = list(self.class_data.keys())
        self.cb_edit_class['values'] = list(self.class_data.keys())
        self.cb_edit_class.current(0)
        self.load_class_data()

    def rec_loc(self, skill):
        self.loc_btns[skill].config(text="Wait (3)")
        self.root.after(3000, lambda: self._do_rec_loc(skill))

    def _do_rec_loc(self, skill):
        self.bot.skill_locations[skill] = self.wm.get_mouse_client_coords()
        self.cfg.save_json(SKILL_LOC_FILE, self.bot.skill_locations)
        self.loc_lbls[skill].config(text=str(self.bot.skill_locations[skill]))
        self.loc_btns[skill].config(text="Rec")

    def refresh_drops(self):
        self.lst_drops.delete(0, tk.END)
        for k,v in self.bot.drop_list.items(): self.lst_drops.insert(tk.END, f"{k}: {v}")

    def add_drop(self):
        self.log("Capture in 3s...")
        self.root.after(3000, self._do_drop_cap)

    def _do_drop_cap(self):
        img = self.wm.capture_client_area()
        if img: SnippingTool(self.root, img, self._save_drop)

    def _save_drop(self, img):
        name = simpledialog.askstring("Name", "Drop Name:")
        if name:
            path = os.path.join(DROPS_DIR, f"{name}.png")
            img.save(path)
            self.bot.drop_list[name] = path
            self.cfg.save_json(DROP_CONFIG_FILE, self.bot.drop_list)
            self.refresh_drops()

    def rem_drop(self):
        sel = self.lst_drops.curselection()
        if sel:
            key = self.lst_drops.get(sel[0]).split(":")[0]
            del self.bot.drop_list[key]
            self.cfg.save_json(DROP_CONFIG_FILE, self.bot.drop_list)
            self.refresh_drops()

    def load_quest_data(self, e=None):
        d = self.quest_data[self.cb_edit_quest.get()]
        self.q_int.set(d["interval_minutes"])
        self.lst_qpts.delete(0, tk.END)
        for p in d["coordinates"]: self.lst_qpts.insert(tk.END, str(p))

    def save_quest(self):
        n = self.cb_edit_quest.get()
        self.quest_data[n]["interval_minutes"] = self.q_int.get()
        self.cfg.save_json(QUEST_CONFIG_FILE, self.quest_data)
        self.log("Quest Saved")

    def add_quest(self):
        n = simpledialog.askstring("New", "Name:")
        if n and n not in self.quest_data:
            self.quest_data[n] = {"interval_minutes":2.0, "coordinates":[]}
            self.cb_quest['values'] = list(self.quest_data.keys())
            self.cb_edit_quest['values'] = list(self.quest_data.keys())

    def del_quest(self):
        del self.quest_data[self.cb_edit_quest.get()]
        self.cb_quest['values'] = list(self.quest_data.keys())
        self.cb_edit_quest['values'] = list(self.quest_data.keys())
        self.cb_edit_quest.current(0)
        self.load_quest_data()

    def rec_qpt(self):
        self.root.after(3000, self._do_rec_qpt)

    def _do_rec_qpt(self):
        pt = self.wm.get_mouse_client_coords()
        self.quest_data[self.cb_edit_quest.get()]["coordinates"].append(pt)
        self.load_quest_data()

    def rem_qpt(self):
        sel = self.lst_qpts.curselection()
        if sel:
            del self.quest_data[self.cb_edit_quest.get()]["coordinates"][sel[0]]
            self.load_quest_data()

if __name__ == "__main__":
    root = tk.Tk()
    app = AQWBotApp(root)
    root.mainloop()