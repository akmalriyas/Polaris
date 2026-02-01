import time
import threading
from pynput import mouse, keyboard
from typing import List, Dict, Any

class Player:
    def __init__(self):
        self.mouse_controller = mouse.Controller()
        self.keyboard_controller = keyboard.Controller()
        self.playing = False
        self.safety_triggered = False
        
        # Tripwire listener
        self.safety_listener = None

    def _safety_check(self, x, y):
        """Callback for the safety tripwire."""
        # Note: This is a very sensitive tripwire. 
        # Any manual movement stops playback.
        # We might need to handle the fact that our OWN playback moves the mouse.
        # pynput listeners pick up programmatic moves too unless we filter them.
        # For simplicity in MVP, we might rely on a keyboard kill switch (ESC) or 
        # check if the position deviates significantly from expected.
        # But `pynput` listener usually triggers on synthetic events too.
        # A common workaround is to disable the tripwire for movement, 
        # or check a specific "Stop" key globally.
        pass

    def play(self, data: Dict[str, Any], speed: float = 1.0):
        """
        Replays the recorded macro.
        
        Args:
            data: The full macro data including 'flow' list.
            speed: Playback speed multiplier (1.0 = normal).
        """
        self.playing = True
        self.safety_triggered = False
        events = data.get("flow", [])
        
        print(f"Starting playback of {len(events)} events...")
        
        # Safety: We can also listen for a specific key effectively to abort
        # For MVP, let's rely on the UI 'Stop' or a global hotkey if valid
        
        for event in events:
            if not self.playing:
                print("Playback stopped manually.")
                break
                
            # Apply delay
            delay = event.get("delay", 0)
            if delay > 0:
                time.sleep(delay / speed)
            
            action = event.get("action")
            
            if action == "mouse_move":
                coords = event.get("coords")
                if coords:
                    self.mouse_controller.position = tuple(coords)
                    
            elif action == "mouse_click":
                button_str = event.get("button")
                pressed = event.get("pressed")
                # Parse button string back to enum
                btn = mouse.Button.left
                if "right" in button_str: btn = mouse.Button.right
                elif "middle" in button_str: btn = mouse.Button.middle
                
                if pressed:
                    self.mouse_controller.press(btn)
                else:
                    self.mouse_controller.release(btn)
                    
            elif action == "mouse_scroll":
                dx = event.get("dx", 0)
                dy = event.get("dy", 0)
                self.mouse_controller.scroll(dx, dy)
                
            elif action == "key_press":
                key_str = event.get("key")
                key = self._parse_key(key_str)
                if key:
                    self.keyboard_controller.press(key)
                    
            elif action == "key_release":
                key_str = event.get("key")
                key = self._parse_key(key_str)
                if key:
                    self.keyboard_controller.release(key)
                    
        self.playing = False
        print("Playback finished.")

    def stop(self):
        """Forces playback to stop."""
        self.playing = False

    def _parse_key(self, key_str: str):
        """Helper to convert string back to Key object or char."""
        if key_str is None:
            return None
        # If it looks like 'Key.enter', we need to map it to the actual Key enum
        if key_str.startswith("Key."):
            try:
                # Reflection to get the attribute from pynput.keyboard.Key
                attr = key_str.split(".")[1]
                return getattr(keyboard.Key, attr)
            except AttributeError:
                return None
        return key_str
