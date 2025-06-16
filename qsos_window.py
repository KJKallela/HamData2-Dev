# NOTE: To prevent column width errors, run this SQL:
# ALTER TABLE gen_settings
# ALTER COLUMN value TYPE VARCHAR(128);


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

        self.my_callsign = self.load_my_callsign()
        self.only_mine_var = tk.BooleanVar()
        self.only_mine_var.trace_add("write", lambda *_: self.on_filter_change())

        self.create_widgets()
        self.load_column_widths()
        self.load_qsos()

    def load_my_callsign(self):
        try:
            conn = get_pg_connection()
            cur = conn.cursor()
            cur.execute("SELECT value FROM gen_settings WHERE key = 'MY_HAMCALL'")
            row = cur.fetchone()
            cur.close()
            conn.close()
            return row[0].strip().upper() if row else None
        except Exception as e:
            print(f"Error loading MY_CALLSIGN: {e}")
            return None

    def create_widgets(self):
        # Filter label and entry
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill="x", padx=5, pady=5)

        # Only mine checkbox
        self.only_mine_cb = ttk.Checkbutton(
            filter_frame,
            text=f"Only {self.my_callsign}" if self.my_callsign else "Only <MY_HAMCALL>",
            variable=self.only_mine_var
        )
        self.only_mine_cb.pack(side="left")
        if not self.my_callsign:
            self.only_mine_cb.state(["disabled"])

        ttk.Label(filter_frame, text="Filter Callsign:").pack(side="left", padx=(10, 0))
        self.filter_var = tk.StringVar()
        self.filter_var.trace_add("write", lambda *_: self.on_filter_change())
        self.filter_entry = ttk.Entry(filter_frame, textvariable=self.filter_var)
        self.filter_entry.pack(side="left", fill="x", expand=True)

        # Treeview
        columns = ("qso_date", "time_on", "raw_call", "freq", "mode", "raw_operator")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title(),
                              command=lambda c=col: self.treeview_sort_column(c, False))
            self.tree.column(col, width=100)
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        hscrollbar = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(xscrollcommand=hscrollbar.set)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        hscrollbar.pack(side="bottom", fill="x")

        self.tree.bind("<Double-1>", self.on_row_double_click)

        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(self, textvariable=self.status_var, anchor="w", relief="sunken")
        self.status_bar.pack(fill="x", side="bottom")
        self.update_clock()

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=5, pady=5)
        self.close_btn = ttk.Button(btn_frame, text="Close", command=self.on_close)
        self.close_btn.pack(side="right")

    
    def on_filter_change(self):
        self.load_column_widths()
        self.load_qsos()

    def load_qsos(self):
        filter_text = self.filter_var.get().strip()
        try:
            conn = get_pg_connection()
            cur = conn.cursor()

            base_query = "SELECT qso_date, time_on, raw_call, freq, mode, raw_operator FROM qsos"
            where_clauses = []
            params = []

            if filter_text:
                where_clauses.append("(raw_call ILIKE %s)")
                params.append(f"%{filter_text}%")

            if self.my_callsign and self.only_mine_var.get():
                where_clauses.append("(raw_call = %s OR raw_operator = %s)")
                params.extend([self.my_callsign, self.my_callsign])

            query = base_query
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)

            query += " ORDER BY qso_date DESC, time_on DESC LIMIT 500"
            cur.execute(query, tuple(params))
            rows = cur.fetchall()

            cur.execute("SELECT COUNT(*) FROM qsos")
            total_count = cur.fetchone()[0]

            cur.close()
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
        self.save_column_widths()

        save_window_geometry("qsos", self.geometry())
        self.destroy()


    def save_column_widths(self):
        try:
            widths = {col: self.tree.column(col)['width'] for col in self.tree['columns']}
            conn = get_pg_connection()
            cur = conn.cursor()
            for col, width in widths.items():
                key = f"qsos_colwidth_{col}"
                cur.execute("INSERT INTO gen_settings (key, value) VALUES (%s, %s) "
                            "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value",
                            (key, str(width)))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Error saving column widths: {e}")

    def load_column_widths(self):
        try:
            conn = get_pg_connection()
            cur = conn.cursor()
            for col in self.tree['columns']:
                key = f"qsos_colwidth_{col}"
                cur.execute("SELECT value FROM gen_settings WHERE key = %s", (key,))
                row = cur.fetchone()
                if row:
                    self.tree.column(col, width=int(row[0]))
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Error loading column widths: {e}")
    