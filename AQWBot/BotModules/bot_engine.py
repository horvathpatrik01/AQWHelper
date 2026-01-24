import threading
import time
import random
import os
import pyautogui
from PIL import ImageStat 
from BotModules.aqw_config import REQUIRED_SKILLS


class BotEngine:
    def __init__(self, window_manager, log_callback):
        self.wm = window_manager
        self.log = log_callback
        self.running = False
        self.thread = None
        
        self.last_skill_timestamps = {k:0 for k in REQUIRED_SKILLS}
        self.last_quest_time = 0
        self.last_drop_scan = 0
        
        # Current active configs (set by main.py)
        self.active_class_config = {}
        self.active_quest_config = {}
        self.skill_locations = {}
        self.drop_list = {}
        self.drop_ui = {}
        
        self.enable_quests = True
        self.enable_drops = True

    def start(self):
        if self.running: return
        self.running = True
        self.last_skill_timestamps = {k:0 for k in REQUIRED_SKILLS}
        self.last_quest_time = time.time()
        self.thread = threading.Thread(target=self.loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def loop(self):
        while self.running:
            try:
                now = time.time()
                
                # 1. Skills
                for skill_name in REQUIRED_SKILLS:
                    if not self.running: break
                    cfg = self.active_class_config.get(skill_name, {})
                    if not cfg.get("use", True): continue
                    
                    if now - self.last_skill_timestamps.get(skill_name, 0) >= cfg.get("cd", 2.5):
                        if skill_name in self.skill_locations:
                            loc = self.skill_locations[skill_name]
                            self.wm.send_background_click(loc[0], loc[1])
                            self.last_skill_timestamps[skill_name] = now
                            self.log(f"Skill: {skill_name}")
                            break
                
                # 2. Drops
                if self.enable_drops and (now - self.last_drop_scan > 2.0):
                    self.scan_drops_text_detection()
                    self.last_drop_scan = time.time()

                # 3. Quests
                if self.enable_quests:
                    interval = self.active_quest_config.get("interval_minutes", 2) * 60
                    if now - self.last_quest_time >= interval:
                        self.run_quest_turnin()
                        self.last_quest_time = time.time()

                time.sleep(0.8)
            except Exception as e:
                self.log(f"Error in loop: {e}")
                self.stop()

    def scan_drops_text_detection(self):
        roi = self.drop_ui.get("roi")     # [x1, y1, x2, y2]
        acc = self.drop_ui.get("accept")  # [x, y]
        dec = self.drop_ui.get("decline") # [x, y]
        threshold = self.drop_ui.get("threshold", 15.0)

        if not (roi and acc and dec):
            return


        screen = self.wm.capture_client_area()
        if not screen: return

        try:
            # 1. Check ROI for "Text Presence" (Variance/Contrast)
            crop_box = (roi[0], roi[1], roi[2], roi[3])
            roi_img = screen.crop(crop_box).convert('L') # Convert to Grayscale

            # Calculate Standard Deviation (Contrast)
            stats = ImageStat.Stat(roi_img)
            variance = stats.stddev[0]

            # If variance is low (e.g. < 15), it's likely an empty/blurry background
            if variance < threshold:
                return # Slot is empty, do nothing.

            # 2. Text Detected! Is it what we want?
            found_wanted = False
            
            # Search for specific item names in the original color image
            # --- THE FIX: Padded Search Area ---
            # We create a "Haystack" that is the ROI + 20 pixels padding.
            # This fixes the "Needle exceed Haystack" crash because the search area 
            # is now guaranteed to be larger than the item text image, 
            # but still localized to the bottom slot.
            
            padding = 20
            s_x1 = max(0, roi[0] - padding)
            s_y1 = max(0, roi[1] - padding)
            s_x2 = min(screen.width, roi[2] + padding)
            s_y2 = min(screen.height, roi[3] + padding)
            
            # Crop the "Padded" area from the screen
            search_haystack = screen.crop((s_x1, s_y1, s_x2, s_y2))

            for name, path in self.drop_list.items():
                if not os.path.exists(path): continue
                if pyautogui.locate(path, search_haystack, confidence=0.8):
                    found_wanted = True
                    self.log(f"Matched Item: {name}")
                    break

            if found_wanted:
                self.wm.send_background_click(acc[0], acc[1])
                self.log(f"Accepted (Var:{int(variance)})")
            else:
                self.wm.send_background_click(dec[0], dec[1])
                self.log(f"Trashed Unknown (Var:{int(variance)})")
                
            time.sleep(0.1)

        except Exception as e:
            self.log(f"Drop Scan Error: {e}")
            pass

    def run_quest_turnin(self):
        self.log("Quest Turn-in...")
        for pt in self.active_quest_config.get("coordinates", []):
            if not self.running: break
            self.wm.send_background_click(pt[0], pt[1])
            time.sleep(1)

