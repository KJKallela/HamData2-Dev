import tkinter as tk
from tkinter import ttk, messagebox
from config import get_pg_connection
from window_prefs import load_window_geometry, save_window_geometry

def open_callsigns_window(master=None):
    CallsignsWindow(master)

class CallsignsWindow(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Callsigns")

        geom = load_window_geometry("callsigns")
        if geom:
            self.geometry(geom)
        else:
            self.geometry("900x600")

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.create_widgets()
        self.load_callsigns()

    def create_widgets(self):
        # Filter label and entry
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(filter_frame, text="Filter:").pack(side="left")
        self.filter_var = tk.StringVar()
        self.filter_var.trace_add("write", lambda *_: self.load_callsigns())
        self.filter_entry = ttk.Entry(filter_frame, textvariable=self.filter_var)
        self.filter_entry.pack(side="left", fill="x", expand=True)

        # Treeview for callsigns
        self.tree = ttk.Treeview(self, columns=("callsign", "name"), show="headings")
        self.tree.heading("callsign", text="Callsign")
        self.tree.heading("name", text="Name")
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)

        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # Bottom buttons frame
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=5, pady=5)

        self.detail_btn = ttk.Button(btn_frame, text="Details", command=self.open_detail)
        self.detail_btn.pack(side="left")

        self.close_btn = ttk.Button(btn_frame, text="Close", command=self.on_close)
        self.close_btn.pack(side="right")

    def load_callsigns(self):
        filter_text = self.filter_var.get().strip()

        try:
            conn = get_pg_connection()
            cur = conn.cursor()
            if filter_text:
                query = """
                SELECT callsign, wholename
                FROM callsigns
                WHERE callsign ILIKE %s OR wholename ILIKE %s
                ORDER BY callsign
                """
                like_filter = f"%{filter_text}%"
                cur.execute(query, (like_filter, like_filter))
            else:
                query = "SELECT callsign, wholename FROM callsigns ORDER BY callsign"
                cur.execute(query)
            rows = cur.fetchall()
            cur.close()
            conn.close()

            # Clear current treeview items
            for item in self.tree.get_children():
                self.tree.delete(item)

            for row in rows:
                self.tree.insert("", "end", values=row)

        except Exception as e:
            messagebox.showerror("Error", f"Error loading callsigns:\n{e}")

    def open_detail(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select a callsign.")
            return
        callsign = self.tree.item(selected[0])["values"][0]
        from callsigns_detail import open_callsign_detail
        open_callsign_detail(callsign, master=self)

    def on_close(self):
        save_window_geometry("callsigns", self.geometry())
        self.destroy()
