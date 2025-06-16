
import requests

import xml.etree.ElementTree as ET
import psycopg2
from config import DB_SETTINGS


def get_qrz_credentials():
    """Return (username, password) strings from gen_settings.

    Raises ValueError if either credential is missing.
    """
    with psycopg2.connect(**DB_SETTINGS) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT value FROM gen_settings WHERE key = 'qrz_username'")
            row_user = cur.fetchone()
            cur.execute("SELECT value FROM gen_settings WHERE key = 'qrz_password'")
            row_pass = cur.fetchone()

    username = row_user[0].strip() if row_user and row_user[0] else None
    password = row_pass[0].strip() if row_pass and row_pass[0] else None

    if not username or not password:
        raise ValueError("QRZ credentials not found in gen_settings (keys 'qrz_username'/'qrz_password').")

    return username, password


def qrz_login():
    username, password = get_qrz_credentials()
    url = f"https://xmldata.qrz.com/xml/current/?username={username};password={password};agent=HAMDataApp"
    response = requests.get(url)
    root = ET.fromstring(response.content)
    # Try to capture error message anywhere in the XML
    error_text = root.findtext('Session/Error') or root.findtext('Error') or root.findtext('.//Error')
    session = root.findtext('Session/key')
    if not session:
        if error_text:
            raise Exception(f'QRZ login failed: {error_text}')
        else:
            raise Exception('QRZ login failed: Unknown response')
        error = root.findtext('Session/Error') or "Unknown error"
        raise Exception(f"QRZ login failed: {error}")
    return session
def qrz_lookup(callsign):
    session = qrz_login()
    url = f"https://xmldata.qrz.com/xml/current/?s={session};callsign={callsign}"
    response = requests.get(url)
    root = ET.fromstring(response.content)
    call_data = root.find('Callsign')
    if call_data is None:
        raise Exception("No data found for this callsign")

    def get(tag):
        return call_data.findtext(tag, '').strip()

    return {
        'aliases': get('aliases'),
        'dxcc': int(get('dxcc') or 0),
        'qslinfo': get('qslmgr'),
        'wholename': get('name'),
        'bornyear': int(get('born') or 0),
        'addr1': get('addr1'),
        'addr2': get('addr2'),
        'state': get('state'),
        'zip': get('zip'),
        'country': get('country'),
        'lat': float(get('lat') or 0),
        'lon': float(get('lon') or 0),
        'grid': get('grid'),
    }

def update_callsign_in_db(callsign, data):
    conn = psycopg2.connect(**DB_SETTINGS)
    cur = conn.cursor()

    updates = ', '.join([f"{key} = %s" for key in data.keys()])
    values = list(data.values())
    values.append(callsign)

    cur.execute(f"""
        UPDATE callsigns
        SET {updates}, qrzupdate = now()
        WHERE callsign = %s
    """, values)

    conn.commit()
    cur.close()
    conn.close()


def update_callsign_from_qrz(callsign):
    data = qrz_lookup(callsign)
    update_callsign_in_db(callsign, data)
    return True
