
import os, json

PREF_FILE = "window_geometry.json"

def load_window_geometry(name_or_window, name=None):
    if isinstance(name_or_window, str):
        name = name_or_window
    data = {}
    if os.path.exists(PREF_FILE):
        with open(PREF_FILE, "r") as f:
            data = json.load(f)
    return data.get(name)

def save_window_geometry(window, name):
    geometry = window.geometry()
    data = {}
    if os.path.exists(PREF_FILE):
        with open(PREF_FILE, "r") as f:
            data = json.load(f)
    data[name] = geometry
    with open(PREF_FILE, "w") as f:
        json.dump(data, f)
