import random
import time
import pyautogui, pygetwindow

# Print the list of window titles
target_window = pygetwindow.getWindowsWithTitle("")[8]

#while True:
#    cursor_x, cursor_y = pyautogui.position()
#    relative_x = cursor_x - target_window.left
#    relative_y = cursor_y - target_window.top
#
#    print(f"Cursor position relative to AQW: ({relative_x}, {relative_y})")
#
#    # Add a delay to avoid high CPU usage
#    time.sleep(1)
print("Press Ctrl+C to finish bot\n\n")
time.sleep(2)
screen_width=3440;
y_coord=570
skill_xcoords={
    "skill1":470+screen_width,
    "skill2":520+screen_width,
    "skill3":565+screen_width,
    "skill4":610+screen_width,  
      }
skill_cooldowns={
    "skill1":3,
    "skill2":2.5,
    #"skill3":6,
    #"skill4":12,
    }

states={
    1:"Idle",
    2:"Running",
    3:"Finished"
    }
# Dictionary to store the timestamps when each skill was last used
last_used_timestamps = {skill: 0 for skill in skill_cooldowns}
while True:
    
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
                    # Example: pyautogui.press("1") for Skill1
                    x_cord=skill_xcoords[skill]
                    print(f"Using {skill} at coords: x={x_cord},y={y_coord}")
                    pyautogui.click(x=x_cord, y=y_coord)  # move to skill coordinates then click the left mouse button.
                    time.sleep(random.uniform(0.1, 0.5))  # Introduce a small delay to simulate human input

                    # Update the last used timestamp for the skill
                    last_used_timestamps[skill] = current_time
    
            # Sleep for a short interval to reduce CPU usage
            time.sleep(1)
    except KeyboardInterrupt:
        print('Bot finished')
