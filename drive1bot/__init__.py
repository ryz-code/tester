import os
import aria2p
import threading
import subprocess
from pyrogram import Client
from datetime import datetime
from dotenv import load_dotenv


if os.path.exists('drive1bot.log'):
    with open('drive1bot.log', 'w') as f:
        pass
    
load_dotenv()


class OneDriveLog:
    def __init__(self):
        self.file_name = "drive1bot.log"
        self.current_datetime = datetime.now().strftime("%d/%m/%Y %I:%M:%S %p")

    def info(self, info_message):
        print(f"[+]: {info_message}")
        with open(self.file_name, "a") as f:
            f.write(f"[INFO]({self.current_datetime}): {info_message}\n")

    def error(self, error_message):
        print(f"[-]: {error_message}")
        with open(self.file_name, "a") as f:
            f.write(f"[ERROR]({self.current_datetime}): {error_message}\n")


log = OneDriveLog()


Interval = []

DOWNLOAD_DIR = "/path/to/drive1bot/downloads/"
DOWNLOAD_STATUS_UPDATE_INTERVAL = 3

AUTO_DELETE_MESSAGE_DURATION = 30

aria2 = aria2p.API(
    aria2p.Client(
        host="http://localhost",
        port=6800,
        secret="",
    )
)

aria2c = [
    "aria2c",
    "--enable-rpc",
    "--rpc-listen-all=false",
    "--rpc-listen-port", "6800",
    "--max-connection-per-server=10",
    "--rpc-max-request-size=1024M",
    "--seed-time=0.01",
    "--min-split-size=10M",
    "--follow-torrent=mem",
    "--split=10",
    "--daemon=true",
    "--allow-overwrite=true",
    "--max-overall-download-limit=0",
    "--max-overall-upload-limit=1K",
    "--max-concurrent-downloads=3"
]

subprocess.run(aria2c)

download_dict_lock = threading.Lock()
status_reply_dict_lock = threading.Lock()
status_reply_dict = {}
download_dict = {}


CLIENT_ID = os.environ.get("CLIENT_ID")
if len(CLIENT_ID) == 0:
    log.error("CLIENT_ID is missing")
    exit(1)


CLIENT_SECRET_VALUE = os.environ.get("CLIENT_SECRET_VALUE")
if len(CLIENT_ID) == 0:
    log.error("CLIENT_SECRET_VALUE is missing")
    exit(1)


REDIRECT_URI = os.environ.get("REDIRECT_URI")
if len(CLIENT_ID) == 0:
    log.error("REDIRECT_URI is missing")
    exit(1)
    

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if len(BOT_TOKEN) == 0:
    log.error("BOT_TOKEN is missing")
    exit(1)
    

OWNER_ID = os.environ.get('OWNER_ID', '')
if len(OWNER_ID) == 0:
    log.error("OWNER_ID variable is missing! Exiting now")
    exit(1)
else:
    OWNER_ID = int(OWNER_ID)
    
    
CHAT_ID = os.environ.get('CHAT_ID', '')
if len(CHAT_ID) == 0:
    log.error("CHAT_ID variable is missing! Exiting now")
    exit(1)
else:
    CHAT_ID = int(CHAT_ID)
    

API_ID = os.environ.get('API_ID', '')
API_HASH = os.environ.get('API_HASH', '')

plugins = dict(root="drive1bot/modules")
app = Client("drive1bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, plugins=plugins)
log.info("Starting Bot")
app.start()

BOT_NAME = app.get_me().first_name + (app.get_me().last_name or "")
