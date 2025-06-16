
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import psycopg2
from config import DB_SETTINGS

def get_pg_connection():
    return psycopg2.connect(
        dbname=DB_SETTINGS["database"],
        user=DB_SETTINGS["user"],
        password=DB_SETTINGS["password"],
        host=DB_SETTINGS["host"],
        port=DB_SETTINGS["port"]
    )

def load_window_geometry(name):
    try:
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT value FROM gen_settings WHERE key = %s", (f"{name}_geometry",))
                row = cur.fetchone()
                return row[0] if row else ""
    except Exception:
        return ""

def save_window_geometry(name, geometry):
    try:
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO gen_settings (key, value) VALUES (%s, %s) "
                    "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value",
                    (f"{name}_geometry", geometry)
                )
                conn.commit()
    except Exception as e:
        print(f"Error saving geometry for {name}: {e}")

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("HamData2")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        geometry = load_window_geometry("main")
        if geometry:
            self.geometry(geometry)
        else:
            self.geometry("1024x768")

        self.create_menubar()

        # Load background image
        self.bg_label = None
        self.load_background_image()

    def create_menubar(self):
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Exit", command=self.on_close)
        menubar.add_cascade(label="File", menu=file_menu)

        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="QSOs", command=self.open_qso_window)
        view_menu.add_command(label="Callsigns", command=self.open_callsigns_window)
        view_menu.add_command(label="DXCC Codes", command=self.open_dxcc_window)
        view_menu.add_command(label="ITU Codes", command=self.open_itu_window)
        menubar.add_cascade(label="View", menu=view_menu)

        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(label="General Settings", command=self.open_settings_window)
        menubar.add_cascade(label="Settings", menu=settings_menu)

        self.config(menu=menubar)

    def load_background_image(self):
        try:
            with get_pg_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT value FROM gen_settings WHERE key = 'background_image'")
                    row = cur.fetchone()
                    if row and row[0]:
                        image_path = row[0]
                        image = Image.open(image_path)
                        bg = ImageTk.PhotoImage(image)
                        self.bg_label = tk.Label(self, image=bg)
                        self.bg_label.image = bg
                        self.bg_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        except Exception as e:
            print(f"Background image loading failed: {e}")

    def on_close(self):
        save_window_geometry("main", self.geometry())
        if messagebox.askokcancel("Quit", "Do you really want to quit?"):
            self.destroy()

    def open_qso_window(self):
        from qsos_window import open_qsos_window
        open_qsos_window(self)

    def open_callsigns_window(self):
        from callsigns_window import open_callsigns_window
        open_callsigns_window(self)

    def open_dxcc_window(self):
        from dxcc_window import open_dxcc_window
        open_dxcc_window(self)

    def open_itu_window(self):
        from itu_window import open_itu_window
        open_itu_window(self)

    def open_settings_window(self):
        from settings_window import SettingsWindow
        win = SettingsWindow(self)
        win.grab_set()

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
