import os
import re
import psycopg2
from datetime import datetime, timedelta
from tkinter import filedialog, messagebox, Toplevel, Label, StringVar
from tkinter.ttk import Progressbar
from config import DB_SETTINGS

ADIF_FILE_TABLE = "imported_adif_files"

# Normalize callsign (e.g. OH0/OH3AA/M -> OH3AA)
def normalize_callsign(call):
    match = re.search(r"([A-Z0-9]+)$", call.replace("/", ""))
    return match.group(1) if match else call

def connect_db():
    return psycopg2.connect(**DB_SETTINGS)

def create_tables():
    with connect_db() as conn:
        with conn.cursor() as cur:
            cur.execute(f'''
                CREATE TABLE IF NOT EXISTS {ADIF_FILE_TABLE} (
                    filename TEXT PRIMARY KEY,
                    imported_at TIMESTAMP NOT NULL
                );
            ''')
            conn.commit()

def parse_adif_line(line):
    fields = {}
    matches = re.findall(r"<(\w+)(?::\d+)(?::\w+)?>((?:(?!<\w+:).)*)", line)
    for key, value in matches:
        fields[key.upper()] = value.strip()
    return fields

def get_or_create_callsign(callsign_str, qso_date):
    callsign_str = normalize_callsign(callsign_str)
    with connect_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, firstseen, lastseen FROM callsigns WHERE callsign = %s", (callsign_str,))
            row = cur.fetchone()
            if row:
                id_, firstseen, lastseen = row
                if not firstseen or qso_date < firstseen:
                    firstseen = qso_date
                if not lastseen or qso_date > lastseen:
                    lastseen = qso_date
                cur.execute("UPDATE callsigns SET firstseen = %s, lastseen = %s WHERE id = %s", (firstseen, lastseen, id_))
                conn.commit()
                return id_
            else:
                cur.execute("INSERT INTO callsigns (callsign, firstseen, lastseen) VALUES (%s, %s, %s) RETURNING id",
                            (callsign_str, qso_date, qso_date))
                id_ = cur.fetchone()[0]
                conn.commit()
                return id_

def create_progress_window(root, total):
    win = Toplevel(root)
    win.title("Import Progress")
    Label(win, text="Importing ADIF file...").pack(padx=10, pady=5)

    imported = StringVar(value="Imported: 0")
    updated = StringVar(value="Updated: 0")
    ignored = StringVar(value="Ignored: 0")

    Label(win, textvariable=imported).pack()
    Label(win, textvariable=updated).pack()
    Label(win, textvariable=ignored).pack()

    progress = Progressbar(win, length=300, maximum=total)
    progress.pack(padx=10, pady=10)

    return win, progress, imported, updated, ignored

def import_adi_file(file_path, root=None):
    create_tables()
    filename = os.path.basename(file_path)

    with connect_db() as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT imported_at FROM {ADIF_FILE_TABLE} WHERE filename = %s", (filename,))
            row = cur.fetchone()
            if row:
                last_time = row[0].strftime("%Y-%m-%d %H:%M")
                if not messagebox.askyesno("File Already Imported", f"The file {filename} was already imported at {last_time}. Import again?"):
                    return

    with open(file_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip().startswith("<") and "<EOR>" in line.upper()]

    if not lines:
        messagebox.showerror("Invalid File", "No valid ADIF records found.")
        return

    win, bar, imported_var, updated_var, ignored_var = (None, None, None, None, None)
    if root:
        win, bar, imported_var, updated_var, ignored_var = create_progress_window(root, len(lines))

    imported = updated = ignored = 0

    with connect_db() as conn:
        for i, line in enumerate(lines):
            fields = parse_adif_line(line)
            try:
                freq = float(fields.get("FREQ", 0))
                brg = int(fields.get("APP_PSKREP_BRG", 0))
                distance = float(fields.get("DISTANCE", 0))
                mode = fields.get("MODE", "").upper() or "UNKNOWN"
                operator = fields.get("OPERATOR", "")
                raw_operator = operator
                call = fields.get("CALL", "")
                raw_call = call
                my_grid = fields.get("MY_GRIDSQUARE", "")
                qso_date = datetime.strptime(fields.get("QSO_DATE", "19700101"), "%Y%m%d").date()
                time_on = datetime.strptime(fields.get("TIME_ON", "000000"), "%H%M%S").time()
                snr = int(fields.get("APP_PSKREP_SNR", 0))
                country = fields.get("COUNTRY", "")
                dxcc = int(fields.get("DXCC", 0))
                grid = fields.get("GRIDSQUARE", "")
                qso_complete = fields.get("QSO_COMPLETE", "1")
                swl = fields.get("SWL", "0") in ("1", "Y", "y", "true", "True")

                operator_id = get_or_create_callsign(operator, qso_date) if operator else None
                call_id = get_or_create_callsign(call, qso_date) if call else None

                with conn.cursor() as cur:
                    # Check for duplicates
                    cur.execute("""
                        SELECT id, qso_complete FROM qsos
                        WHERE operator_id = %s AND call_id = %s AND freq = %s
                        AND qso_date = %s AND ABS(EXTRACT(EPOCH FROM (time_on - %s))) <= 180
                    """, (operator_id, call_id, freq, qso_date, time_on))
                    dup = cur.fetchone()
                    if dup:
                        if qso_complete > (dup[1] or ''):
                            cur.execute("""
                                UPDATE qsos SET qso_complete = %s WHERE id = %s
                            """, (qso_complete, dup[0]))
                            updated += 1
                        else:
                            ignored += 1
                        continue

                    cur.execute("""
                        INSERT INTO qsos (freq, app_pskrep_brg, distance, mode, operator_id, call_id,
                            my_gridsquare, qso_date, time_on, app_pskrep_snr, raw_operator, raw_call,
                            country, dxcc, gridsquare, qso_complete, swl)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (freq, brg, distance, mode, operator_id, call_id, my_grid, qso_date, time_on,
                          snr, raw_operator, raw_call, country, dxcc, grid, qso_complete, swl))
                    imported += 1

            except Exception as e:
                ignored += 1

            if win:
                bar["value"] = i + 1
                imported_var.set(f"Imported: {imported}")
                updated_var.set(f"Updated: {updated}")
                ignored_var.set(f"Ignored: {ignored}")
                win.update()

        with conn.cursor() as cur:
            cur.execute(f"""
                INSERT INTO {ADIF_FILE_TABLE} (filename, imported_at)
                VALUES (%s, now())
                ON CONFLICT (filename) DO UPDATE SET imported_at = EXCLUDED.imported_at
            """, (filename,))
            conn.commit()

    if win:
        messagebox.showinfo("Import Complete", f"QSOs imported: {imported}\nUpdated: {updated}\nIgnored: {ignored}")
        win.destroy()
