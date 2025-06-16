import tkinter as tk
from tkinter import ttk, messagebox
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


class SettingsWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("General Settings")
        self.geometry("500x400")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.tree = ttk.Treeview(self, columns=("key", "value"), show="headings", selectmode="browse")
        self.tree.heading("key", text="Key")
        self.tree.heading("value", text="Value")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tree.bind("<Double-1>", self.on_double_click)

        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=5)

        ttk.Button(btn_frame, text="Add", command=self.add_row).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Delete", command=self.delete_row).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Save", command=self.save_changes).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Close", command=self.on_close).pack(side=tk.LEFT, padx=5)

        self.load_settings()

    def load_settings(self):
        try:
            with get_pg_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT key, value FROM gen_settings ORDER BY key")
                    rows = cur.fetchall()
                    self.tree.delete(*self.tree.get_children())
                    for row in rows:
                        self.tree.insert("", "end", values=row)
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to load settings:\n{e}")

    def add_row(self):
        self.tree.insert("", "end", values=("", ""))

    def delete_row(self):
        selected = self.tree.selection()
        if not selected:
            return
        self.tree.delete(selected[0])

    def on_double_click(self, event):
        item_id = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        if not item_id or column not in ("#1", "#2"):
            return

        col_index = int(column.strip("#")) - 1
        old_value = self.tree.item(item_id, "values")[col_index]

        entry = tk.Entry(self)
        entry.insert(0, old_value)
        entry.focus()
        entry.place(x=event.x_root - self.winfo_rootx(), y=event.y_root - self.winfo_rooty())

        def save_edit(event):
            new_value = entry.get()
            values = list(self.tree.item(item_id, "values"))
            values[col_index] = new_value
            self.tree.item(item_id, values=values)
            entry.destroy()

        entry.bind("<Return>", save_edit)
        entry.bind("<FocusOut>", lambda e: entry.destroy())

    def save_changes(self):
        try:
            with get_pg_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM gen_settings")  # clear all first
                    for item in self.tree.get_children():
                        key, value = self.tree.item(item, "values")
                        if key:  # skip blank keys
                            cur.execute(
                                "INSERT INTO gen_settings (key, value) VALUES (%s, %s)",
                                (key, value)
                            )
                conn.commit()
            messagebox.showinfo("Saved", "Settings saved successfully.")
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to save settings:\n{e}")

    def on_close(self):
        self.destroy()