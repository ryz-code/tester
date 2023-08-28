import os
import pathlib
from drive1bot.helper.ext_utils import fs_utils, bot_utils
from drive1bot.helper.ext_utils.bot_utils import setInterval
from drive1bot.helper.telegram_helper.message_utils import *
from drive1bot.helper.mirror_utils.status_utils import listeners
from drive1bot.helper.mirror_utils.upload_utils import onedrivetool
from drive1bot.helper.mirror_utils.status_utils.upload_status import UploadStatus
from drive1bot.helper.mirror_utils.download_utils.aria2_download import AriaDownloadHelper

from drive1bot import (
    DOWNLOAD_DIR, DOWNLOAD_STATUS_UPDATE_INTERVAL, 
    download_dict, download_dict_lock, Interval, 
    OneDriveLog, app, CHAT_ID, OWNER_ID
)

ariaDlManager = AriaDownloadHelper()
ariaDlManager.start_listener()
    
from pyrogram import filters


log = OneDriveLog()


@app.on_message(filters.command("mirror"))
def mirroring(_, message):
    if message.chat.id in [OWNER_ID, CHAT_ID]:
        _mirror(message)


class MirrorListener(listeners.MirrorListeners):
    def __init__(self, message, tag=None):
        super().__init__(message)
        self.tag = tag

    def onDownloadStarted(self):
        pass

    def onDownloadProgress(self):
        # We are handling this on our own!
        pass

    def clean(self):
        try:
            Interval[0].cancel()
            del Interval[0]
            delete_all_messages()
        except IndexError:
            pass

    def onDownloadComplete(self):
        with download_dict_lock:
            log.info(f"Download completed: {download_dict[self.uid].name()}")
            download = download_dict[self.uid]
            name = download.name()
            size = download.size_raw()
            if name is None:
                name = os.listdir(f'{DOWNLOAD_DIR}{self.uid}')[0]
            m_path = f'{DOWNLOAD_DIR}{self.uid}/{name}'
        path = f'{DOWNLOAD_DIR}{self.uid}/{name}'
        up_name = pathlib.PurePath(path).name
        log.info(f"Upload Name : {up_name}")
        onedrive = onedrivetool.OneDriveHelper(up_name, self)
        if size == 0:
            size = fs_utils.get_path_size(m_path)
        upload_status = UploadStatus(onedrive, size, self)
        with download_dict_lock:
            download_dict[self.uid] = upload_status
        update_all_messages()
        onedrive.upload(up_name)

    def onDownloadError(self, error):
        error = error.replace('<', ' ')
        error = error.replace('>', ' ')
        log.info(self.message.chat.id)
        with download_dict_lock:
            try:
                download = download_dict[self.uid]
                del download_dict[self.uid]
                log.info(f"Deleting folder: {download.path()}")
                fs_utils.clean_download(download.path())
                log.info(str(download_dict))
            except Exception as e:
                log.error(str(e))
                pass
            count = len(download_dict)
        if self.message.from_user.username:
            uname = f"@{self.message.from_user.username}"
        else:
            uname = f"[{self.message.from_user.first_name}]({f'tg://user?id={self.message.from_user.id}'})"
        msg = f"{uname} your download has been stopped due to: {error}"
        sendMessage(msg, self.message)
        if count == 0:
            self.clean()
        else:
            update_all_messages()

    def onUploadStarted(self):
        pass

    def onUploadProgress(self):
        pass

    def onUploadComplete(self, link: str):
        with download_dict_lock:
            msg = f"[{download_dict[self.uid].name()}]({link}) ({download_dict[self.uid].size()})"
            log.info(f'Done Uploading {download_dict[self.uid].name()}')
            if self.tag is not None:
                msg += f'\ncc: @{self.tag}'
            try:
                fs_utils.clean_download(download_dict[self.uid].path())
            except FileNotFoundError:
                pass
            del download_dict[self.uid]
            count = len(download_dict)
        sendMessage(msg, self.message)
        if count == 0:
            self.clean()
        else:
            update_all_messages()

    def onUploadError(self, error):
        e_str = error.replace('<', '').replace('>', '')
        with download_dict_lock:
            try:
                fs_utils.clean_download(download_dict[self.uid].path())
            except FileNotFoundError:
                pass
            del download_dict[self.message.id]
            count = len(download_dict)
        sendMessage(e_str, self.message)
        if count == 0:
            self.clean()
        else:
            update_all_messages()


def _mirror(message):
    message_args = message.text.split(' ')
    try:
        link = message_args[1]
    except IndexError:
        link = ''
    log.info(link)
    link = link.strip()
    reply_to = message.reply_to_message
    if reply_to is not None:
        file = None
        tag = reply_to.from_user.username
        media_array = [reply_to.document, reply_to.video, reply_to.audio]
        for i in media_array:
            if i is not None:
                file = i
                break

        if len(link) == 0:
            if file is not None:
                if file.mime_type != "application/x-bittorrent":
                    listener = MirrorListener(message, tag)
                    sendStatusMessage(message)
                    if len(Interval) == 0:
                        Interval.append(setInterval(DOWNLOAD_STATUS_UPDATE_INTERVAL, update_all_messages))
                    return
                else:
                    link = file.get_file().file_path
    else:
        tag = None
    if not bot_utils.is_url(link) and not bot_utils.is_magnet(link):
        sendMessage('No download source provided', message)
        return

    listener = MirrorListener(message, tag)
    ariaDlManager.add_download(link, f'{DOWNLOAD_DIR}{listener.uid}/', listener)
    sendStatusMessage(message)
    if len(Interval) == 0:
        Interval.append(setInterval(DOWNLOAD_STATUS_UPDATE_INTERVAL, update_all_messages))