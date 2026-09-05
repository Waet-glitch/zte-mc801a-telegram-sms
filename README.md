# ZTE MC801A SMS to Telegram Forwarder

A lightweight Python script to automatically read SMS messages from the **ZTE MC801A 5G Gateway** and forward them to a Telegram chat or channel.

## Key Features

* **Authentication Handling:** Handles ZTE's double SHA-256 password hashing protocol `SHA256(SHA256(password) + LD_token)`.
* **API Bypass:** Interacts with the hidden `goform_get_cmd_process` endpoint using exact WebUI query ordering (`order_by="order by id desc"`).
* **Text Decoding:** Decodes ZTE's raw UCS2 / UTF-16BE hex-encoded message payloads into clean text.
* **Timestamp Formatting:** Parses proprietary ZTE comma-delimited time strings (`YY,MM,DD,HH,MM,SS,+TZ`) into standard formatted dates with UTC offset support.
* **State Tracking:** Tracks forwarded message IDs locally in `processed_sms.json` to prevent duplicate Telegram alerts.

---

## Installation & Setup

### 1. Dependencies
Ensure you have Python 3 and `requests` installed:

sudo apt update
sudo apt install python3 python3-requests -y

### 2. Configuration
Copy the template configuration file to config.py:

cp config.py.example config.py

Edit config.py with your gateway credentials and Telegram bot details:

ZTE_IP = "192.168.2.52"              # Router IP
ZTE_PWD = "your_router_password"     # WebUI Admin Password

TELEGRAM_BOT_TOKEN = "your_bot_token"# From @BotFather
TELEGRAM_CHAT_ID = "your_chat_id"    # Your chat ID

### 3. Usage
Run the script manually to test:

python3 ztesms.py

Project Structure

ztesms/
├── ztesms.py           # Main execution script
├── config.py           # Private credentials (git-ignored)
├── config.py.example   # Configuration template
├── processed_sms.json  # Tracks forwarded SMS IDs (auto-generated, git-ignored)
└── README.md           # Documentation

### License
MIT License. Free to use, modify, and distribute.


