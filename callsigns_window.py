from datetime import datetime
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
        # --- Top filter bar ---
        filter_frame = ttk.Frame(self)
        filter_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.columnconfigure(0, weight=1)

        ttk.Label(filter_frame, text="Filter:").pack(side="left")
        self.filter_var = tk.StringVar()
        self.filter_var.trace_add("write", lambda *_: self.load_callsigns())
        self.filter_entry = ttk.Entry(filter_frame, textvariable=self.filter_var)
        self.filter_entry.pack(side="left", fill="x", expand=True)

        # --- Central treeview with scrollbar ---
        tree_frame = ttk.Frame(self)
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.rowconfigure(1, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        columns = ("callsign", "wholename")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title(),
                              command=lambda c=col: self.treeview_sort_column(c, False))
            self.tree.column(col, width=100)

        self.tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.bind("<Double-1>", self.on_row_double_click if hasattr(self, 'on_row_double_click') else lambda e: None)

        # --- Buttons (Close etc.) ---
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        self.close_btn = ttk.Button(btn_frame, text="Close", command=self.on_close)
        self.close_btn.pack(side="right")

        # --- Status bar ---
        self.status_frame = ttk.Frame(self)
        self.status_frame.grid(row=3, column=0, sticky="ew")
        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(self.status_frame, textvariable=self.status_var, anchor="w", relief="sunken")
        self.status_label.pack(side="left", fill="x", expand=True)

        self.clock_var = tk.StringVar()
        self.clock_label = ttk.Label(self.status_frame, textvariable=self.clock_var, anchor="e", relief="sunken")
        self.clock_label.pack(side="right")

        self.update_clock()
    
    def update_clock(self):
        self.clock_var.set(datetime.now().strftime("%H:%M:%S"))
        self.after(1000, self.update_clock)

    def load_callsigns(self):
        filter_text = self.filter_var.get().strip()

        try:
            conn = get_pg_connection()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM callsigns")
            total_records = cur.fetchone()[0]
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
            self.status_var.set(f"Callsigns: {len(rows)}/{total_records}")

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