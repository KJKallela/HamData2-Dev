import psycopg2
from config import get_setting, set_setting
from config import get_pg_connection

def load_window_geometry(name):
    try:
        conn = get_pg_connection()
        cur = conn.cursor()
        cur.execute("SELECT value FROM gen_settings WHERE key = %s", (f"{name}_geometry",))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            return row[0]
    except Exception as e:
        print(f"Error loading geometry for {name}: {e}")
    return None

def save_window_geometry(name, geometry):
    try:
        conn = get_pg_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO gen_settings (key, value)
            VALUES (%s, %s)
            ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
        """, (f"{name}_geometry", geometry))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error saving geometry for {name}: {e}")


