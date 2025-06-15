
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from window_prefs import load_window_geometry, save_window_geometry
from config import get_pg_connection

def open_itu_window(parent=None):
    window = tk.Toplevel(parent)
    window.title("ITU Codes")

    geometry = load_window_geometry(window, "itu")
    if geometry:
        window.geometry(geometry)
    else:
        window.geometry("900x500")

    window.protocol("WM_DELETE_WINDOW", lambda: on_close(window))

    frame = ttk.Frame(window)
    frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    columns = ("code", "name", "fifa", "itu", "ioc", "id", "continent", "a2", "a3")
    tree = ttk.Treeview(frame, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col.upper())
        tree.column(col, width=100)

    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(yscroll=vsb.set, xscroll=hsb.set)
    tree.grid(row=0, column=0, sticky='nsew')
    vsb.grid(row=0, column=1, sticky='ns')
    hsb.grid(row=1, column=0, sticky='ew')

    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)

    load_itu_data(tree)

    bottom = ttk.Frame(window)
    bottom.pack(fill=tk.X, side=tk.BOTTOM)

    import_btn = ttk.Button(bottom, text="Import...", command=lambda: import_itu_data(tree))
    import_btn.pack(side=tk.LEFT, padx=10, pady=5)

    close_btn = ttk.Button(bottom, text="Close", command=lambda: on_close(window))
    close_btn.pack(side=tk.RIGHT, padx=10, pady=5)

def load_itu_data(tree):
    tree.delete(*tree.get_children())
    try:
        conn = get_pg_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT code, name, fifa, itu, ioc, id, continent, a2, a3
            FROM itu_codes ORDER BY code
        """)
        rows = cursor.fetchall()
        for row in rows:
            tree.insert("", "end", values=row)
        cursor.close()
        conn.close()
    except Exception as e:
        messagebox.showerror("Error", f"Error loading ITU codes: {e}")

def import_itu_data(tree):
    file_path = filedialog.askopenfilename(
        title="Select ITU Codes Data File",
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
    )
    if not file_path:
        return

    try:
        import json
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        conn = get_pg_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM itu_codes")

        for item in data:
            cursor.execute("""
                INSERT INTO itu_codes (
                    code, name, fifa, itu, ioc, id, continent, a2, a3
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                item.get("code"), item.get("name"), item.get("fifa"),
                item.get("itu"), item.get("ioc"), item.get("id"),
                item.get("continent"), item.get("a2"), item.get("a3")
            ))

        conn.commit()
        cursor.close()
        conn.close()

        load_itu_data(tree)
        messagebox.showinfo("Success", "ITU codes data imported successfully.")

    except Exception as e:
        messagebox.showerror("Import Error", f"Failed to import ITU data:\n{e}")

def on_close(window):
    save_window_geometry(window, "itu")
    window.destroy()
