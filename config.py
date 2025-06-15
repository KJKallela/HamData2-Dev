import psycopg2

# config.py
DB_SETTINGS = {
    "host": "localhost",
    "port": 5432,
    "dbname": "HamData",
    "user": "postgres",
    "password": "PostiRessi22!"
}


def get_pg_connection():
    return psycopg2.connect(**DB_SETTINGS)


def get_setting(key):
    conn = get_pg_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT value FROM gen_settings WHERE key = %s", (key,))
            result = cur.fetchone()
            return result[0] if result else None
    finally:
        conn.close()


def set_setting(key, value):
    conn = get_pg_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO gen_settings (key, value)
                VALUES (%s, %s)
                ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
            """, (key, value))
        conn.commit()
    finally:
        conn.close()
