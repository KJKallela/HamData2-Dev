
import tkinter as tk
from tkinter import ttk, messagebox
from config import get_pg_connection
from window_prefs import load_window_geometry, save_window_geometry
from callsigns_detail import open_callsign_detail
import datetime

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

        # Frame to hold Treeview and scrollbars
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.tree = ttk.Treeview(tree_frame, columns=("callsign", "name", "lastseen"), show="headings")
        self.tree.heading("callsign", text="Callsign", command=lambda: self.sort_tree("callsign", False))
        self.tree.heading("name", text="Name", command=lambda: self.sort_tree("name", False))
        self.tree.heading("lastseen", text="Last Seen", command=lambda: self.sort_tree("lastseen", False))
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda event: self.open_detail())

        vscroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        vscroll.pack(side="right", fill="y")

        hscroll = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        hscroll.pack(fill="x")

        self.tree.configure(yscrollcommand=vscroll.set, xscrollcommand=hscroll.set)

        # Bottom status bar (always visible)
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(self, textvariable=self.status_var, relief="sunken", anchor="w")
        self.status_bar.pack(fill="x", side="bottom")
        self.update_clock()

        # Bottom buttons frame
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=5, pady=5)

        self.add_btn = ttk.Button(btn_frame, text="Add", command=self.add_callsign)
        self.add_btn.pack(side="left")

        self.delete_btn = ttk.Button(btn_frame, text="Delete", command=self.delete_callsign)
        self.delete_btn.pack(side="left", padx=(5, 0))

        self.detail_btn = ttk.Button(btn_frame, text="Details", command=self.open_detail)
        self.detail_btn.pack(side="left", padx=(5, 0))

        self.close_btn = ttk.Button(btn_frame, text="Close", command=self.on_close)
        self.close_btn.pack(side="right")

    def load_callsigns(self):
        filter_text = self.filter_var.get().strip()

        try:
            conn = get_pg_connection()
            cur = conn.cursor()
            if filter_text:
                query = """SELECT callsign, wholename, lastseen
                           FROM callsigns
                           WHERE callsign ILIKE %s OR wholename ILIKE %s
                           ORDER BY callsign"""
                like_filter = f"%{filter_text}%"
                cur.execute(query, (like_filter, like_filter))
            else:
                query = "SELECT callsign, wholename, lastseen FROM callsigns ORDER BY callsign"
                cur.execute(query)
            rows = cur.fetchall()
            cur.close()

            # Total and filtered count
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM callsigns")
            total_count = cur.fetchone()[0]
            cur.close()
            existing = self.status_var.get().split(" | ")
            clock = existing[1] if len(existing) > 1 else ""
            self.status_var.set(f"Calls {len(rows)}/{total_count} | {clock}")
            conn.close()

            self.tree.delete(*self.tree.get_children())
            for row in rows:
                self.tree.insert("", "end", values=row)

        except Exception as e:
            messagebox.showerror("Error", f"Error loading callsigns:\n{e}")

    def update_clock(self):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status_text = self.status_var.get().split(" | ")[0]
        self.status_var.set(f"{status_text} | {now}")
        self.after(1000, self.update_clock)

    def open_detail(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select a callsign.")
            return
        callsign = self.tree.item(selected[0])["values"][0]
        open_callsign_detail(callsign, parent_refresh_callback=lambda _: self.load_callsigns())

    def add_callsign(self):
        open_callsign_detail(None, parent_refresh_callback=lambda _: self.load_callsigns())

    def delete_callsign(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Info", "Please select a callsign to delete.")
            return
        callsign = self.tree.item(selected[0])["values"][0]
        if messagebox.askyesno("Confirm", f"Delete callsign '{callsign}'?"):
            try:
                conn = get_pg_connection()
                cur = conn.cursor()
                cur.execute("DELETE FROM callsigns WHERE callsign = %s", (callsign,))
                conn.commit()
                cur.close()
                conn.close()
                self.load_callsigns()
            except Exception as e:
                messagebox.showerror("Error", f"Error deleting callsign:\n{e}")

    def sort_tree(self, col, reverse):
        data = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        data.sort(reverse=reverse)
        for index, (val, k) in enumerate(data):
            self.tree.move(k, '', index)
        self.tree.heading(col, command=lambda: self.sort_tree(col, not reverse))

    def on_close(self):
        save_window_geometry("callsigns", self.geometry())
        self.destroy()
