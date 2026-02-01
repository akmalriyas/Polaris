import customtkinter as ctk
import time

class BaseOverlay:
    def __init__(self, root, title="Overlay", accent_color="#3f3f46"):
        self.root = root
        self.window = None
        self.running = False
        self.start_time = 0
        self.accent_color = accent_color
        self.title_text = title
        self.lbl_timer = None
        self.lbl_status = None

    def show(self):
        self.hide() # Clean up any existing window and references
            
        self.window = ctk.CTkToplevel(self.root)
        self.window.attributes('-topmost', True)
        self.window.overrideredirect(True)
        self.window.attributes('-alpha', 0.95)
        
        # Geometry - Widened for hotkey text
        sw = self.window.winfo_screenwidth()
        w, h = 320, 90
        x = (sw // 2) - (w // 2)
        y = 40
        self.window.geometry(f"{w}x{h}+{x}+{y}")
        
        # Transparent Key Trick for Borders
        # We set the window bg to a specific color and make that color transparent
        # allowing the rounded frame to stand out cleanly.
        TRANS_KEY = "#000001"
        self.window.configure(fg_color=TRANS_KEY)
        try: self.window.attributes("-transparentcolor", TRANS_KEY)
        except: pass # Linux/Mac fallback might fail this, but win32 supports it

        # Main Container with Border
        # Note: border_color in ctk frame is the border. 
        self.frame = ctk.CTkFrame(self.window, fg_color="#18181b", border_width=2, border_color=self.accent_color, corner_radius=16)
        self.frame.pack(expand=True, fill="both", padx=0, pady=0) # No padding needed if transparent key works
        
        # Content
        # Title Line
        self.lbl_status = ctk.CTkLabel(self.frame, text=self.title_text, font=ctk.CTkFont(size=13, weight="bold"), text_color=self.accent_color)
        self.lbl_status.pack(pady=(12, 0))
        
        # Timer / Main Info
        self.lbl_timer = ctk.CTkLabel(self.frame, text="00:00", font=ctk.CTkFont(family="Consolas", size=24, weight="bold"), text_color="white")
        self.lbl_timer.pack(pady=(0, 0))
        
        # Footer
        self.lbl_footer = ctk.CTkLabel(self.frame, text="...", font=ctk.CTkFont(size=12), text_color="gray60")
        self.lbl_footer.pack(pady=(0, 10))

        self.running = True
        self.start_time = time.time()
        self._update()

    def hide(self):
        self.running = False
        if self.window:
            try: self.window.destroy()
            except: pass
            self.window = None
        # Clear references to widgets that were inside the destroyed window
        self.lbl_timer = None
        self.lbl_status = None
        self.lbl_footer = None

    def _update(self):
        if not self.running or not self.window: return
        try:
            if not self.window.winfo_exists(): return
        except: return
            
        self.on_update()
        self.window.after(100, self._update)
        
    def on_update(self):
        pass

class RecordingOverlay(BaseOverlay):
    def __init__(self, root):
        super().__init__(root, "🔴 RECORDING", "#e11d48") # Rose-600
        self.stop_key_text = ""

    def show(self, stop_key="F8"):
        self.stop_key_text = stop_key
        super().show()
        # Initial update of text
        self.lbl_footer.configure(text=f"Press {self.stop_key_text} to Stop")
        
    def on_update(self):
        elapsed = time.time() - self.start_time
        mins = int(elapsed // 60)
        secs = int(elapsed % 60)
        if self.lbl_timer:
            self.lbl_timer.configure(text=f"{mins:02}:{secs:02}")
        # Keep on top
        self.window.attributes('-topmost', True)

class PlaybackOverlay(BaseOverlay):
    def __init__(self, root):
        super().__init__(root, "▶ PLAYING", "#10b981") # Emerald-500
        self.action_count = 0
        self.loop_mode = "once"
        self.total_loops = 1
        self.current_loop = 1
        self.lbl_loop = None
    
    def show(self, total_actions=0, loop_mode="once", total_loops=1):
        self.action_count = total_actions
        self.loop_mode = loop_mode
        self.total_loops = total_loops
        self.current_loop = 1
        super().show()
        
        # Add loop status label between timer and footer
        if self.lbl_loop is None:
            self.lbl_loop = ctk.CTkLabel(self.frame, text="", font=ctk.CTkFont(size=12, weight="bold"), text_color="#a3e635")
            self.lbl_loop.pack(pady=(0, 0))
        
        self._update_loop_display()
        self.lbl_footer.configure(text="Press Play Key to Stop")
    
    def _update_loop_display(self):
        if self.loop_mode == "once":
            text = "Single Run"
        elif self.loop_mode == "count":
            text = f"Loop {self.current_loop}/{self.total_loops}"
        elif self.loop_mode == "infinite":
            text = f"Loop {self.current_loop} (∞)"
        else:
            text = ""
        
        if self.lbl_loop:
            self.lbl_loop.configure(text=text)
    
    def update_loop(self, current_loop):
        """Update the current loop number (called from main thread)."""
        self.current_loop = current_loop
        self._update_loop_display()

    def hide(self):
        super().hide()
        self.lbl_loop = None

    def on_update(self):
        elapsed = time.time() - self.start_time
        mins = int(elapsed // 60)
        secs = int(elapsed % 60)
        if self.lbl_timer:
            self.lbl_timer.configure(text=f"{mins:02}:{secs:02}")
        self.window.attributes('-topmost', True)
