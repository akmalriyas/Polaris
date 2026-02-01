### Copyright @Akmal Riyas

import os
import sys

# Add path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ui.app import App

def show_splash():
    """Show splash screen before main app loads."""
    import customtkinter as ctk
    import time
    
    splash_root = ctk.CTk()
    splash_root.withdraw()
    
    splash = ctk.CTkToplevel(splash_root)
    splash.overrideredirect(True)
    splash.attributes('-topmost', True)
    
    # Center on screen
    w, h = 400, 200
    sw = splash.winfo_screenwidth()
    sh = splash.winfo_screenheight()
    x = (sw // 2) - (w // 2)
    y = (sh // 2) - (h // 2)
    splash.geometry(f"{w}x{h}+{x}+{y}")
    
    # Transparent key trick
    TRANS_KEY = "#000001"
    splash.configure(fg_color=TRANS_KEY)
    try: splash.attributes("-transparentcolor", TRANS_KEY)
    except: pass
    
    # Main frame
    frame = ctk.CTkFrame(splash, fg_color="#18181b", corner_radius=20, border_width=2, border_color="#8e44ad")
    frame.pack(expand=True, fill="both")
    
    # Logo text
    ctk.CTkLabel(frame, text="POLARIS", font=ctk.CTkFont(size=36, weight="bold"), text_color="#a1a1aa").pack(pady=(40, 5))
    ctk.CTkLabel(frame, text="Automation Made Simple", font=ctk.CTkFont(size=14), text_color="#71717a").pack()
    ctk.CTkLabel(frame, text="Loading...", font=ctk.CTkFont(size=11), text_color="#52525b").pack(pady=(30, 0))
    
    splash.update()
    splash_root.after(1500, splash_root.quit)
    splash_root.mainloop()
    
    splash.destroy()
    splash_root.destroy()

if __name__ == "__main__":
    # Show splash screen
    show_splash()
    
    # Launch main app
    app = App()
    
    # Set window icon
    icon_path_ico = os.path.join(os.path.dirname(__file__), "assets", "icon.ico")
    icon_path_png = os.path.join(os.path.dirname(__file__), "assets", "icon.png")
    
    if os.path.exists(icon_path_ico):
        try:
            app.iconbitmap(icon_path_ico)
        except Exception as e:
            print(f"Ico icon error: {e}")
    elif os.path.exists(icon_path_png):
        try:
            from PIL import Image, ImageTk
            img = Image.open(icon_path_png)
            img = img.resize((64, 64), Image.Resampling.LANCZOS)
            app.icon_photo = ImageTk.PhotoImage(img)
            app.iconphoto(True, app.icon_photo)
        except Exception as e:
            print(f"Png icon error: {e}")
    
    app.mainloop()
