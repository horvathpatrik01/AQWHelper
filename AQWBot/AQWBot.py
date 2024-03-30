import random
import time
import pyautogui, pygetwindow
import win32gui, win32con
import schedule

skill_keys={
    "auto":'1',
    "skill1":'2',
    "skill2":'3',
    "skill3":'4',
    "skill4":'5',  
      }

# Change skill cooldown's and priority here
#skill_cooldowns={
#    "skill4":9,
 #   "skill2":3,
  #  "skill3":3,
   # "skill1":3,
    #}

# archmage solo farm
archmage_skill_cooldowns={
    "skill3":2.5,
    #"skill4":10,
    "skill2":2.5,
    "skill1":2.5,
    }

# vhl solo farm
vhl_skill_cooldowns={
    "skill4":9,
    "skill2":3,
    "skill3":3,
    "skill1":3,
    }

# loo solo farm
loo_skill_cooldowns={
    "skill4":2,
    "skill3":5,
    "skill2":7,
    "skill1":5,
    }

def sendSkillInput():
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
            time.sleep(random.uniform(0.1, 0.3))  # Introduce a small delay to simulate human input
            # Update the last used timestamp for the skill
            last_used_timestamps[skill] = current_time

# Works with the default size of the application      
coordinates_quest = [(360,340), (385,920), (1085,610), (850,700)]
#Adjust if the quest doesn't load in time but should be enough
quest_interval=1
def turnInQuest():
    print("turning in quests")
    for coord in coordinates_quest:
        x=active_window.topleft[0] + coord[0]
        y=active_window.topleft[1] + coord[1]
        print("x: ",x," y: ",y)
        pyautogui.click(x,y)
        time.sleep(quest_interval)
        

for i in range(2):
        print(f"{3-i} seconds to get the window")
        time.sleep(1)
# Get the active window handle
active_window = pygetwindow.getActiveWindow()
active_window_handle = active_window._hWnd
if __name__=="__main__":

    # Schedule the function to run every 2 minutes
    schedule.every(2).minutes.do(turnInQuest)

    skill_cooldowns=archmage_skill_cooldowns
    # Dictionary to store the timestamps when each skill was last used
    last_used_timestamps = {skill: 0 for skill in skill_cooldowns}
    try:
        while True:
            sendSkillInput()
            # Sleep for a short interval to reduce CPU usage
            schedule.run_pending()
            time.sleep(1) 
    except KeyboardInterrupt:
        print('Bot finished')
