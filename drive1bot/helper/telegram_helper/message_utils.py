import time
from pyrogram.enums import ParseMode
from drive1bot.helper.ext_utils.bot_utils import get_readable_message
from drive1bot import AUTO_DELETE_MESSAGE_DURATION, OneDriveLog, status_reply_dict, status_reply_dict_lock


log = OneDriveLog()

def sendMessage(text, message):
    return message.reply(
        text=text, 
        parse_mode=ParseMode.MARKDOWN
    )


def editMessage(text: str, message):
    message.edit(
        text=text,
        parse_mode=ParseMode.MARKDOWN
    )


def deleteMessage(message):
    message.delete()


def auto_delete_message(cmd_message, bot_message):
    if AUTO_DELETE_MESSAGE_DURATION != -1:
        time.sleep(AUTO_DELETE_MESSAGE_DURATION)
        try:
            # Skip if None is passed meaning we don't want to delete bot xor cmd message
            deleteMessage(cmd_message)
            deleteMessage(bot_message)
        except AttributeError:
            pass

def delete_all_messages():
    with status_reply_dict_lock:
        for message in list(status_reply_dict.values()):
            try:
                deleteMessage(message)
                del status_reply_dict[message.chat.id]
            except Exception as e:
                log.error(str(e))
                
def update_all_messages():
    msg = get_readable_message()
    with status_reply_dict_lock:
        for chat_id in list(status_reply_dict.keys()):
            if status_reply_dict[chat_id] and msg != status_reply_dict[chat_id].text:
                try:
                    editMessage(msg, status_reply_dict[chat_id])
                except Exception as e:
                    log.error(str(e))
                status_reply_dict[chat_id].text = msg
                
def sendStatusMessage(msg):
    progress = get_readable_message()
    with status_reply_dict_lock:
        if msg.chat.id in list(status_reply_dict.keys()):
            try:
                message = status_reply_dict[msg.chat.id]
                deleteMessage(message)
                del status_reply_dict[msg.chat.id]
            except Exception as e:
                log.error(str(e))
                del status_reply_dict[msg.chat.id]
        message = sendMessage(progress, msg)
        status_reply_dict[msg.chat.id] = message