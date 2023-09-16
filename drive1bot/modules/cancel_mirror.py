from time import sleep
from pyrogram import filters
from drive1bot.helper.telegram_helper.message_utils import *
from drive1bot.helper.ext_utils.fs_utils import clean_download
from drive1bot.helper.telegram_helper.filters import owner_only_command
from drive1bot import download_dict, download_dict_lock, DOWNLOAD_DIR, app
from drive1bot.helper.ext_utils.bot_utils import getDownloadByGid, MirrorStatus


@app.on_message(filters.regex(r'/cancel_.*'))
def cancel_mirror(_, message):
    args = message.text.split("@")[0].split("_")
    gid = args[1] if len(args) > 1 else None
    mirror_message = getDownloadByGid(gid).message if gid and getDownloadByGid(gid) else None
    if not mirror_message:
        if gid:
            sendMessage(f"GID: `{gid}` not found.", message, keyboard=None)
        return

    if message.from_user.id != mirror_message.from_user.id:
        sendMessage("It's not your mirror.", message, keyboard=None)
        return

    if mirror_message.id in download_dict:
        download = download_dict[mirror_message.id].download()
        download.cancel_download()
        sleep(1)
        clean_download(f'{DOWNLOAD_DIR}{mirror_message.id}')


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
    sendMessage(f'Cancelled {count} downloads!', message, keyboard=None)