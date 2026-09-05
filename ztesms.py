#!/usr/bin/env python3
import requests
import hashlib
import json
import os
import re

from config import ZTE_IP, ZTE_PWD, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

STATE_FILE = os.path.expanduser("~/zte_processed_sms.json")

session = requests.Session()
base_url = f"http://{ZTE_IP}"
headers = {"Referer": f"{base_url}/index.html"}

def sha256_up(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest().upper()

def decode_hex_content(hex_str):
    """ Decrypt ZTE UCS2-hex or text """
    if not hex_str:
        return ""
    try:
        # Check if its just hex
        if re.match(r'^[0-9a-fA-F]+$', hex_str) and len(hex_str) % 4 == 0:
            bytes_data = bytes.fromhex(hex_str)
            return bytes_data.decode('utf-16-be')
    except Exception:
        pass
    return hex_str

def parse_zte_date(date_str):
    """ Converts '26,09,01,00,19,57,+32' into '2026-09-01 00:19:57 (UTC+8)' """
    if not date_str:
        return "Unknown"
    
    parts = date_str.split(',')
    if len(parts) < 6:
        return date_str
    
    try:
        year = int(f"20{parts[0]}")
        month = int(parts[1])
        day = int(parts[2])
        hour = int(parts[3])
        minute = int(parts[4])
        second = int(parts[5])
        
        formatted_date = f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"
        
        if len(parts) >= 7:
            tz_raw = parts[6].replace('+', '')
            quarter_hours = int(tz_raw)
            tz_hours = quarter_hours // 4
            sign = "+" if quarter_hours >= 0 else "-"
            formatted_date += f" (UTC{sign}{abs(tz_hours)})"
            
        return formatted_date
    except Exception:
        return date_str


def load_processed_ids():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return set(json.load(f))
        except Exception:
            pass
    return set()

def save_processed_ids(ids):
    with open(STATE_FILE, "w") as f:
        json.dump(list(ids), f)

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        r = requests.post(url, data=payload, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"Telegram-error: {e}")
        return False

def main():
    processed_ids = load_processed_ids()

    # 1. Session & LD-token
    session.get(f"{base_url}/index.html", headers=headers)
    r_ld = session.get(f"{base_url}/goform/goform_get_cmd_process?isAsync=true&cmd=LD", headers=headers)
    ld_token = r_ld.json().get("LD", "")

    # 2. Login
    pass_h1 = sha256_up(ZTE_PWD)
    final_pass = sha256_up(pass_h1 + ld_token)

    login_res = session.post(f"{base_url}/goform/goform_set_cmd_process", data={
        "isAsync": "true",
        "goformId": "LOGIN",
        "password": final_pass
    }, headers=headers)

    if '"result":"0"' not in login_res.text:
        print("Login failed.")
        return

    # 3. SMS-module wakeup
    session.get(f"{base_url}/goform/goform_get_cmd_process", params={
        "isAsync": "true",
        "cmd": "sms_cmd_status_info",
        "sms_cmd": "1"
    }, headers=headers)

    # 4. Fetch messages
    sms_res = session.get(f"{base_url}/goform/goform_get_cmd_process", params={
        "isAsync": "true",
        "cmd": "sms_data_total",
        "page": "0",
        "data_per_page": "500",
        "mem_store": "1",
        "tags": "10",
        "order_by": "order by id desc"
    }, headers=headers)

    data = sms_res.json()
    messages = data.get("messages", [])

    new_count = 0
    for msg in reversed(messages):  # Old to newest process
        msg_id = str(msg.get("id"))
        
        if msg_id in processed_ids:
            continue

        sender = msg.get("number", "Unknown")
        raw_content = msg.get("content", "")
        decoded_body = decode_hex_content(raw_content)
        date_str = parse_zte_date(msg.get("date", ""))

        # Message to Telegram 
        tg_message = (
            f"<b>📩 New SMS received (ZTE)</b>\n"
            f"<b>Sender:</b> {sender}\n"
            f"<b>Time:</b> {date_str}\n"
            f"-----------------------------------\n"
            f"{decoded_body}"
        )

        print(f"Send message ID: {msg_id} ({sender})...")
        if send_telegram(tg_message):
            processed_ids.add(msg_id)
            new_count += 1

    if new_count > 0:
        save_processed_ids(processed_ids)
        print(f"Processed and sent {new_count} new messages.")
    else:
        print("No new messages.")

if __name__ == "__main__":
    main()
