import random
import time
import pyautogui, pygetwindow
import win32gui, win32con

for i in range(2):
    print(f"{3-i} seconds to get the window")
    time.sleep(1)
    
# Get the active window handle
active_window = pygetwindow.getActiveWindow()
active_window_handle = active_window._hWnd


skill_keys={
    "auto":'1',
    "skill1":'2',
    "skill2":'3',
    "skill3":'4',
    "skill4":'5',  
      }

# Change skill cooldown's and priority here
skill_cooldowns={
    #"skill3":14,
    #"skill4":10,
    "skill2":2,
    "skill1":2.5,
    }
# Dictionary to store the timestamps when each skill was last used
last_used_timestamps = {skill: 0 for skill in skill_cooldowns}
try:
    while True:
        current_time=time.time()
        # Check skill cooldowns
        skillused=False
        for skill, cooldown in skill_cooldowns.items():
            last_used_time = last_used_timestamps[skill]
            time_elapsed = current_time - last_used_time
            if time_elapsed >= cooldown:
                # Skill cooldown is off; simulate keypress (you'll need to replace these with actual keypresses)
                if skillused:
                    break
                skillused=True
                # Simulate a keypress or mouse click to activate the skill
                # Replace the following line with code to press the appropriate keys
                print(f"Using {skill}")
                #pyautogui.press(skill_keys[skill])
                win32gui.SetActiveWindow(active_window_handle)
                win32gui.PostMessage(active_window_handle, win32con.WM_KEYDOWN, ord(skill_keys[skill]), 0)
                win32gui.PostMessage(active_window_handle, win32con.WM_KEYUP, ord(skill_keys[skill]), 0)
                time.sleep(random.uniform(0.1, 0.5))  # Introduce a small delay to simulate human input
                # Update the last used timestamp for the skill
                last_used_timestamps[skill] = current_time
                
        # Sleep for a short interval to reduce CPU usage
        time.sleep(1)
except KeyboardInterrupt:
    print('Bot finished')
