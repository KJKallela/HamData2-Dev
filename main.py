import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import psycopg2
import io

# --- Generic window geometry saving/loading using gen_settings table ---

def get_pg_connection():
    # Adjust your connection parameters here
    return psycopg2.connect(
        dbname="HAMData",
        user="your_user",
        password="your_password",
        host="localhost",
        port=5432
    )

def load_window_geometry(name):
    """Load saved window geometry for a window named `name` from gen_settings."""
    try:
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT value FROM gen_settings WHERE key = %s", (f"win_geom_{name}",))
                row = cur.fetchone()
                if row and row[0]:
                    return row[0]
    except Exception as e:
        print(f"Error loading geometry for {name}: {e}")
    return None

def save_window_geometry(name, geometry):
    """Save window geometry string to gen_settings table."""
    try:
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO gen_settings(key, value) VALUES (%s, %s)
                    ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
                """, (f"win_geom_{name}", geometry))
                conn.commit()
    except Exception as e:
        print(f"Error saving geometry for {name}: {e}")

def load_background_image_filename():
    """Load background image filename from gen_settings."""
    try:
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT value FROM gen_settings WHERE key = %s", ("background_image",))
                row = cur.fetchone()
                if row and row[0]:
                    return row[0]
    except Exception as e:
        print(f"Error loading background image filename: {e}")
    return None

# --- Your window opening functions (replace with your actual implementations) ---
def open_qsos_window():
    print("Open QSOs window (stub)")

def open_callsigns_window():
    print("Open Callsigns window (stub)")

def open_dxcc_window():
    print("Open DXCC window (stub)")

def open_itu_window():
    print("Open ITU window (stub)")

def open_settings_window():
    print("Open Settings window (stub)")

# --- Main Application ---
class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("HAM Radio Application")

        # Load window geometry if saved previously
        geom = load_window_geometry("main")
        if geom:
            self.geometry(geom)
        else:
            self.geometry("1024x768")

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.create_menu()
        self.background_label = None
        self.load_and_display_background()

        # Save geometry on close
        self.bind("<Configure>", self.on_configure)

    def create_menu(self):
        menubar = tk.Menu(self)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Exit", command=self.on_close)
        menubar.add_cascade(label="File", menu=file_menu)

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="QSOs", command=open_qsos_window)
        view_menu.add_command(label="Callsigns", command=open_callsigns_window)
        view_menu.add_command(label="DXCC", command=open_dxcc_window)
        view_menu.add_command(label="ITU", command=open_itu_window)
        menubar.add_cascade(label="View", menu=view_menu)

        # Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(label="General Settings", command=open_settings_window)
        menubar.add_cascade(label="Settings", menu=settings_menu)

        self.config(menu=menubar)

    def on_close(self):
        if messagebox.askokcancel("Quit", "Are you sure you want to exit?"):
            # Save geometry before exit
            save_window_geometry("main", self.geometry())
            self.destroy()

    def on_configure(self, event):
        # Save geometry on window resize/move - could be optimized
        # but this is simple and works well
        if self.state() == 'normal':  # only when not minimized/maximized
            save_window_geometry("main", self.geometry())

    def load_and_display_background(self):
        filename = load_background_image_filename()
        if not filename:
            return  # no background image specified

        try:
            img = Image.open(filename)
            # We do NOT resize image; just center it
            self.background_image = ImageTk.PhotoImage(img)
            if self.background_label is None:
                self.background_label = tk.Label(self, image=self.background_image)
                self.background_label.place(relx=0.5, rely=0.5, anchor='center')
            else:
                self.background_label.config(image=self.background_image)
        except Exception as e:
            print(f"Failed to load background image {filename}: {e}")

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
