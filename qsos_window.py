
import tkinter as tk
from tkinter import ttk, messagebox
from config import get_pg_connection
from window_prefs import load_window_geometry, save_window_geometry
import datetime

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

        self.create_widgets()
        self.load_qsos()

    def create_widgets(self):
        # Filter label and entry
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(filter_frame, text="Filter Callsign:").pack(side="left")
        self.filter_var = tk.StringVar()
        self.filter_var.trace_add("write", lambda *_: self.load_qsos())
        self.filter_entry = ttk.Entry(filter_frame, textvariable=self.filter_var)
        self.filter_entry.pack(side="left", fill="x", expand=True)

        # Treeview for QSOs
        columns = ("qso_date", "time_on", "raw_call", "freq", "mode", "raw_operator")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title(),
                              command=lambda c=col: self.treeview_sort_column(c, False))
            self.tree.column(col, width=100)
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)

        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", self.on_row_double_click)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(self, textvariable=self.status_var, anchor="w", relief="sunken")
        self.status_bar.pack(fill="x", side="bottom")
        self.update_clock()

        # Bottom buttons frame
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=5, pady=5)

        self.close_btn = ttk.Button(btn_frame, text="Close", command=self.on_close)
        self.close_btn.pack(side="right")

    def load_qsos(self):
        filter_text = self.filter_var.get().strip()

        try:
            conn = get_pg_connection()
            cur = conn.cursor()
            if filter_text:
                query = """SELECT qso_date, time_on, raw_call, freq, mode, raw_operator
                           FROM qsos
                           WHERE raw_call ILIKE %s
                           ORDER BY qso_date DESC, time_on DESC
                           LIMIT 500"""
                like_filter = f"%{filter_text}%"
                cur.execute(query, (like_filter,))
            else:
                query = """SELECT qso_date, time_on, raw_call, freq, mode, raw_operator
                           FROM qsos
                           ORDER BY qso_date DESC, time_on DESC
                           LIMIT 500"""
                cur.execute(query)
            rows = cur.fetchall()

            # Total count
            cur.execute("SELECT COUNT(*) FROM qsos")
            total_count = cur.fetchone()[0]

            conn.close()

            self.tree.delete(*self.tree.get_children())
            for row in rows:
                self.tree.insert("", "end", values=row)

            existing = self.status_var.get().split(" | ")
            clock = existing[1] if len(existing) > 1 else ""
            self.status_var.set(f"QSOs {len(rows)}/{total_count} | {clock}")

        except Exception as e:
            messagebox.showerror("Error", f"Error loading QSOs:\n{e}")

    def update_clock(self):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status_text = self.status_var.get().split(" | ")[0]
        self.status_var.set(f"{status_text} | {now}")
        self.after(1000, self.update_clock)

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
                messagebox.showerror("Error", f"Unable to open detail view:\n{e}")

    def treeview_sort_column(self, col, reverse):
        data = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        try:
            data.sort(key=lambda t: float(t[0]), reverse=reverse)
        except ValueError:
            data.sort(key=lambda t: t[0], reverse=reverse)

        for index, (val, k) in enumerate(data):
            self.tree.move(k, '', index)

        self.tree.heading(col, command=lambda: self.treeview_sort_column(col, not reverse))

    def on_close(self):
        save_window_geometry("qsos", self.geometry())
        self.destroy()
