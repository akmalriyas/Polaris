import requests
import json
import threading
from datetime import datetime

class WebhookManager:
    """Handles sending aesthetic embedded updates to Discord-compatible webhooks."""
    
    def __init__(self, url=None, enabled=False):
        self.url = url
        self.enabled = enabled
        self.color_info = 0x3498db  # Blue
        self.color_success = 0x2ecc71 # Green
        self.color_warning = 0xf1c40f # Gold
        self.color_error = 0xe74c3c   # Red

    def update_settings(self, url, enabled):
        self.url = url
        self.enabled = enabled

    def _send_async(self, payload):
        if not self.enabled or not self.url:
            return
            
        def _target():
            try:
                requests.post(self.url, json=payload, timeout=5)
            except Exception as e:
                print(f"Webhook failed: {e}")
                
        threading.Thread(target=_target, daemon=True).start()

    def send_status(self, title, description, status_type="info", fields=None):
        """Sends a structured embed message."""
        if not self.enabled or not self.url:
            return

        colors = {
            "info": self.color_info,
            "success": self.color_success,
            "warning": self.color_warning,
            "error": self.color_error
        }
        
        embed = {
            "title": f"Polaris | {title}",
            "description": description,
            "color": colors.get(status_type, self.color_info),
            "footer": {
                "text": "Polaris Macro • Made with ❤️ by Akmal"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if fields:
            embed["fields"] = fields
            
        payload = {
            "embeds": [embed],
            "username": "Polaris System",
            "avatar_url": "https://raw.githubusercontent.com/AkmalAzz/polaris-assets/main/logo.png" # Placeholder icon
        }
        
        self._send_async(payload)

    def on_recording_started(self):
        self.send_status("🔴 Recording Started", "The user has started recording a new macro.", "warning")

    def on_recording_finished(self, action_count):
        self.send_status("✅ Recording Finished", f"Macro capture completed successfully.", "success", [
            {"name": "Total Actions", "value": str(action_count), "inline": True}
        ])

    def on_playback_started(self, macro_name, loop_mode, total_loops):
        loops_text = f"Mode: {loop_mode.capitalize()}"
        if loop_mode == "count":
            loops_text += f" ({total_loops} times)"
        
        self.send_status("▶️ Playback Started", f"Executing macro: `{macro_name}`", "info", [
            {"name": "Loop Settings", "value": loops_text, "inline": True}
        ])

    def on_playback_finished(self, loop_count):
        self.send_status("🏁 Playback Completed", "Automation sequence finished.", "success", [
            {"name": "Loops Completed", "value": str(loop_count), "inline": True}
        ])

    def on_playback_error(self, error_msg):
        self.send_status("❌ Playback Error", f"An error occurred during execution: `{error_msg}`", "error")
