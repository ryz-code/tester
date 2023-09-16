import os
import time
import mimetypes
from drive1bot.helper.ext_utils.bot_utils import *
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from drive1bot import OneDriveLog, DOWNLOAD_DIR, app, userbot, PREMIUM_USER


log = OneDriveLog()
DUMP_CHANNEL = int(os.environ.get('DUMP_CHANNEL'))
DUMP_CHANNEL_LINK = os.environ.get('DUMP_CHANNEL_LINK')


class PyroGramHelper:
    def __init__(self, name=None, listener=None):
        self.__listener = listener
        self.uploaded_bytes = 0
        self.start_time = 0
        self.last_uploaded = 0
        self.name = name
        
        
    def speed(self):
        """
        It calculates the average upload speed and returns it in bytes/seconds unit
        :return: Upload speed in bytes/second
        """
        try:
            return self.uploaded_bytes / (time.time() - self.start_time)
        except ZeroDivisionError:
            return 0


    def __upload_progress(self, current, total):
        chunk_size = current - self.last_uploaded
        self.last_uploaded = current
        self.uploaded_bytes += chunk_size
        

    def get_mime_type(self, file_path):
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type

            
    def upload_file(self, file_path, _):
        leeched_files = []
        skipped_count = 0
        
        def _send_file(file_path, mime_type):
            nonlocal leeched_files
            uploaded_file = self.send_file(DUMP_CHANNEL, file_path, mime_type)
            time.sleep(3) # for avoiding floodwait
            if uploaded_file:
                leeched_files.append((uploaded_file, len(leeched_files) + 1, file_path))
            
        def send_directory_files(directory_path):
            nonlocal skipped_count
            for root, _, files in os.walk(directory_path):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    mime_type = self.get_mime_type(file_path)
                    file_size = os.path.getsize(file_path)
                    
                    threshold = 3.95 * 1024 ** 3 if PREMIUM_USER else 1.95 * 1024 ** 3
                    if file_size > threshold:
                        skipped_count += 1
                    else:
                        _send_file(file_path, mime_type)

        if os.path.isdir(file_path):
            send_directory_files(file_path)
        else:
            mime_type = self.get_mime_type(file_path)
            file_size = os.path.getsize(file_path)

            threshold = 3.95 * 1024 ** 3 if PREMIUM_USER else 1.95 * 1024 ** 3
            if file_size > threshold:
                skipped_count += 1
            else:
                _send_file(file_path, mime_type)
        
        if leeched_files:
            message_links = "\n".join([f"{count}. [{file_path.split('/')[-1]}](https://t.me/c/{str(DUMP_CHANNEL)[4:]}/{file.id})" for file, count, file_path in leeched_files])
            success_count = len(leeched_files)

            final_message = f"**Total FIles**: {success_count}\n"
            final_message += f"**Skipped Files**: {skipped_count}\n\n" if skipped_count > 0 else "\n"
            final_message += f"➥ **__Your Files have been leeched. Access via Links__**:\n\n{message_links}\n\n"

            try:
                start_idx = 0
                end_idx = 0
                while end_idx < len(final_message):
                    end_idx += final_message.rfind('\n', start_idx, 4096 + start_idx)
                    final_message = final_message[start_idx:end_idx]
                    start_idx = end_idx
                else:
                    final_message = final_message
            except:
                pass
            
            buttons = InlineKeyboardButton("Join Dump Channel For Access", url=DUMP_CHANNEL_LINK)
            invite_link = InlineKeyboardMarkup([[buttons]])
            return final_message, invite_link
    
        
    def send_file(self, DUMP_CHANNEL, file_path, mime_type):
        file_size = os.path.getsize(file_path)
        if PREMIUM_USER and 1.95 * 1024 ** 3 < file_size < 3.95 * 1024 ** 3:
            log.info(f"Skipped upload due to size limit: {file_path}")
            return None

        sender = userbot if PREMIUM_USER else app
        
        if not mime_type:
            try:
                get = sender.send_document(DUMP_CHANNEL, document=file_path, progress=self.__upload_progress)
                return get
            except:
                pass
        else:
            try:
                if mime_type and mime_type.startswith('image'):
                    get = sender.send_photo(DUMP_CHANNEL, photo=file_path, progress=self.__upload_progress)
                elif mime_type and mime_type.startswith('audio'):
                    get = sender.send_audio(DUMP_CHANNEL, audio=file_path, progress=self.__upload_progress)
                elif mime_type and mime_type.startswith('video'):
                    get = sender.send_video(DUMP_CHANNEL, video=file_path, progress=self.__upload_progress)
                else:
                    get = sender.send_document(DUMP_CHANNEL, document=file_path, progress=self.__upload_progress)

                return get
            except:
                pass

    
    def upload(self, file_name):
        self.__listener.onUploadStarted()
        file_dir = f"{DOWNLOAD_DIR}{self.__listener.message.id}"
        file_path = f"{file_dir}/{file_name}"
        log.info(f"Uploading File: {file_path}")
        self.start_time = time.time()
        try:
            final_message, invite_link = self.upload_file(file_path, file_name)
            log.info(f"Uploaded To Telegram: {file_path}")
        except Exception as e:
            log.error(e)
            self.__listener.onUploadError(str(e))
            return
        self.__listener.onUploadComplete(invite_link, None, final_message)
        log.info("Deleting downloaded file/folder..")