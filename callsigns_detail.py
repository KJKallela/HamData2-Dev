
"""Detail window for a single callsign.

Cleaned and auto‑formatted (4‑space indents)."""

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os
import psycopg2
from config import DB_SETTINGS
import json

from qrz_api import update_callsign_from_qrz

SETTINGS_FILE = "callsign_detail_size.json"


def load_window_size():
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"width": 600, "height": 500}


def save_window_size(width: int, height: int) -> None:
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump({"width": width, "height": height}, f)


def open_callsign_detail(callsign_str: str, parent_refresh_callback=None):
    """Open a Toplevel window showing details for *callsign_str*.

    If *parent_refresh_callback* is provided, call it when the detail window
    closes or after a successful QRZ update so the parent list refreshes.
    """
    # ------------------------------------------------------------------
    # Load row from DB --------------------------------------------------
    conn = psycopg2.connect(**DB_SETTINGS)
    cur = conn.cursor()
    cur.execute("SELECT * FROM callsigns WHERE callsign = %s", (callsign_str,))
    row = cur.fetchone()
    colnames = [desc[0] for desc in cur.description]
    cur.close()
    conn.close()

    if not row:
        messagebox.showerror("Error", f"Callsign {callsign_str} not found.")
        return

    data = dict(zip(colnames, row))
    size = load_window_size()

    # ------------------------------------------------------------------
    # Build UI ----------------------------------------------------------
    window = tk.Toplevel()
    window.title(f"Details for {callsign_str}")
    window.geometry(f"{size['width']}x{size['height']}")
    window.minsize(400, 300)

    # Save geometry on resize
    def on_resize(event):
        save_window_size(event.width, event.height)

    window.bind("<Configure>", on_resize)

    # Top frame --------------------------------------------------------
    top_frame = ttk.Frame(window)
    top_frame.pack(fill=tk.X, padx=10, pady=10)

    # Callsign label
    cs_label = tk.Label(
        top_frame,
        text=data['callsign'],
        font=("Arial", 20, "bold"),
        fg="blue"
    )
    cs_label.grid(row=0, column=0, sticky="w")

    # Portrait if present
    if data.get("image") and os.path.isfile(data["image"]):
        try:
            img = Image.open(data["image"])
            img.thumbnail((120, 120))
            photo = ImageTk.PhotoImage(img)
            img_label = tk.Label(top_frame, image=photo)
            img_label.image = photo  # keep ref
            img_label.grid(row=0, column=1, rowspan=6, padx=10, sticky="ne")
        except Exception as exc:
            print("Failed to load image:", exc)

    # Selected address / name fields
    row_index = 1
    for label, field in [
        ("Name", "wholename"),
        ("Address 1", "addr1"),
        ("Address 2", "addr2"),
        ("State/ZIP", ("state", "zip")),
        ("Country", "country"),
    ]:
        value = ""
        if isinstance(field, tuple):
            value = f"{data.get(field[0], '')} {data.get(field[1], '')}".strip()
        else:
            value = data.get(field, "")

        if value:
            lbl = tk.Label(top_frame, text=value, font=("Arial", 14))
            lbl.grid(row=row_index, column=0, sticky="w", pady=2)
            row_index += 1

    # Text frame for all columns --------------------------------------
    text_frame = ttk.Frame(window)
    text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    text_widget = tk.Text(text_frame, wrap=tk.NONE, height=10)
    text_widget.pack(fill=tk.BOTH, expand=True)

    # Put every column key/value
    for k, v in data.items():
        text_widget.insert(tk.END, f"{k}: {v}\n")
    text_widget.config(state=tk.DISABLED)

    # Bottom frame -----------------------------------------------------
    bottom_frame = ttk.Frame(window)
    bottom_frame.pack(fill=tk.X, padx=10, pady=5)

    # Handlers ---------------------------------------------------------
    def handle_close():
        window.destroy()
        if parent_refresh_callback:
            parent_refresh_callback()

    def handle_qrz():
        if not messagebox.askyesno(
            "QRZ Lookup",
            f"Download fresh data for {callsign_str} from QRZ.com?"
        ):
            return
        try:
            updated = update_callsign_from_qrz(callsign_str)
            if updated:
                messagebox.showinfo(
                    "QRZ Update", f"{callsign_str} updated from QRZ.com."
                )
                window.destroy()
                if parent_refresh_callback:
                    parent_refresh_callback()
                open_callsign_detail(callsign_str, parent_refresh_callback)
            else:
                messagebox.showwarning(
                    "QRZ Update", f"Failed to update {callsign_str} from QRZ.com."
                )
        except Exception as exc:
            messagebox.showerror("QRZ Error", str(exc))

    # Buttons ----------------------------------------------------------
    qrz_btn = ttk.Button(bottom_frame, text="QRZ...", command=handle_qrz)
    qrz_btn.pack(side=tk.LEFT, padx=(0, 5))

    close_btn = ttk.Button(bottom_frame, text="Close", command=handle_close)
    close_btn.pack(side=tk.RIGHT)
