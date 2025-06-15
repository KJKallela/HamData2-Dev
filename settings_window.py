
import tkinter as tk
from tkinter import ttk, messagebox
from config import get_pg_connection
from window_prefs import load_window_geometry, save_window_geometry

def open_settings_window(master=None):
    SettingsWindow(master)

class SettingsWindow(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Settings")

        geom = load_window_geometry("settings")
        if geom:
            self.geometry(geom)
        else:
            self.geometry("600x400")

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.create_widgets()
        self.load_settings()

    def create_widgets(self):
        self.tree = ttk.Treeview(self, columns=("key", "value"), show="headings")
        self.tree.heading("key", text="Key")
        self.tree.heading("value", text="Value")
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)

        # Bottom buttons frame
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=5, pady=5)

        self.save_btn = ttk.Button(btn_frame, text="Save", command=self.save_settings)
        self.save_btn.pack(side="left")

        self.close_btn = ttk.Button(btn_frame, text="Close", command=self.on_close)
        self.close_btn.pack(side="right")

    def load_settings(self):
        try:
            conn = get_pg_connection()
            cur = conn.cursor()
            cur.execute("SELECT key, value FROM gen_settings ORDER BY key")
            rows = cur.fetchall()
            cur.close()
            conn.close()

            for row in self.tree.get_children():
                self.tree.delete(row)

            for key, val in rows:
                self.tree.insert("", "end", values=(key, val))

        except Exception as e:
            messagebox.showerror("Error", f"Error loading settings:\n{e}")

    def save_settings(self):
        try:
            conn = get_pg_connection()
            cur = conn.cursor()
            for item in self.tree.get_children():
                key, value = self.tree.item(item)["values"]
                cur.execute("""
                    INSERT INTO gen_settings (key, value)
                    VALUES (%s, %s)
                    ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
                """, (key, value))
            conn.commit()
            cur.close()
            conn.close()
            messagebox.showinfo("Success", "Settings saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Error saving settings:\n{e}")

    def on_close(self):
        save_window_geometry("settings", self.geometry())
        self.destroy()
