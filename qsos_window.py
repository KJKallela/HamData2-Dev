import tkinter as tk
from tkinter import ttk, messagebox
from config import get_pg_connection
from window_prefs import load_window_geometry, save_window_geometry

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
        columns = ("qso_date", "time_on", "call_id", "freq", "mode", "operator_id")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=100)
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)

        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

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
                query = """
                SELECT qso_date, time_on, raw_call, freq, mode, raw_operator
                FROM qsos
                WHERE raw_call ILIKE %s
                ORDER BY qso_date DESC, time_on DESC
                LIMIT 500
                """
                like_filter = f"%{filter_text}%"
                cur.execute(query, (like_filter,))
            else:
                query = """
                SELECT qso_date, time_on, raw_call, freq, mode, raw_operator
                FROM qsos
                ORDER BY qso_date DESC, time_on DESC
                LIMIT 500
                """
                cur.execute(query)
            rows = cur.fetchall()
            cur.close()
            conn.close()

            # Clear treeview
            for item in self.tree.get_children():
                self.tree.delete(item)

            for row in rows:
                self.tree.insert("", "end", values=row)

        except Exception as e:
            messagebox.showerror("Error", f"Error loading QSOs:\n{e}")

    def on_close(self):
        save_window_geometry("qsos", self.geometry())
        self.destroy()
