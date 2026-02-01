from pynput import keyboard
from typing import Callable, Dict, Optional

class HotkeyManager:
    def __init__(self):
        self.listener = None
        self.hotkeys: Dict[str, Callable] = {}

    def start(self, key_map: Dict[str, Callable]):
        """
        Starts the GlobalHotKeys listener.
        
        Args:
            key_map: Dictionary mapping key strings to callback functions.
                     Example: {'<ctrl>+<shift>+p': my_func, '<f8>': other_func}
        """
        self.stop() # Ensure clean restart
        
        # Pynput expects format like: '<ctrl>+<alt>+h'
        # We need to normalize our stored keys to this format if they aren't already.
        # For MVP, we'll assume the inputs are cleaner or use a helper.
        
        normalized_map = {}
        for k, v in key_map.items():
            normalized = self._normalize_key(k)
            if normalized:
                normalized_map[normalized] = v
                
        if not normalized_map:
            return

        print(f"Starting Hotkey Listener with: {normalized_map.keys()}")
        self.listener = keyboard.GlobalHotKeys(normalized_map)
        self.listener.start()

    def stop(self):
        if self.listener:
            try:
                self.listener.stop()
            except: 
                pass
            self.listener = None

    def _normalize_key(self, key_str: str) -> Optional[str]:
        """
        Converts user-friendly key strings to pynput format.
        Examples:
        - "f8" -> "<f8>"
        - "CTRL + SHIFT + ALT + R" -> "<ctrl>+<shift>+<alt>+r"
        """
        if not key_str: return None
        
        key_str = key_str.lower().strip()
        
        # Simple single keys (f8, a, 1)
        if "+" not in key_str and " " not in key_str:
            if len(key_str) > 1: return f"<{key_str}>" # e.g. <f8>, <esc> 
            return key_str # e.g. a
            
        # Complex combos
        parts = [p.strip() for p in key_str.split("+")]
        formatted = []
        for p in parts:
            if p in ["ctrl", "shift", "alt", "cmd", "win"]:
                formatted.append(f"<{p}>")
            elif len(p) > 1: # f8, esc
                formatted.append(f"<{p}>")
            else:
                formatted.append(p)
                
        return "+".join(formatted)
