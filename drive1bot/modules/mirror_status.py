import threading
from pyrogram import filters
from drive1bot.helper.telegram_helper.message_utils import *
from drive1bot.helper.ext_utils.bot_utils import get_readable_message
from drive1bot import status_reply_dict, app, status_reply_dict_lock, OWNER_ID, CHAT_ID


@app.on_message(filters.command("status"))
def mirror_status(_, message):
    if message.chat.id in [OWNER_ID, CHAT_ID]:
        msg = get_readable_message()
        if len(msg) == 0:
            message = "No active downloads"
            reply_message = sendMessage(msg, keyboard=None)
            threading.Thread(target=auto_delete_message, args=(message, reply_message)).start()
            return
        index = message.chat.id
        with status_reply_dict_lock:
            if index in status_reply_dict.keys():
                deleteMessage(status_reply_dict[index])
                del status_reply_dict[index]
        sendStatusMessage(message)
        deleteMessage(message)