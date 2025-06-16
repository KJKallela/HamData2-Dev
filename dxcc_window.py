import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from window_prefs import load_window_geometry, save_window_geometry
from config import get_pg_connection
import json

def open_dxcc_window(parent=None):
    window = tk.Toplevel(parent)
    window.title("DXCC Codes")

    geometry = load_window_geometry(window, "dxcc")
    if geometry:
        window.geometry(geometry)
    else:
        window.geometry("1000x500")

    window.protocol("WM_DELETE_WINDOW", lambda: on_close(window))

    frame = ttk.Frame(window)
    frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    columns = ("entity_code", "name", "country_code", "prefix", "prefix_regex", "cq",
               "itu", "notes", "outgoing_qsl_service", "third_party_traffic", "valid_start", "valid_end")

    tree = ttk.Treeview(frame, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col.replace("_", " ").title())
        tree.column(col, width=120, anchor="center")

    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(yscroll=vsb.set, xscroll=hsb.set)

    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")

    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)

    load_dxcc_data(tree)

    bottom = ttk.Frame(window)
    bottom.pack(fill=tk.X, side=tk.BOTTOM)

    import_btn = ttk.Button(bottom, text="Import...", command=lambda: import_dxcc_data(tree))
    import_btn.pack(side=tk.LEFT, padx=10, pady=5)

    close_btn = ttk.Button(bottom, text="Close", command=lambda: on_close(window))
    close_btn.pack(side=tk.RIGHT, padx=10, pady=5)

def load_dxcc_data(tree):
    tree.delete(*tree.get_children())
    try:
        conn = get_pg_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT entity_code, name, country_code, prefix, prefix_regex, cq, itu,
                   notes, outgoing_qsl_service, third_party_traffic, valid_start, valid_end
            FROM dxcc_codes ORDER BY entity_code
        """)
        rows = cursor.fetchall()
        for row in rows:
            row = list(row)
            for i, val in enumerate(row):
                if hasattr(val, "strftime"):
                    row[i] = val.strftime("%Y-%m-%d")
            tree.insert("", "end", values=row)
        cursor.close()
        conn.close()
    except Exception as e:
        messagebox.showerror("Error", f"Error loading DXCC data: {e}")

def import_dxcc_data(tree):
    file_path = filedialog.askopenfilename(
        title="Select DXCC Data File",
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
    )
    if not file_path:
        return

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        conn = get_pg_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM dxcc_codes")

        for item in data:
            cursor.execute("""
                INSERT INTO dxcc_codes (
                    entity_code, name, country_code, prefix, prefix_regex,
                    cq, itu, notes, outgoing_qsl_service, third_party_traffic,
                    valid_start, valid_end
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                item.get("entityCode"),
                item.get("name"),
                item.get("countryCode"),
                item.get("prefix"),
                item.get("prefixRegex"),
                item.get("cq"),
                item.get("itu"),
                item.get("notes"),
                item.get("outgoingQslService"),
                item.get("thirdPartyTraffic"),
                item.get("validStart"),
                item.get("validEnd")
            ))

        conn.commit()
        cursor.close()
        conn.close()

        load_dxcc_data(tree)
        messagebox.showinfo("Success", "DXCC codes imported successfully.")

    except Exception as e:
        messagebox.showerror("Import Error", f"Failed to import DXCC data:\n{e}")

def on_close(window):
    save_window_geometry(window, "dxcc")
    window.destroy()