import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from window_prefs import load_window_geometry, save_window_geometry
from config import get_pg_connection

def open_itu_window(parent=None):
    window = tk.Toplevel(parent)
    window.title("ITU Zones")

    geometry = load_window_geometry(window, "itu")
    if geometry:
        window.geometry(geometry)
    else:
        window.geometry("700x450")

    window.protocol("WM_DELETE_WINDOW", lambda: on_close(window))

    frame = ttk.Frame(window)
    frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    columns = ("itu_code", "zone_name", "description")
    tree = ttk.Treeview(frame, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col.capitalize())
        tree.column(col, width=200)

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
        cursor.execute("SELECT itu_code, zone_name, description FROM itu_zones ORDER BY itu_code")
        rows = cursor.fetchall()
        for row in rows:
            tree.insert("", "end", values=row)
        cursor.close()
        conn.close()
    except Exception as e:
        messagebox.showerror("Error", f"Error loading ITU data: {e}")

def import_itu_data(tree):
    # Open file dialog
    file_path = filedialog.askopenfilename(
        title="Select ITU Zones Data File",
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
    )
    if not file_path:
        return

    try:
        import json
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Example: data is expected to be a list of dicts with keys matching DB fields
        conn = get_pg_connection()
        cursor = conn.cursor()

        # Clear existing data or do upsert logic
        cursor.execute("DELETE FROM itu_zones")

        for item in data:
            # Adjust keys to your DB schema
            cursor.execute("""
                INSERT INTO itu_zones (itu_code, zone_name, description)
                VALUES (%s, %s, %s)
            """, (item.get("itu_code"), item.get("zone_name"), item.get("description")))

        conn.commit()
        cursor.close()
        conn.close()

        load_itu_data(tree)
        messagebox.showinfo("Success", "ITU Zones data imported successfully.")

    except Exception as e:
        messagebox.showerror("Import Error", f"Failed to import ITU data:\n{e}")

def on_close(window):
    save_window_geometry(window, "itu")
    window.destroy()
