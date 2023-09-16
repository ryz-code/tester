import os
import pathlib
from drive1bot.helper.ext_utils import fs_utils, bot_utils
from drive1bot.helper.ext_utils.bot_utils import setInterval
from drive1bot.helper.telegram_helper.message_utils import *
from drive1bot.helper.mirror_utils.status_utils import listeners
from drive1bot.helper.mirror_utils.upload_utils import onedrivetool
from drive1bot.helper.mirror_utils.upload_utils import pyrogramtool
from drive1bot.helper.mirror_utils.status_utils.upload_status import UploadStatus
from drive1bot.helper.mirror_utils.download_utils.aria2_download import AriaDownloadHelper
from drive1bot.helper.mirror_utils.download_utils.telegram_downloader import TelegramDownloadHelper
from drive1bot.helper.mirror_utils.download_utils.mega_download import MegaDownloader

from drive1bot import (
    DOWNLOAD_DIR, DOWNLOAD_STATUS_UPDATE_INTERVAL, 
    download_dict, download_dict_lock, Interval, 
    OneDriveLog, app, CHAT_ID, OWNER_ID
)
from pyrogram import filters

ariaDlManager = AriaDownloadHelper()
ariaDlManager.start_listener()
log = OneDriveLog()


@app.on_message(filters.command("mirror"))
def mirroring(_, message):
    if message.chat.id in [OWNER_ID, CHAT_ID]:
        _mirror(message, leech=False)
        

@app.on_message(filters.command("leech"))
def mirroring(_, message):
    if message.chat.id in [OWNER_ID, CHAT_ID]:
        _mirror(message, leech=True)


class MirrorListener(listeners.MirrorListeners):
    def __init__(self, message, leech=None):
        super().__init__(message)
        self.__leech = leech

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
            # m_path = f'{DOWNLOAD_DIR}{self.uid}/{name}'
        path = f'{DOWNLOAD_DIR}{self.uid}/{name}'
        up_name = pathlib.PurePath(path).name
        log.info(f"Upload Name : {up_name}")
        if self.__leech:
            _pyrogram = pyrogramtool.PyroGramHelper(up_name, self)
            if size == 0:
                size = fs_utils.get_path_size(path)
            upload_status = UploadStatus(_pyrogram, size, self)
            with download_dict_lock:
                download_dict[self.uid] = upload_status
            update_all_messages()
            _pyrogram.upload(up_name)
        else:
            onedrive = onedrivetool.OneDriveHelper(up_name, self)
            if size == 0:
                size = fs_utils.get_path_size(path)
            upload_status = UploadStatus(onedrive, size, self)
            with download_dict_lock:
                download_dict[self.uid] = upload_status
            update_all_messages()
            onedrive.upload(up_name)
            

    def onDownloadError(self, error):
        error = error.replace('<', ' ').replace('>', ' ')
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
        sendMessage(msg, self.message, keyboard=None)
        if count == 0:
            self.clean()
        else:
            update_all_messages()

    def onUploadStarted(self):
        pass

    def onUploadProgress(self):
        pass

    def onUploadComplete(self, index_url_keyboard, mime_type, final_messages=None):
        with download_dict_lock:
            uname = f"@{self.message.from_user.username}"
            if not uname:
                uname = f"[{self.message.from_user.first_name}]({f'tg://user?id={self.message.from_user.id}'})"
            
            final_message = (
                f"**Name**: `{download_dict[self.uid].name()}`\n"
                f"**Size**: {download_dict[self.uid].size()}\n"
                f"**By**: {uname}\n"
            )
            
            if final_messages is not None:
                _final_message = f"**Total Files**: {final_messages}" if isinstance(final_messages, int) else final_messages
                final_message += str(_final_message)
            
            if mime_type is not None:
                final_message += f"**Mime Type**: {mime_type}"
        
            log.info(f'Done Uploading {download_dict[self.uid].name()}')
            try:
                fs_utils.clean_download(download_dict[self.uid].path())
            except FileNotFoundError:
                pass
            del download_dict[self.uid]
            count = len(download_dict)
            
        sendMessage(final_message, self.message, keyboard=index_url_keyboard)
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
        sendMessage(e_str, self.message, keyboard=None)
        if count == 0:
            self.clean()
        else:
            update_all_messages()


def _mirror(message, leech=None):
    message_args = message.text.split(' ')
    try:
        link = message_args[1].strip()
    except IndexError:
        link = ''
    log.info(link)
    
    reply_to = message.reply_to_message
    if reply_to is not None:
        file = None
        media_array = [reply_to.document, reply_to.video, reply_to.audio]
        for i in media_array:
            if i is not None:
                file = i
                break
        if len(link) == 0:
            if file is not None:
                if file.mime_type != "application/x-bittorrent":
                    listener = MirrorListener(message, leech)
                    tg_downloader = TelegramDownloadHelper(listener)
                    tg_downloader.add_download(reply_to, f'{DOWNLOAD_DIR}{listener.uid}/')
                    sendStatusMessage(message)
                    if len(Interval) == 0:
                        Interval.append(setInterval(DOWNLOAD_STATUS_UPDATE_INTERVAL, update_all_messages))
                    return
                else:
                    link = file.get_file().file_path
    
    if not bot_utils.is_url(link) and not bot_utils.is_magnet(link):
        sendMessage('No download source provided', message, keyboard=None)
        return

    listener = MirrorListener(message, leech)
    if bot_utils.is_mega_link(link):
        mega_dl = MegaDownloader(listener)
        mega_dl.add_download(link, f'{DOWNLOAD_DIR}{listener.uid}/')
    else:
        ariaDlManager.add_download(link, f'{DOWNLOAD_DIR}{listener.uid}/', listener)
    sendStatusMessage(message)
    if len(Interval) == 0:
        Interval.append(setInterval(DOWNLOAD_STATUS_UPDATE_INTERVAL, update_all_messages))