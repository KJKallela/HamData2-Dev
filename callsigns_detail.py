import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os
import psycopg2
from config import DB_SETTINGS
import json

SETTINGS_FILE = "callsign_detail_size.json"

def load_window_size():
    try:
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    except:
        return {"width": 600, "height": 500}

def save_window_size(width, height):
    with open(SETTINGS_FILE, "w") as f:
        json.dump({"width": width, "height": height}, f)

def open_callsign_detail(callsign_str, parent_refresh_callback=None):
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

    window = tk.Toplevel()
    window.title(f"Details for {callsign_str}")
    window.geometry(f"{size['width']}x{size['height']}")
    window.minsize(400, 300)

    def on_resize(event):
        save_window_size(event.width, event.height)

    window.bind("<Configure>", on_resize)

    top_frame = ttk.Frame(window)
    top_frame.pack(fill=tk.X, padx=10, pady=10)

    text_frame = ttk.Frame(window)
    text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    bottom_frame = ttk.Frame(window)
    bottom_frame.pack(fill=tk.X, padx=10, pady=5)

    # Display callsign
    cs_label = tk.Label(top_frame, text=data['callsign'], font=("Arial", 20, "bold"), fg="blue")
    cs_label.grid(row=0, column=0, sticky="w")

    # Display image
    if data.get("image") and os.path.isfile(data["image"]):
        try:
            img = Image.open(data["image"])
            img.thumbnail((120, 120))
            photo = ImageTk.PhotoImage(img)
            img_label = tk.Label(top_frame, image=photo)
            img_label.image = photo
            img_label.grid(row=0, column=1, rowspan=6, padx=10, sticky="ne")
        except Exception as e:
            print("Failed to load image:", e)

    # Display selected fields
    row_index = 1
    for label, field in [
        ("Name", "wholename"),
        ("Address 1", "addr1"),
        ("Address 2", "addr2"),
        ("State/ZIP", ("state", "zip")),
        ("Country", "country")
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

    # Scrollable text field for all data
    text_widget = tk.Text(text_frame, wrap=tk.WORD)
    text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar = ttk.Scrollbar(text_frame, command=text_widget.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    text_widget.config(yscrollcommand=scrollbar.set)

    # Insert remaining fields
    for key in colnames:
        if key in ["callsign", "wholename", "addr1", "addr2", "state", "zip", "country", "image"]:
            continue
        text_widget.insert(tk.END, f"{key}: {data.get(key)}\n")
    text_widget.config(state=tk.DISABLED)

    # Close and QRZ buttons
    def handle_close():
        window.destroy()
        if parent_refresh_callback:
            parent_refresh_callback(callsign_str)

    def handle_qrz():
        updated = update_callsign_from_qrz(callsign_str)
        if updated:
            messagebox.showinfo("QRZ Update", f"{callsign_str} updated from QRZ.com.")
            window.destroy()
            open_callsign_detail(callsign_str, parent_refresh_callback)
        else:
            messagebox.showwarning("QRZ Update", f"Failed to update {callsign_str} from QRZ.com.")

    qrz_btn = ttk.Button(bottom_frame, text="QRZ...", command=handle_qrz)
    qrz_btn.pack(side=tk.LEFT)

    close_btn = ttk.Button(bottom_frame, text="Close", command=handle_close)
    close_btn.pack(side=tk.RIGHT)
