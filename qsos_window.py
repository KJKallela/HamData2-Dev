
from datetime import datetime
import os
import tkinter as tk
from tkinter import ttk, messagebox
from config import get_pg_connection
from window_prefs import load_window_geometry, save_window_geometry


def get_my_callsign():
    """Return the user's own callsign.

    Priority:
    1. Value in gen_settings where key ILIKE 'MY_HAMCALL'
    2. Environment variable MY_HAMCALL
    3. Empty string
    """
    try:
        conn = get_pg_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT value FROM gen_settings WHERE key ILIKE %s", ('my_hamcall',))
            row = cur.fetchone()
            return row[0] if row and row[0] else os.getenv('MY_HAMCALL', '')
    except Exception:
        return os.getenv('MY_HAMCALL', '')


def open_qsos_window(master=None):
    QsosWindow(master)

class QsosWindow(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("QSOs")

        geom = load_window_geometry("qsos")
        if geom:
            self.geometry(geom)
        else:
            self.geometry("900x600")

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # own callsign for filtering
        self.my_call = get_my_callsign()

        self.only_mine_var = tk.BooleanVar(value=False)

        self.create_widgets()
        self.load_qsos()

    # ---------- UI ----------
    def create_widgets(self):
        # --- Top bar: Only‑mine checkbox + filter ---
        filter_frame = ttk.Frame(self)
        filter_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.columnconfigure(0, weight=1)

        # Checkbutton before the filter field
        self.only_mine_cb = ttk.Checkbutton(
            filter_frame,
            text="Only my QSOs",
            variable=self.only_mine_var,
            command=self.load_qsos
        )
        self.only_mine_cb.pack(side="left", padx=(0, 8))
        # Disable checkbox if MY_HAMCALL not set
        if not self.my_call:
            self.only_mine_cb.state(['disabled'])

        ttk.Label(filter_frame, text="Filter Callsign:").pack(side="left")
        self.filter_var = tk.StringVar()
        self.filter_var.trace_add("write", lambda *_: self.load_qsos())
        self.filter_entry = ttk.Entry(filter_frame, textvariable=self.filter_var)
        self.filter_entry.pack(side="left", fill="x", expand=True)

        # --- Central treeview with scrollbar ---
        tree_frame = ttk.Frame(self)
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.rowconfigure(1, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        columns = ("qso_date", "time_on", "raw_call", "freq", "mode", "raw_operator")
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

    # ---------- Data ----------
    def load_qsos(self):
        """Load QSOs into treeview honoring filter text and only‑mine checkbox."""
        filter_text = self.filter_var.get().strip()

        try:
            conn = get_pg_connection()
            cur = conn.cursor()

            # Get total number of rows in the table (for the status bar)
            cur.execute("SELECT COUNT(*) FROM qsos")
            total_records = cur.fetchone()[0]

            # Build main query
            base_query = '''
                SELECT qso_date, time_on, raw_call, freq, mode, raw_operator
                FROM qsos
                WHERE 1 = 1
            '''
            params = []

            if self.only_mine_var.get() and self.my_call:
                base_query += " AND (raw_operator ILIKE %s OR raw_call ILIKE %s)"
                params.extend([self.my_call, self.my_call])

            if filter_text:
                base_query += " AND raw_call ILIKE %s"
                params.append(f"%{filter_text}%")

            base_query += " ORDER BY qso_date DESC, time_on DESC LIMIT 500"

            cur.execute(base_query, tuple(params))
            rows = cur.fetchall()
            cur.close()
            conn.close()

            # Populate treeview
            self.tree.delete(*self.tree.get_children())
            for row in rows:
                self.tree.insert("", "end", values=row)

            # Update record count
            self.status_var.set(f"QSOs: {len(rows)}/{total_records}")

        except Exception as e:
            messagebox.showerror("Error", f"Error loading QSOs:\n{e}")

    # ---------- Helpers ----------
    def update_clock(self):
        self.clock_var.set(datetime.now().strftime("%H:%M:%S"))
        self.after(1000, self.update_clock)

    def treeview_sort_column(self, col, reverse):
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        try:
            l.sort(key=lambda t: float(t[0]), reverse=reverse)
        except ValueError:
            l.sort(reverse=reverse)
        for index, (val, k) in enumerate(l):
            self.tree.move(k, '', index)
        self.tree.heading(col, command=lambda: self.treeview_sort_column(col, not reverse))

    def on_row_double_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        row_data = self.tree.item(item, "values")
        if len(row_data) >= 3:
            raw_call = row_data[2]
            try:
                from callsign_detail import open_callsign_detail_window
                open_callsign_detail_window(self, raw_call)
            except Exception as e:
                messagebox.showerror("Error", f"Error opening Callsign detail:\n{e}")

    def on_close(self):
        save_window_geometry("qsos", self.geometry())
        self.destroy()
