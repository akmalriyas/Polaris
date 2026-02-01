import customtkinter as ctk
import time
import os

class SplashScreen:
    """Modern windowless splash screen for app startup."""
    
    def __init__(self):
        self.root = ctk.CTk()
        self.root.withdraw()  # Hide root window
        
        self.splash = ctk.CTkToplevel(self.root)
        self.splash.overrideredirect(True)
        self.splash.attributes('-topmost', True)
        self.splash.attributes('-alpha', 0.0)  # Start transparent for fade-in
        
        # Center on screen
        w, h = 400, 200
        sw = self.splash.winfo_screenwidth()
        sh = self.splash.winfo_screenheight()
        x = (sw // 2) - (w // 2)
        y = (sh // 2) - (h // 2)
        self.splash.geometry(f"{w}x{h}+{x}+{y}")
        
        # Transparent key trick
        TRANS_KEY = "#000001"
        self.splash.configure(fg_color=TRANS_KEY)
        try: self.splash.attributes("-transparentcolor", TRANS_KEY)
        except: pass
        
        # Main frame
        self.frame = ctk.CTkFrame(self.splash, fg_color="#18181b", corner_radius=20, border_width=2, border_color="#8e44ad")
        self.frame.pack(expand=True, fill="both")
        
        # Logo text
        ctk.CTkLabel(self.frame, text="POLARIS", font=ctk.CTkFont(size=36, weight="bold"), text_color="#a1a1aa").pack(pady=(40, 5))
        
        # Tagline
        ctk.CTkLabel(self.frame, text="Automation Made Simple", font=ctk.CTkFont(size=14), text_color="#71717a").pack()
        
        # Loading indicator
        self.loading_label = ctk.CTkLabel(self.frame, text="Loading...", font=ctk.CTkFont(size=11), text_color="#52525b")
        self.loading_label.pack(pady=(30, 0))
        
        # Fade in
        self._fade_in()
    
    def _fade_in(self, alpha=0.0):
        if alpha < 0.95:
            alpha += 0.05
            self.splash.attributes('-alpha', alpha)
            self.splash.after(20, lambda: self._fade_in(alpha))
    
    def update_status(self, text):
        """Update the loading status text."""
        self.loading_label.configure(text=text)
        self.splash.update()
    
    def close(self):
        """Fade out and close splash."""
        self._fade_out(0.95)
    
    def _fade_out(self, alpha):
        if alpha > 0:
            alpha -= 0.1
            self.splash.attributes('-alpha', alpha)
            self.splash.after(20, lambda: self._fade_out(alpha))
        else:
            self.splash.destroy()
            self.root.destroy()
    
    def mainloop(self, duration_ms=1500):
        """Run splash for specified duration then close."""
        self.splash.after(duration_ms, self.close)
        self.root.mainloop()


def show_splash(duration_ms=1500):
    """Convenience function to show splash screen."""
    splash = SplashScreen()
    splash.mainloop(duration_ms)
