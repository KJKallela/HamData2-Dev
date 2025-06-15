
DB_SETTINGS = {
    "host": "localhost",
    "port": 5432,
    "database": "HamData",
    "user": "postgres",
    "password": "PostiRessi22!"
}

import psycopg2

def get_pg_connection():
    return psycopg2.connect(
        dbname=DB_SETTINGS["database"],
        user=DB_SETTINGS["user"],
        password=DB_SETTINGS["password"],
        host=DB_SETTINGS["host"],
        port=DB_SETTINGS["port"]
    )
