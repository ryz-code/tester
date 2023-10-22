import os
import time
from aria2p import API as a2API, Client as a2Client
import threading
import subprocess
from pyrogram import Client as pClient
from datetime import datetime
from dotenv import load_dotenv


file_names = ['megalog.txt', 'drive1bot.txt']
for file_name in file_names:
    if os.path.exists(file_name):
        with open(file_name, 'w') as f:
            pass
    
    
load_dotenv()

if os.environ.get('MEGA_USERNAME', None) is not None and os.environ.get('MEGA_PASSWORD', None) is not None:
    from pymegasdkrest import MegaSdkRestClient, errors as mega_err


class OneDriveLog:
    def __init__(self):
        self.file_name = "drive1bot.txt"
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

DOWNLOAD_DIR = "/app/downloads/"
DOWNLOAD_STATUS_UPDATE_INTERVAL = 5

AUTO_DELETE_MESSAGE_DURATION = 30

aria2 = a2API(
    a2Client(
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

USER_ID = os.environ.get('USER_ID', '')
USER_HASH = os.environ.get('USER_HASH', '')
SESSION_STRING = os.environ.get('SESSION_STRING', '')

app = pClient("drive1bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
userbot = pClient("drive1user", api_id=USER_ID, api_hash=USER_HASH, session_string=SESSION_STRING)

log.info("Starting Bot")
app.start()
log.info("Starting User")
userbot.start()

PREMIUM_USER = userbot.get_me().is_premium

BOT_NAME = app.get_me().first_name + (app.get_me().last_name or "")
USERBOT_NAME = userbot.get_me().first_name + (userbot.get_me().last_name or "")

MEGA_USERNAME = os.environ.get('MEGA_USERNAME', None)
if MEGA_USERNAME:
    if len(MEGA_USERNAME) == 0:
        log.error("MEGA_USERNAME variable is missing! Exiting now")
        exit(1)
    else:
        MEGA_USERNAME = MEGA_USERNAME
    
MEGA_PASSWORD = os.environ.get('MEGA_PASSWORD', None)
if MEGA_PASSWORD:
    if len(MEGA_PASSWORD) == 0:
        log.error("MEGA_PASSWORD variable is missing! Exiting now")
        exit(1)
    else:
        MEGA_PASSWORD = MEGA_PASSWORD


if MEGA_PASSWORD and MEGA_USERNAME:
    # Start megasdkrest binary
    ENV_VARS = {
        # "APP_PORT": "4000", # you can change port default is 6969
        # "MEGA_DEBUG": "false", # if you want debug log enable and make it "true"
        "APP_THREADS": "3",
        "MEGA_THREADS": "3",
        "LOG_FILE": "megalog.txt",
    }

    subprocess.Popen(["/usr/local/bin/megasdkrest"], env=ENV_VARS, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)  # Wait for the mega server to start listening
    mega_client = MegaSdkRestClient('http://localhost:6969')
    log.info("Mega Client Started")
    try:
        mega_client.login(MEGA_USERNAME, MEGA_PASSWORD)
    except mega_err.MegaSdkRestClientException as e:
        log.error(e.message['message'])
        exit(0)