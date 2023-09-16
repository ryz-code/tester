import threading
from drive1bot.modules.mirror import MirrorListener
from drive1bot.helper.ext_utils.bot_utils import setInterval
from drive1bot import Interval, DOWNLOAD_DIR, DOWNLOAD_STATUS_UPDATE_INTERVAL, app, OWNER_ID, CHAT_ID
from drive1bot.helper.telegram_helper.message_utils import update_all_messages, sendStatusMessage
from drive1bot.helper.mirror_utils.download_utils.youtube_dl_download_helper import YoutubeDLHelper
from pyrogram import filters


@app.on_message(filters.command("yt"))
def watch(_, message):
    if message.chat.id in [OWNER_ID, CHAT_ID]:
        _ytdownload(message, leech=False)

@app.on_message(filters.command("ytl"))
def watch(_, message):
    if message.chat.id in [OWNER_ID, CHAT_ID]:
        _ytdownload(message, leech=True)


def _ytdownload(message, leech=None):
    args = message.text.split(' ')
    try:
        link = args[1].strip()
    except IndexError:
        pass
    
    listener = MirrorListener(message, leech)
    ydl = YoutubeDLHelper(listener)
    threading.Thread(target=ydl.add_download,args=(link, f'{DOWNLOAD_DIR}{listener.uid}')).start()
    sendStatusMessage(message)
    if len(Interval) == 0:
        Interval.append(setInterval(DOWNLOAD_STATUS_UPDATE_INTERVAL, update_all_messages))