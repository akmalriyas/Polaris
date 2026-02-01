import customtkinter as ctk
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import sys
import time
from datetime import datetime
# from pynput import keyboard # Moved to HotkeyManager in logic

# Add path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.recorder import Recorder
from backend.player import Player
from backend.hotkeys import HotkeyManager
from ui.overlay import RecordingOverlay, PlaybackOverlay
from utils.file_manager import save_macro, load_macro
from utils.config import load_settings, save_settings
from utils.webhook_manager import WebhookManager

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Data & Configuration ---
        self.settings = load_settings()
        self.current_macro_data = {"flow": [], "metadata": {}}
        
        # Keep track of internal listeners/threads
        self.playback_lock = threading.Lock()
        self.playback_thread = None
        
        # --- Backend Setup ---
        self.hotkey_manager = HotkeyManager()
        self.recorder = Recorder(stop_key=None)
        self.player = Player()
        self.webhook_manager = WebhookManager(
            url=self.settings.get("webhook_url", ""),
            enabled=self.settings.get("webhook_enabled", False)
        )
        
        # --- UI Setup ---
        self.title("Polaris Macro")
        self.geometry("1100x750")
        
        # Better Dark Theme Colors
        # Backgrounds: #1e1e2e (Dark Indigo)
        # Accents: #8e44ad (Purple), #2980b9 (Blue)
        # Panels: #2b2d42
        
        ctk.set_appearance_mode("Dark")
        # We'll use manual colors mainly, but set default to blue
        ctk.set_default_color_theme("blue") 
        
        # Overlays
        self.rec_overlay = RecordingOverlay(self)
        self.play_overlay = PlaybackOverlay(self)

        # Layout Configuration
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Components
        self._create_sidebar()
        self._create_home_frame()
        self._create_playback_frame()
        self._create_webhooks_frame()
        self._create_settings_frame()
        
        # Init state
        self.select_frame("home")
        self._update_hotkeys()
        
        # Apply modern background
        self.configure(fg_color="#18181b") # Very dark grey/black

    def _update_hotkeys(self):
        """Updates global hotkeys based on settings."""
        def toggle_record():
            # Block recording entirely if playback is active
            if self.player.playing: 
                return  # Ignore record hotkey during playback
            
            if self.recorder.recording:
                self.after(0, self.stop_recording)
            else:
                self.after(0, self.start_recording)

        def trigger_play():
            if self.recorder.recording: return  # Can't play while recording
            
            # Toggle: if already playing, stop. Otherwise start.
            if self.player.playing:
                self.after(0, self.stop_playback)
            else:
                self.after(0, self.start_playback)
        
        key_map = {
            self.settings.get("rec_key", "f8"): toggle_record,
            self.settings.get("play_key", "f12"): trigger_play
        }
        self.hotkey_manager.start(key_map)

    def _create_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color="#202023")
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        
        # Configure grid rows - row 5 expands to push bottom elements down
        for i in range(10):
            self.sidebar_frame.grid_rowconfigure(i, weight=0)
        self.sidebar_frame.grid_rowconfigure(5, weight=1)  # Spacer row expands
        
        # Logo / Title
        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame, 
            text="POLARIS", 
            font=ctk.CTkFont(size=26, weight="bold", family="Segoe UI"),
            text_color="#a1a1aa" # Zinc-400
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(40, 30), sticky="w")
        
        # Nav Buttons
        self.btn_nav_home = self._create_nav_btn("Home", "home", 1)
        self.btn_nav_playback = self._create_nav_btn("Playback", "playback", 2)
        self.btn_nav_webhooks = self._create_nav_btn("Webhooks", "webhooks", 3)
        self.btn_nav_settings = self._create_nav_btn("Settings", "settings", 4)
        
        # Row 5 is empty spacer (weight=1 pushes everything below to bottom)
        
        # Metadata Panel
        self.meta_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.meta_frame.grid(row=6, column=0, padx=20, pady=(10, 5), sticky="sw")
        
        self.lbl_meta_date = ctk.CTkLabel(self.meta_frame, text="", text_color="gray50", font=ctk.CTkFont(size=11))
        self.lbl_meta_date.pack(anchor="w")
        
        self.lbl_meta_res = ctk.CTkLabel(self.meta_frame, text="", text_color="gray50", font=ctk.CTkFont(size=11))
        self.lbl_meta_res.pack(anchor="w")

        # Version
        self.version_label = ctk.CTkLabel(self.sidebar_frame, text="v1.3", text_color="gray40", font=ctk.CTkFont(size=10))
        self.version_label.grid(row=7, column=0, padx=20, pady=(5, 2), sticky="sw")

        # Credits (at very bottom)
        self.credits_label = ctk.CTkLabel(self.sidebar_frame, text="Made with ❤ by Akmal", text_color="#E91E63", font=ctk.CTkFont(size=10))
        self.credits_label.grid(row=8, column=0, padx=20, pady=(0, 15), sticky="sw")

    def _create_nav_btn(self, text, name, row):
        btn = ctk.CTkButton(
            self.sidebar_frame, 
            text=text, 
            command=lambda: self.select_frame(name),
            fg_color="transparent", 
            text_color="#d4d4d8", # Zinc-300
            hover_color="#3f3f46", # Zinc-700
            anchor="w",
            height=45,
            font=ctk.CTkFont(size=16, weight="normal")
        )
        btn.grid(row=row, column=0, padx=15, pady=4, sticky="ew")
        return btn

    def _create_home_frame(self):
        self.home_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.home_frame.grid_columnconfigure(0, weight=1)
        self.home_frame.grid_rowconfigure(2, weight=1) # Row 2 is workspace now (0=ribbon, 1=header)

        # Modern Ribbon
        self.ribbon = ctk.CTkFrame(self.home_frame, height=80, corner_radius=16, fg_color="#27272a") # Zinc-800
        self.ribbon.grid(row=0, column=0, padx=30, pady=30, sticky="ew")
        
        # Left Actions
        self.btn_record = ctk.CTkButton(self.ribbon, text="RECORD", width=110, height=42, corner_radius=8, 
                                        fg_color="#e11d48", hover_color="#be123c", font=ctk.CTkFont(weight="bold"),
                                        command=self.start_recording)
        self.btn_record.pack(side="left", padx=(20, 10), pady=20)
        
        self.btn_stop = ctk.CTkButton(self.ribbon, text="STOP", width=90, height=42, corner_radius=8, 
                                      fg_color="#52525b", state="disabled", font=ctk.CTkFont(weight="bold"),
                                      command=self.stop_recording)
        self.btn_stop.pack(side="left", padx=5, pady=20)
        
        self.btn_play = ctk.CTkButton(self.ribbon, text="PLAY", width=110, height=42, corner_radius=8, 
                                      fg_color="#10b981", hover_color="#059669", font=ctk.CTkFont(weight="bold"),
                                      command=self.start_playback)
        self.btn_play.pack(side="left", padx=10, pady=20)
        
        # Right Actions
        self.btn_save = ctk.CTkButton(self.ribbon, text="Export", width=90, height=38, fg_color="#3f3f46", hover_color="#52525b",
                                      command=self.save_current_macro)
        self.btn_save.pack(side="right", padx=(5, 20), pady=20)
        
        self.btn_load = ctk.CTkButton(self.ribbon, text="Import", width=90, height=38, fg_color="#3f3f46", hover_color="#52525b",
                                      command=self.load_macro_file)
        self.btn_load.pack(side="right", padx=5, pady=20)

        # Flow Header (Custom Styled)
        self.flow_header_frame = ctk.CTkFrame(self.home_frame, fg_color="transparent", height=30)
        self.flow_header_frame.grid(row=1, column=0, padx=35, pady=(0, 5), sticky="ew")
        
        ctk.CTkLabel(self.flow_header_frame, text="FLOW SEQUENCE", font=ctk.CTkFont(size=12, weight="bold"), text_color="gray60").pack(side="left")
        ctk.CTkLabel(self.flow_header_frame, text="ACTIONS", font=ctk.CTkFont(size=12, weight="bold"), text_color="gray60").pack(side="right", padx=10)

        # Workspace with modern styling (No label_text, using custom header above)
        self.workspace_frame = ctk.CTkScrollableFrame(self.home_frame, label_text="", fg_color="#27272a")
        self.workspace_frame.grid(row=2, column=0, padx=30, pady=(0, 30), sticky="nsew")
        
        # Status Bar Panel
        self.status_bar = ctk.CTkFrame(self.home_frame, height=35, corner_radius=8, fg_color="#27272a")
        self.status_bar.grid(row=3, column=0, padx=30, pady=(0, 20), sticky="ew")
        
        self.status_label = ctk.CTkLabel(self.status_bar, text="Ready", anchor="w", text_color="#a1a1aa", font=ctk.CTkFont(size=12))
        self.status_label.pack(side="left", padx=15, pady=5)

    def _create_playback_frame(self):
        self.playback_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        
        # Centered Container
        playback_container = ctk.CTkFrame(self.playback_frame, width=650, fg_color="transparent")
        playback_container.pack(expand=True, fill="y", pady=50)
        
        ctk.CTkLabel(playback_container, text="Playback Settings", font=ctk.CTkFont(size=28, weight="bold")).pack(pady=(0, 40))
        
        # Loop Mode Section
        loop_section = ctk.CTkFrame(playback_container, fg_color="#27272a", corner_radius=12)
        loop_section.pack(fill="x", padx=0, pady=10)
        
        # Header
        hdr = ctk.CTkFrame(loop_section, fg_color="transparent", height=30)
        hdr.pack(fill="x", padx=20, pady=(15, 5))
        ctk.CTkLabel(hdr, text="Loop Mode", font=ctk.CTkFont(size=16, weight="bold"), text_color="white").pack(side="left")
        ctk.CTkLabel(hdr, text="REPEAT", font=ctk.CTkFont(size=11, weight="bold"), text_color="#71717a").pack(side="right")
        ctk.CTkFrame(loop_section, height=2, fg_color="#3f3f46").pack(fill="x", padx=20, pady=(0, 10))
        
        # Grid container for aligned settings
        self.playback_grid = ctk.CTkFrame(loop_section, fg_color="transparent")
        self.playback_grid.pack(fill="x", padx=20, pady=(0, 10))
        self.playback_grid.columnconfigure(1, weight=1)
        
        # Repeat Mode row
        ctk.CTkLabel(self.playback_grid, text="Repeat Mode:", text_color="gray60", font=ctk.CTkFont(size=13)).grid(row=0, column=0, sticky="w", pady=10)
        self.opt_loop_mode = ctk.CTkOptionMenu(self.playback_grid, values=["Once", "Count", "Infinite"], 
                                                command=self.on_loop_mode_change, fg_color="#3f3f46", 
                                                button_color="#52525b", width=150, height=32)
        current_mode = self.settings.get("loop_mode", "once").capitalize()
        self.opt_loop_mode.set(current_mode)
        self.opt_loop_mode.grid(row=0, column=1, sticky="w", padx=15, pady=10)
        
        # Description row
        desc_text = {
            "Once": "Macro plays one time and stops.",
            "Count": "Macro plays a specific number of times.",
            "Infinite": "Macro loops until you press the Play hotkey."
        }
        self.loop_desc_label = ctk.CTkLabel(self.playback_grid, text=desc_text.get(current_mode, ""), 
                                             text_color="#71717a", font=ctk.CTkFont(size=11))
        self.loop_desc_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 10))
        
        # Loop count row (hidden by default unless mode is Count)
        self.lbl_loop_count = ctk.CTkLabel(self.playback_grid, text="Number of loops:", text_color="gray60", font=ctk.CTkFont(size=13))
        self.entry_loop_count = ctk.CTkEntry(self.playback_grid, width=100, height=32, placeholder_text="3")
        self.entry_loop_count.insert(0, str(self.settings.get("loop_count", 3)))
        self.entry_loop_count.bind("<FocusOut>", self.on_loop_count_change)
        
        if current_mode == "Count":
            self.lbl_loop_count.grid(row=2, column=0, sticky="w", pady=10)
            self.entry_loop_count.grid(row=2, column=1, sticky="w", padx=15, pady=10)

    def _create_settings_frame(self):
        self.settings_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        
        # Centered Container
        self.settings_container = ctk.CTkFrame(self.settings_frame, width=650, fg_color="transparent")
        self.settings_container.pack(expand=True, fill="y", pady=50) 
        
        ctk.CTkLabel(self.settings_container, text="Configuration", font=ctk.CTkFont(size=28, weight="bold")).pack(pady=(0, 40))

        # Start/Stop Key
        self._add_setting_section(self.settings_container, "Recording", "Global Hotkeys")
        self.opt_rec_key = ctk.CTkOptionMenu(self.curr_sec_frame, values=["F8", "CTRL + SHIFT + ALT + R", "Custom"], 
                                             command=self.on_rec_preset_change, fg_color="#3f3f46", button_color="#52525b", width=220)
        self.opt_rec_key.set(self.settings.get("rec_preset", "F8"))
        self.opt_rec_key.pack(anchor="w", pady=(5, 10))
        
        self.lbl_rec_custom = ctk.CTkLabel(self.curr_sec_frame, text=f"Active Bind: {self.settings.get('rec_key', 'f8')} (Toggles Record/Stop)", text_color="gray60", font=ctk.CTkFont(size=12))
        self.lbl_rec_custom.pack(anchor="w", padx=5, pady=(0, 10))
        
        # Listen Button
        self.btn_rec_listen = ctk.CTkButton(self.curr_sec_frame, text="Set New Key", width=120, height=28, fg_color="#4f46e5", hover_color="#4338ca",
                                            command=lambda: self.listen_for_key("rec"))

        # Play Key
        self._add_setting_section(self.settings_container, "Playback", "Global Hotkeys")
        self.opt_play_key = ctk.CTkOptionMenu(self.curr_sec_frame, values=["F12", "CTRL + SHIFT + ALT + P", "Custom"], 
                                              command=self.on_play_preset_change, fg_color="#3f3f46", button_color="#52525b", width=220)
        self.opt_play_key.set(self.settings.get("play_preset", "F12"))
        self.opt_play_key.pack(anchor="w", pady=(5, 10))
        self.lbl_play_custom = ctk.CTkLabel(self.curr_sec_frame, text=f"Active Bind: {self.settings.get('play_key', 'f12')}", text_color="gray60", font=ctk.CTkFont(size=12))
        self.lbl_play_custom.pack(anchor="w", padx=5, pady=(0, 10))
        
        self.btn_play_listen = ctk.CTkButton(self.curr_sec_frame, text="Set New Key", width=120, height=28, fg_color="#4f46e5", hover_color="#4338ca",
                                             command=lambda: self.listen_for_key("play"))
        
        # Init Listen Btn state
        if self.settings.get("rec_preset") == "Custom": self.btn_rec_listen.pack(anchor="w", pady=5)
        if self.settings.get("play_preset") == "Custom": self.btn_play_listen.pack(anchor="w", pady=5)

        # Visuals
        self._add_setting_section(self.settings_container, "Visuals", "Interface")
        self.sw_overlay = ctk.CTkSwitch(self.curr_sec_frame, text="Show Status Overlays", command=self.toggle_overlay, progress_color="#7c3aed")
        if self.settings.get("show_overlay", True): self.sw_overlay.select()
        else: self.sw_overlay.deselect()
        self.sw_overlay.pack(anchor="w", pady=5)

    def _create_webhooks_frame(self):
        self.webhooks_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        
        # Centered Container
        webhooks_container = ctk.CTkFrame(self.webhooks_frame, width=650, fg_color="transparent")
        webhooks_container.pack(expand=True, fill="y", pady=50)
        
        ctk.CTkLabel(webhooks_container, text="Webhook Integration", font=ctk.CTkFont(size=28, weight="bold")).pack(pady=(0, 40))
        
        # Config Section
        self._add_setting_section(webhooks_container, "Webhook Setup", "REAL-TIME STATUS")
        
        self.sw_webhook = ctk.CTkSwitch(self.curr_sec_frame, text="Enable Webhook Updates", command=self.toggle_webhooks, progress_color="#8dbdff")
        if self.settings.get("webhook_enabled", False): self.sw_webhook.select()
        else: self.sw_webhook.deselect()
        self.sw_webhook.pack(anchor="w", pady=(5, 15))
        
        ctk.CTkLabel(self.curr_sec_frame, text="Webhook URL:", text_color="gray60", font=ctk.CTkFont(size=13)).pack(anchor="w", padx=5, pady=(0, 5))
        self.entry_webhook_url = ctk.CTkEntry(self.curr_sec_frame, width=500, height=35, placeholder_text="https://discord.com/api/webhooks/...")
        self.entry_webhook_url.insert(0, self.settings.get("webhook_url", ""))
        self.entry_webhook_url.pack(anchor="w", padx=5, pady=(0, 15))
        self.entry_webhook_url.bind("<FocusOut>", lambda e: self.toggle_webhooks())
        
        self.btn_test_webhook = ctk.CTkButton(self.curr_sec_frame, text="Send Test Message", width=160, height=32, 
                                             fg_color="#3f3f46", hover_color="#52525b", command=self.send_test_webhook)
        self.btn_test_webhook.pack(anchor="w", padx=5, pady=(0, 10))
        
        # Info Box
        info_frame = ctk.CTkFrame(webhooks_container, fg_color="#1e1b4b", corner_radius=12) # Dark indigo/blue
        info_frame.pack(fill="x", pady=20)
        ctk.CTkLabel(info_frame, text="ℹ️ Polaris will send aesthetic embeds (Discord format) on events like Recording Start, Playback Finished, etc.", 
                     wraplength=550, text_color="#93c5fd", font=ctk.CTkFont(size=12)).pack(padx=20, pady=15)

    def _add_setting_section(self, parent, title, category):
        # We can add a category header if new
        self.curr_sec_frame = ctk.CTkFrame(parent, fg_color="#27272a", corner_radius=12)
        self.curr_sec_frame.pack(fill="x", padx=0, pady=10)
        
        hdr = ctk.CTkFrame(self.curr_sec_frame, fg_color="transparent", height=30)
        hdr.pack(fill="x", padx=20, pady=(15, 5))
        
        ctk.CTkLabel(hdr, text=title, font=ctk.CTkFont(size=16, weight="bold"), text_color="white").pack(side="left")
        if category:
            ctk.CTkLabel(hdr, text=category.upper(), font=ctk.CTkFont(size=11, weight="bold"), text_color="#71717a").pack(side="right", pady=2)
            
        # Divider
        ctk.CTkFrame(self.curr_sec_frame, height=2, fg_color="#3f3f46").pack(fill="x", padx=20, pady=(0, 10))
        # Content padding wrapper
        self.curr_sec_frame = ctk.CTkFrame(self.curr_sec_frame, fg_color="transparent")
        self.curr_sec_frame.pack(fill="x", padx=20, pady=(0, 20))

    # --- Logic ---
    
    def toggle_overlay(self):
        val = self.sw_overlay.get()
        self.settings["show_overlay"] = bool(val)
        save_settings(self.settings)

    def toggle_webhooks(self):
        enabled = bool(self.sw_webhook.get())
        url = self.entry_webhook_url.get().strip()
        self.settings["webhook_enabled"] = enabled
        self.settings["webhook_url"] = url
        save_settings(self.settings)
        self.webhook_manager.update_settings(url, enabled)

    def send_test_webhook(self):
        self.webhook_manager.send_status("🧪 Test Notification", "Webhook integration is correctly configured!", "success")
        self.status_label.configure(text="Test webhook sent.")

    def on_loop_mode_change(self, choice):
        mode = choice.lower()
        self.settings["loop_mode"] = mode
        save_settings(self.settings)
        
        # Update description
        desc_text = {
            "once": "Macro plays one time and stops.",
            "count": "Macro plays a specific number of times.",
            "infinite": "Macro loops until you press the Play hotkey."
        }
        if hasattr(self, 'loop_desc_label'):
            self.loop_desc_label.configure(text=desc_text.get(mode, ""))
        
        # Show/hide loop count fields using grid
        if mode == "count":
            self.lbl_loop_count.grid(row=2, column=0, sticky="w", pady=10)
            self.entry_loop_count.grid(row=2, column=1, sticky="w", padx=15, pady=10)
        else:
            self.lbl_loop_count.grid_forget()
            self.entry_loop_count.grid_forget()
    
    def on_loop_count_change(self, event=None):
        try:
            count = int(self.entry_loop_count.get())
            if count < 1: count = 1
            if count > 9999: count = 9999
            self.settings["loop_count"] = count
            save_settings(self.settings)
        except ValueError:
            pass  # Invalid input, ignore

    def on_rec_preset_change(self, choice):
        if choice == "Custom":
            self.settings["rec_preset"] = "Custom"
            self.btn_rec_listen.pack(anchor="w", pady=5)
            # Maybe show listen immediately?
        else:
            self.btn_rec_listen.pack_forget()
            val = "f8" if choice == "F8" else "ctrl+shift+alt+r"
            self._validate_and_set_key("rec", val, choice)

    def on_play_preset_change(self, choice):
        if choice == "Custom":
            self.settings["play_preset"] = "Custom"
            self.btn_play_listen.pack(anchor="w", pady=5)
        else:
            self.btn_play_listen.pack_forget()
            val = "f12" if choice == "F12" else "ctrl+shift+alt+p"
            self._validate_and_set_key("play", val, choice)
            
    def _validate_and_set_key(self, type_, key, preset):
        # Validation
        key = key.lower()
        if type_ == "rec":
            other = self.settings.get("play_key", "f12").lower()
            if key == other:
                messagebox.showerror("Conflict", "Record key cannot be the same as Playback key!")
                self.opt_rec_key.set(self.settings.get("rec_preset")) # Revert
                return
            
            self.settings["rec_key"] = key
            self.settings["rec_preset"] = preset
            self.lbl_rec_custom.configure(text=f"Active Bind: {key} (Toggles Record/Stop)")
        else:
            other = self.settings.get("rec_key", "f8").lower()
            if key == other:
                messagebox.showerror("Conflict", "Playback key cannot be the same as Record key!")
                self.opt_play_key.set(self.settings.get("play_preset")) # Revert
                return

            self.settings["play_key"] = key
            self.settings["play_preset"] = preset
            self.lbl_play_custom.configure(text=f"Active Bind: {key}")
            
        save_settings(self.settings)
        self._update_hotkeys()

    def listen_for_key(self, type_):
        # Modal Overlay inside window
        self.listen_overlay = ctk.CTkFrame(self, fg_color="black") # High contrast overlay
        self.listen_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.listen_overlay.place_configure(relx=0.5, rely=0.5, anchor="center") # Centered? no, fullscreen place
        
        # Semi-transparent feel (cant do alpha on frame easily in tk, so just opaque dark)
        self.listen_overlay.configure(fg_color="#000000") 
        # Actually use a centered box inside
        
        container = ctk.CTkFrame(self.listen_overlay, fg_color="#18181b", border_width=2, border_color="#4f46e5", width=400, height=300)
        container.place(relx=0.5, rely=0.5, anchor="center")
        
        ctk.CTkLabel(container, text="Listening for Input...", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(50, 20))
        ctk.CTkLabel(container, text="Press any key to bind...", text_color="gray").pack()
        
        cancel = ctk.CTkButton(container, text="Cancel", fg_color="#3f3f46", hover_color="#52525b", command=self._cancel_listen)
        cancel.pack(pady=30)
        
        self.update()
        
        # Check current key to ensure we don't capture the mouse click that opened this
        time.sleep(0.2)
        
        def on_press(key):
            try: k = key.char
            except: k = key.name
            if k is None: k = str(key)
            self.after(0, lambda: self._finish_listen(type_, k))
            return False 
            
        from pynput import keyboard
        self.key_listener = keyboard.Listener(on_press=on_press)
        self.key_listener.start()

    def _cancel_listen(self):
        if hasattr(self, 'key_listener') and self.key_listener:
            self.key_listener.stop()
        if hasattr(self, 'listen_overlay'):
            self.listen_overlay.destroy()

    def _finish_listen(self, type_, key):
        self._cancel_listen()
        # Apply
        new_key = str(key).lower()
        self._validate_and_set_key(type_, new_key, "Custom")
    
    # ... End keybind logic ...

    def show_loading(self, msg):
        # Windowless Overlay style
        self.loading_overlay = ctk.CTkFrame(self, fg_color="#18181b")
        self.loading_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        container = ctk.CTkFrame(self.loading_overlay, fg_color="#27272a", corner_radius=20)
        container.place(relx=0.5, rely=0.5, anchor="center")
        
        ctk.CTkLabel(container, text="⏳", font=ctk.CTkFont(size=40)).pack(padx=50, pady=(40, 10))
        ctk.CTkLabel(container, text=msg, font=ctk.CTkFont(size=16, weight="bold")).pack(padx=50, pady=(10, 40))
        self.update()

    def hide_loading(self):
        if hasattr(self, 'loading_overlay') and self.loading_overlay:
            self.loading_overlay.destroy()
            del self.loading_overlay

    def select_frame(self, name):
        # Reset all nav button states
        self.btn_nav_home.configure(fg_color="transparent")
        self.btn_nav_playback.configure(fg_color="transparent")
        self.btn_nav_webhooks.configure(fg_color="transparent")
        self.btn_nav_settings.configure(fg_color="transparent")
        
        # Hide all frames
        self.home_frame.grid_forget()
        self.playback_frame.grid_forget()
        self.webhooks_frame.grid_forget()
        self.settings_frame.grid_forget()
        
        # Show selected frame
        if name == "home":
            self.home_frame.grid(row=0, column=1, sticky="nsew")
            self.btn_nav_home.configure(fg_color="#3f3f46")
        elif name == "playback":
            self.playback_frame.grid(row=0, column=1, sticky="nsew")
            self.btn_nav_playback.configure(fg_color="#3f3f46")
        elif name == "webhooks":
            self.webhooks_frame.grid(row=0, column=1, sticky="nsew")
            self.btn_nav_webhooks.configure(fg_color="#3f3f46")
        elif name == "settings":
            self.settings_frame.grid(row=0, column=1, sticky="nsew")
            self.btn_nav_settings.configure(fg_color="#3f3f46")

    def start_recording(self):
        # Stop playback if running and wait for it to finish
        if self.player.playing: 
            self.stop_playback()
            # Wait for player thread to fully stop
            for _ in range(50): # Max 500ms wait
                if not self.player.playing:
                    break
                time.sleep(0.01)
        
        self.status_label.configure(text="Recording started...")
        self.btn_record.configure(state="disabled")
        self.btn_play.configure(state="disabled")
        self.btn_stop.configure(state="normal", fg_color="#e74c3c")
        
        # Show overlay with keybind (if enabled)
        if self.settings.get("show_overlay", True):
            rec_key = self.settings.get("rec_preset", "F8")
            if rec_key == "Custom": rec_key = self.settings.get("rec_key", "?")
            self.rec_overlay.show(stop_key=rec_key)
        
        self.recorder.start()
        self.webhook_manager.on_recording_started()

    def stop_recording(self):
        # if not self.recorder.recording and not self.recorder.mouse_listener: return # REMOVED: Cause of state desync
        events = self.recorder.stop()
        events = self._trim_hotkeys(events) # Clean up triggers
        self.webhook_manager.on_recording_finished(len(events))
        self.current_macro_data["flow"] = events
        self.current_macro_data["metadata"] = {
            "screen_width": self.winfo_screenwidth(),
            "screen_height": self.winfo_screenheight(),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.rec_overlay.hide() # Always hide just in case
        self.btn_record.configure(state="normal")
        self.btn_play.configure(state="normal")
        self.btn_stop.configure(state="disabled", fg_color="#52525b")
        self.status_label.configure(text=f"Recording finished. Captured {len(events)} actions.")
        self.refresh_workspace()
        self._update_metadata_ui()

    def _trim_hotkeys(self, events):
        """Removes the start/stop hotkey events from both ends of the recording."""
        if not events: return []
        
        # Get components of the hotkey (e.g. "f8" or "ctrl+alt" -> {'f8'} or {'ctrl', 'alt'})
        rec_key = self.settings.get("rec_key", "f8").lower()
        parts = set([p.strip() for p in rec_key.split("+")])
        
        def normalize_key(k):
            """Normalize key string for comparison"""
            k = str(k).lower()
            # Handle 'Key.ctrl_l', 'Key.alt_r', 'Key.f8' formats
            if k.startswith("key."): k = k[4:]
            # Handle ctrl_l -> ctrl, alt_r -> alt
            for suffix in ['_l', '_r']:
                if k.endswith(suffix):
                    k = k[:-2]
            return k
        
        def is_hotkey_part(event):
            k = normalize_key(event.get("key", ""))
            return k in parts
        
        # Trim from HEAD: releases of the start hotkey (user lifting fingers after pressing to start)
        while events and events[0].get("action") == "key_release" and is_hotkey_part(events[0]):
            events.pop(0)
        
        # Trim from TAIL: any key events (press or release) that are part of stop hotkey
        # This catches: key_press of stop combo, and any lingering releases
        while events and is_hotkey_part(events[-1]):
            events.pop()
        
        return events

    def stop_playback(self):
        """Forces playback to stop."""
        if self.player.playing:
            self.player.stop()
        self.play_overlay.hide() # Always hide
        self.btn_record.configure(state="normal")
        self.btn_play.configure(state="normal")

    def start_playback(self):
        with self.playback_lock:
            if not self.current_macro_data["flow"]:
                messagebox.showwarning("Polaris", "No macro loaded!")
                return

            # Concurrency Check: If already playing, stop first
            if self.player.playing:
                self.player.stop()
                time.sleep(0.2) 
            
            # Reset tracking
            self._last_loop_count = 0
            self.player.playing = True

            # Get loop settings
            loop_mode = self.settings.get("loop_mode", "once")
            loop_count = self.settings.get("loop_count", 3) if loop_mode == "count" else 1
            if loop_mode == "infinite":
                loop_count = -1
                
            self.status_label.configure(text="Playing...")
            self.btn_record.configure(state="disabled")
            self.btn_play.configure(state="disabled")
            
            if self.settings.get("show_overlay", True):
                self.play_overlay.show(len(self.current_macro_data["flow"]), loop_mode, loop_count)
            
            self.webhook_manager.on_playback_started("Custom Macro", loop_mode, loop_count)
            
            self.playback_thread = threading.Thread(target=self._run_playback_thread, args=(loop_mode, loop_count), daemon=True)
            self.playback_thread.start()

    def _run_playback_thread(self, loop_mode="once", total_loops=1):
        current_loop = 0
        try:
            while self.player.playing:
                current_loop += 1
                self._last_loop_count = current_loop
                
                # Update overlay with current loop
                if self.settings.get("show_overlay", True):
                    self.after(0, lambda l=current_loop: self.play_overlay.update_loop(l))
                
                self.player.play(self.current_macro_data)
                
                # Check exit conditions
                if not self.player.playing:
                    break
                if loop_mode == "once":
                    break
                elif loop_mode == "count" and current_loop >= total_loops:
                    break
                # Infinite continues automatically
        finally:
            self.player.playing = False
            self.after(0, self._on_playback_finished)
        
    def _on_playback_finished(self):
        # Removed safety check that could hang the UI if state was inconsistent
        self.status_label.configure(text="Playback finished.")
        self.play_overlay.hide()
        self.btn_record.configure(state="normal")
        self.btn_play.configure(state="normal")
        
        loop_count = getattr(self, '_last_loop_count', 1)
        self.webhook_manager.on_playback_finished(loop_count)

    # ... Save/Load/Refresh (UI updates) ...
    def save_current_macro(self):
        if not self.current_macro_data["flow"]: return
        f = filedialog.asksaveasfilename(defaultextension=".polaris", filetypes=[("Polaris Macro", "*.polaris")])
        if f:
            self.show_loading("Exporting Macro...")
            self.after(100, lambda: self._do_save(f))
            
    def _do_save(self, f):
        self.current_macro_data["metadata"] = {
            "screen_width": self.winfo_screenwidth(),
            "screen_height": self.winfo_screenheight(),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        save_macro(f, self.current_macro_data)
        self.status_label.configure(text=f"Saved to {os.path.basename(f)}")
        self.hide_loading()
        self._update_metadata_ui()

    def load_macro_file(self):
        f = filedialog.askopenfilename(filetypes=[("Polaris Macro", "*.polaris")])
        if f:
            self.show_loading("Importing Macro...")
            self.after(100, lambda: self._do_load(f))
            
    def _do_load(self, f):
        try:
            data = load_macro(f)
            # Check for resolution mismatch
            md = data.get("metadata", {})
            mac_w = md.get("screen_width")
            mac_h = md.get("screen_height")
            
            if mac_w and mac_h:
                curr_w = self.winfo_screenwidth()
                curr_h = self.winfo_screenheight()
                if mac_w != curr_w or mac_h != curr_h:
                    warn_msg = (
                        f"Resolution Mismatch!\n\n"
                        f"This macro was recorded at {mac_w}x{mac_h}, but your current screen is {curr_w}x{curr_h}.\n"
                        f"Playback might be inaccurate or fail. Continue?"
                    )
                    if not messagebox.askyesno("Polaris - Warning", warn_msg):
                        self.hide_loading()
                        return
            
            self.current_macro_data = data
            self.refresh_workspace()
            self._update_metadata_ui()
            self.status_label.configure(text=f"Loaded {os.path.basename(f)}")
        except Exception as e:
            messagebox.showerror("Error", f"{e}")
        self.hide_loading()

    def _update_metadata_ui(self):
        md = self.current_macro_data.get("metadata", {})
        self.lbl_meta_date.configure(text=f"Date: {md.get('created_at', '-')}")
        res = f"{md.get('screen_width', '-')}x{md.get('screen_height', '-')}"
        self.lbl_meta_res.configure(text=f"Res: {res}")

    def refresh_workspace(self):
        # Clear
        for widget in self.workspace_frame.winfo_children(): widget.destroy()
        
        grouped_events = []
        current_move_batch = []
        buttons_down = set()
        
        def flush_batch():
            nonlocal current_move_batch
            if not current_move_batch: return
            start_pos = current_move_batch[0]["coords"]
            end_pos = current_move_batch[-1]["coords"]
            count = len(current_move_batch)
            is_drag = current_move_batch[0].get("_is_drag", False)
            btn = current_move_batch[0].get("_drag_btn", "")
            
            icon = "🖐️" if is_drag else "〰️"
            label = "Drag Path" if is_drag else "Mouse Movement"
            details = f"[{btn}]" if is_drag and btn else ""
            
            grouped_events.append({
                "action": "mouse_path_group",
                "display_text": f"{icon}  {label} {details}  ({count} pts)",
                "count": count, "is_drag": is_drag
            })
            current_move_batch = []

        for event in self.current_macro_data["flow"]:
            action = event.get("action")
            if action == "mouse_click":
                flush_batch()
                btn = event.get("button")
                pressed = event.get("pressed")
                if pressed: buttons_down.add(btn)
                else: buttons_down.discard(btn)
                grouped_events.append(event)
            elif action == "mouse_move":
                is_dragging = len(buttons_down) > 0
                drag_btn = list(buttons_down)[0] if is_dragging else ""
                event["_is_drag"] = is_dragging
                event["_drag_btn"] = drag_btn
                current_move_batch.append(event)
            else:
                flush_batch()
                grouped_events.append(event)
        flush_batch()

        MAX_ITEMS = 500
        count_display = len(grouped_events)
        
        # Color palette
        C_DRAG = "#7c3aed" # Violet 600
        # Alternating row colors for readability
        ROW_A = "#27272a" # Zinc 800
        ROW_B = "#18181b" # Zinc 950
        
        for i, item in enumerate(grouped_events):
            if i >= MAX_ITEMS:
                ctk.CTkLabel(self.workspace_frame, text=f"... and {count_display - MAX_ITEMS} more.", 
                             fg_color="#f59e0b", text_color="black", corner_radius=6).pack(fill="x", padx=5, pady=2)
                break
            
            bg_col = ROW_A if i % 2 == 0 else ROW_B
            text = ""
            at = item.get("action", "?")
            fg_col = bg_col # Default
            
            if at == "mouse_path_group":
                text = f"  {i+1:<4} {item['display_text']}"
                is_drag = item.get("is_drag", False)
                if is_drag: fg_col = C_DRAG
                
            elif at == "mouse_click":
                btn = str(item.get("button")).replace("Button.", "").upper()
                state = "DOWN" if item.get("pressed") else "UP  "
                icon = "🖱️ "
                # Align text with spaces/f-string padding
                text = f"  {i+1:<4} {icon}  CLICK  {btn:<6} {state}  @ {item.get('coords')}"
                if item.get("pressed"): fg_col = "#7f1d1d" # Red 900 for down
            
            elif at == "key_press": 
                k = item.get("key")
                icon = "⌨️ "
                text = f"  {i+1:<4} {icon}  PRESS  '{k}'"
                
            elif at == "key_release":
                k = item.get("key")
                icon = "⌨️ "
                text = f"  {i+1:<4} {icon}  RELEASE  '{k}'"
                
            elif at == "mouse_scroll":
                icon = "↕️ "
                text = f"  {i+1:<4} {icon}  SCROLL  {item.get('dx')}, {item.get('dy')}"
                
            else:
                text = f"  {i+1:<4} {at}"

            # Render Row (Optimized for scrolling performance)
            lbl = ctk.CTkLabel(
                self.workspace_frame, 
                text=text, 
                anchor="w", 
                fg_color=fg_col, 
                corner_radius=0, # Removed for buttery smooth scrolling
                font=ctk.CTkFont(family="Consolas", size=12)
            )
            lbl.pack(fill="x", padx=2, pady=0.5, ipady=4)
        
        # Stabilize layout for the scrollable frame
        self.workspace_frame.update_idletasks()

if __name__ == "__main__":
    app = App()
    app.mainloop()
