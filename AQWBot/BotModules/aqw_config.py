import json
import os

# --- Constants ---
QUEST_CONFIG_FILE = "quest_configs.json"
SKILL_LOC_FILE = "skill_locations.json"
CLASS_CONFIG_FILE = "class_configs.json"
DROP_CONFIG_FILE = "drop_configs.json"
DROP_UI_FILE = "drop_ui_layout.json"
DROPS_DIR = "drops_images"

REQUIRED_SKILLS = ["auto", "skill1", "skill2", "skill3", "skill4"]

if not os.path.exists(DROPS_DIR):
    os.makedirs(DROPS_DIR)

# --- Defaults ---
DEFAULT_QUESTS = {
    "Default Quest": {
        "interval_minutes": 2.0,
        "coordinates": [] 
    }
}

DEFAULT_CLASSES = {
    "Archmage": {
        "auto": {"cd": 2.5, "use": False},
        "skill1": {"cd": 2.5, "use": True},
        "skill2": {"cd": 2.5, "use": True},
        "skill3": {"cd": 2.5, "use": True},
        "skill4": {"cd": 2.5, "use": True}
    },
    "VHL": {
        "auto": {"cd": 2.0, "use": True},
        "skill1": {"cd": 3.0, "use": True},
        "skill2": {"cd": 3.0, "use": True},
        "skill3": {"cd": 3.0, "use": True},
        "skill4": {"cd": 9.0, "use": True}
    }
}

class ConfigManager:
    @staticmethod
    def load_json(filename, default):
        if os.path.exists(filename):
            try:
                with open(filename, "r") as f:
                    return json.load(f)
            except:
                return default.copy()
        return default.copy()

    @staticmethod
    def save_json(filename, data):
        try:
            with open(filename, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error saving {filename}: {e}")

    def load_all(self):
        return {
            "quests": self.load_json(QUEST_CONFIG_FILE, DEFAULT_QUESTS),
            "classes": self.load_json(CLASS_CONFIG_FILE, DEFAULT_CLASSES),
            "skills": self.load_json(SKILL_LOC_FILE, {}),
            "drops": self.load_json(DROP_CONFIG_FILE, {}),
            # Updated UI Layout config
            "drop_ui": self.load_json(DROP_UI_FILE, {
                "roi": None,      # [x1, y1, x2, y2]
                "accept": None,   # [x, y]
                "decline": None,  # [x, y]
                "threshold": 15.0   # Variance threshold to detect text
            })
        }