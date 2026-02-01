import json
import os
from typing import Dict, Any

SETTINGS_FILE = "settings.json"
DEFAULT_SETTINGS = {
    "rec_key": "f8",            # Stop/Record Toggle (simplified for now as Stop)
    "play_key": "f12",
    "rec_preset": "F8",         # Helper for UI
    "play_preset": "F12",       # Helper for UI
    "theme": "Dark",
    "accent_color": "blue",
    "transparency": 0.8,
    "show_overlay": True,
    "loop_mode": "once",        # "once", "count", "infinite"
    "loop_count": 3,            # Number of loops when mode is "count"
    "webhook_url": "",
    "webhook_enabled": False
}

def load_settings() -> Dict[str, Any]:
    if not os.path.exists(SETTINGS_FILE):
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()
    
    try:
        with open(SETTINGS_FILE, 'r') as f:
            data = json.load(f)
            # Merge with defaults
            settings = DEFAULT_SETTINGS.copy()
            settings.update(data)
            return settings
    except Exception:
        return DEFAULT_SETTINGS.copy()

def save_settings(settings: Dict[str, Any]) -> None:
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        print(f"Failed to save settings: {e}")
