import time
import threading
from pynput import mouse, keyboard
from typing import List, Dict, Any, Optional

class Recorder:
    def __init__(self, stop_key: str = "f8", on_stop: Optional[callable] = None, blocked_keys: set = None):
        self.events: List[Dict[str, Any]] = []
        self.start_time: float = 0
        self.last_event_time: float = 0
        self.last_move_time: float = 0
        self.last_pos = (0, 0)
        self.recording: bool = False
        self.mouse_listener: Optional[mouse.Listener] = None
        self.keyboard_listener: Optional[keyboard.Listener] = None
        self.stop_key = stop_key
        self.on_stop = on_stop
        self.blocked_keys = blocked_keys or set()  # Keys to never record
        
        # We need a lock to prevent race conditions when appending events from multiple threads (mouse/kb)
        self.lock = threading.Lock()
    
    def _normalize_key(self, key) -> str:
        """Normalize a key to a simple string for comparison."""
        try:
            return key.char.lower() if key.char else ""
        except AttributeError:
            return key.name.lower() if hasattr(key, 'name') else str(key).lower().replace("key.", "")
    
    def _is_blocked(self, key) -> bool:
        """Check if a key is in the blocked set."""
        if not self.blocked_keys:
            return False
        normalized = self._normalize_key(key)
        return normalized in self.blocked_keys

    def start(self):
        """Starts the global listener."""
        self.events = []
        self.recording = True
        self.start_time = time.time()
        self.last_event_time = self.start_time
        self.last_move_time = self.start_time
        self.last_pos = mouse.Controller().position
        
        # Start listeners
        self.mouse_listener = mouse.Listener(
            on_move=self._on_move,
            on_click=self._on_click,
            on_scroll=self._on_scroll
        )
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        
        self.mouse_listener.start()
        self.keyboard_listener.start()
        print(f"Recorder started (Stop Key: {self.stop_key}).")

    def stop(self) -> List[Dict[str, Any]]:
        """Stops the listener and returns the recorded events."""
        self.recording = False
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None
            
        print(f"Recorder stopped. Captured {len(self.events)} events.")
        return self.events

    def _get_delay(self) -> float:
        """Calculates delay from the last event."""
        current_time = time.time()
        delay = current_time - self.last_event_time
        self.last_event_time = current_time
        return delay

    def _on_move(self, x, y):
        # Optimization: Only record if moved significant distance or enough time passed
        with self.lock:
            if not self.recording: return
            
            # Optimization: High fidelity (100Hz) for smooth playback
            # Only throttle slightly to avoid excessive CPU usage
            time_since_move = time.time() - self.last_move_time
            if time_since_move < 0.01:
                return

            self.last_pos = (x, y)
            self.last_move_time = time.time()
            
            self.events.append({
                "action": "mouse_move",
                "coords": (x, y),
                "delay": self._get_delay()
            })

    def _on_click(self, x, y, button, pressed):
        with self.lock:
            if not self.recording: return
            self.events.append({
                "action": "mouse_click",
                "coords": (x, y),
                "button": str(button),
                "pressed": pressed,
                "delay": self._get_delay()
            })

    def _on_scroll(self, x, y, dx, dy):
        with self.lock:
            if not self.recording: return
            self.events.append({
                "action": "mouse_scroll",
                "coords": (x, y),
                "dx": dx,
                "dy": dy,
                "delay": self._get_delay()
            })

    def _on_press(self, key):
        if not self.recording: return
        
        # Check if this key is blocked (part of the hotkey combo)
        if self._is_blocked(key):
            return  # Don't record this key at all
        
        # check for stop key
        try:
            k = key.char
        except AttributeError:
            k = key.name # e.g. "f8"

        # Check raw match or Key.<key> match
        key_str = str(key).replace("Key.", "")
        
        if self.stop_key is None:
            pass # Skip internal check
        elif key_str == self.stop_key or k == self.stop_key:
            print("Stop key pressed.")
            self.stop()
            if self.on_stop:
                self.on_stop()
            return

        with self.lock:
            try:
                key_char = key.char
            except AttributeError:
                key_char = str(key)
                
            self.events.append({
                "action": "key_press",
                "key": key_char,
                "delay": self._get_delay()
            })

    def _on_release(self, key):
        if not self.recording: return
        
        # Check if this key is blocked
        if self._is_blocked(key):
            return  # Don't record this key at all
            
        with self.lock:
            try:
                key_char = key.char
            except AttributeError:
                key_char = str(key)
                
            self.events.append({
                "action": "key_release",
                "key": key_char,
                "delay": self._get_delay()
            })
