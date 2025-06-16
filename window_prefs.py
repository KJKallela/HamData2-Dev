
from config import get_pg_connection

def save_window_geometry(name, geometry):
    try:
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO gen_settings (key, value) VALUES (%s, %s) "
                    "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value",
                    (f"{name}_geometry", geometry)
                )
                conn.commit()
    except Exception as e:
        print(f"Error saving geometry for {name}: {e}")

def load_window_geometry(name):
    try:
        with get_pg_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT value FROM gen_settings WHERE key = %s", (f"{name}_geometry",))
                row = cur.fetchone()
                return row[0] if row else ""
    except Exception:
        return ""
