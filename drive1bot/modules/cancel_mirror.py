from time import sleep
from pyrogram import filters
from drive1bot.helper.telegram_helper.message_utils import *
from drive1bot.helper.ext_utils.fs_utils import clean_download
from drive1bot.helper.telegram_helper.filters import owner_only_command
from drive1bot import download_dict, download_dict_lock, DOWNLOAD_DIR, app
from drive1bot.helper.ext_utils.bot_utils import getDownloadByGid, MirrorStatus



@app.on_message(filters.command("cancel"))
def cancel_mirror(_, message):
    args = message.text.split(" ", maxsplit=1)
    mirror_message = None
    if len(args) > 1:
        gid = args[1]
        dl = getDownloadByGid(gid)
        if not dl:
            sendMessage(f"GID: `{gid}` not found.", message)
            return
        mirror_message = dl.message
    elif message.reply_to_message:
        mirror_message = message.reply_to_message
        with download_dict_lock:
            dl = download_dict[mirror_message.id]
    if len(args) == 1:
        msg = "Please reply to the /mirror message which was used to start the download or /cancel gid to cancel it!"
        sendMessage(msg, message)
        return
    if dl.status() == "Uploading":
        sendMessage("Upload in Progress, Don't Cancel it.", message)
        return
    else:
        dl.download().cancel_download()
    sleep(1)  # Wait a Second For Aria2 To free Resources.
    clean_download(f'{DOWNLOAD_DIR}{mirror_message.id}/')


@owner_only_command("cancelall")
def cancel_all(_, message):
    with download_dict_lock:
        count = 0
        for dlDetails in list(download_dict.values()):
            if dlDetails.status() == MirrorStatus.STATUS_DOWNLOADING \
                    or dlDetails.status() == MirrorStatus.STATUS_WAITING:
                dlDetails.download().cancel_download()
                count += 1
    delete_all_messages()
    sendMessage(f'Cancelled {count} downloads!', message)