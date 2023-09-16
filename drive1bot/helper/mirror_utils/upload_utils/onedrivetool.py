import os
import time
import requests
from urllib.parse import quote
from dotenv import load_dotenv
from drive1bot import OneDriveLog, DOWNLOAD_DIR
from drive1bot.helper.ext_utils.bot_utils import *
from drive1bot.msgraphauth import MicrosoftGraphAuth
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


load_dotenv()
log = OneDriveLog()

auth_manager = MicrosoftGraphAuth()
HEADERS = auth_manager.headers()
DRIVE_URI = os.getenv("DRIVE_URI")

VIDEO_MIMETYPES = {
    "mp4": "video/mp4",
    "mkv": "video/x-matroska",
    "avi": "video/x-msvideo",
    "mov": "video/quicktime",
    "flv": "video/x-flv",
    "m4a": "audio/mp4",
    "mp3": "audio/mpeg",
    "webm": "video/webm",
    "jpg": "image/jpg",
    "jpeg": "image/jpeg",
    "png": "image/png"
}


class OneDriveHelper:
    def __init__(self, name=None, listener=None):
        self.__listener = listener
        self.uploaded_bytes = 0
        self.total_size = 0
        self.start_time = 0
        self.total_time = 0
        self.progress = 0
        self.name = name
        self.is_uploading = True
        self.is_cancelled = False
        self.status = False
        self.updater = None
        self.update_interval = 3
        self._file_uploaded_bytes = 0
    
    
    def cancel(self):
        self.is_cancelled = True
        self.is_uploading = False
        
    def speed(self):
        """
        It calculates the average upload speed and returns it in bytes/seconds unit
        :return: Upload speed in bytes/second
        """
        try:
            return self.uploaded_bytes / self.total_time
        except ZeroDivisionError:
            return 0
    
        
    def _on_upload_progress(self):
        if self.status:
            self._file_uploaded_bytes = self.total_size * self.progress
            chunk_size = self.total_size * self.progress - self._file_uploaded_bytes
            self.uploaded_bytes += chunk_size
            self.total_time += self.update_interval
    
        
    def upload_file(self, file_path, file_name):
        request_url = f"https://graph.microsoft.com/v1.0/me/drive/root:/{quote(file_name)}:/createUploadSession"
        response = requests.post(request_url, headers=HEADERS)
        upload_url = response.json()["uploadUrl"]
        
        self.total_size = os.path.getsize(file_path)
        chunk_size = 1024 * 320 * 16
        
        timeout = (10.0, 180.0)
        client = requests.Session()
        client.timeout = timeout
        
        data = open(file_path, 'rb')
        self.start_time = time.time()
        
        while data.tell() < self.total_size:
            content_range_start = data.tell()
            content_range_end = min(content_range_start + chunk_size - 1, self.total_size - 1)
            header = {
                "Content-Range": f"bytes {content_range_start}-{content_range_end}/{self.total_size}"
            }
            content = data.read(chunk_size)
            
            response = client.put(
                upload_url,
                headers=header,
                data=content,
            )
            
            self.uploaded_bytes += len(content)
            self.progress = (self.uploaded_bytes / self.total_size) * 100
            self.status = True
        
        data.close()
        client.close()
        
        extension = file_name.split(".")[-1]
        mime_type = None
        if extension in VIDEO_MIMETYPES:
            mime_type = VIDEO_MIMETYPES[extension]
        index_view_url = f"{os.environ.get('INDEX_DOMAIN')}/{quote(file_name)}"
        index_url = f"{os.environ.get('INDEX_DOMAIN')}/api/raw/?path=/{quote(file_name)}"
        buttons = [InlineKeyboardButton("Download", url=index_url)]
        if mime_type is not None:
            buttons.insert(1, InlineKeyboardButton("View", url=index_view_url))
        index_url_keyboard = InlineKeyboardMarkup([buttons])
        return (index_url_keyboard, mime_type) if mime_type is not None else (index_url_keyboard, None)


    def upload_directory(self, directory_path, directory_name):
        total_files = 0
        for root, _, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_relative_path = os.path.relpath(file_path, directory_path)
                onedrive_path = f"/{directory_name}/{file_relative_path}"
                try:
                    index_url_keyboard, _ = self.upload_file(file_path, onedrive_path)
                    total_files += 1
                except AttributeError:
                    pass
                except Exception as e:
                    log.error(f"Error uploading file {file_path}: {str(e)}")
        if total_files > 0:
            index_url = f"{os.environ.get('INDEX_DOMAIN')}/{quote(directory_name)}"
            buttons = InlineKeyboardButton("Download", url=index_url)
            index_url_keyboard = InlineKeyboardMarkup([[buttons]])
            return index_url_keyboard, total_files


    def upload(self, file_name: str):
        self.__listener.onUploadStarted()
        file_dir = f"{DOWNLOAD_DIR}{self.__listener.message.id}"
        file_path = f"{file_dir}/{file_name}"
        log.info(f"Uploading File: {file_path}")
        self.start_time = time.time()
        self.updater = setInterval(self.update_interval, self._on_upload_progress)
        
        if os.path.isdir(file_path):
            try:
                directory_name = file_name
                index_url_keyboard, total_files = self.upload_directory(file_path, directory_name)
                if index_url_keyboard is None:
                    raise Exception('Upload has been manually cancelled')
                log.info(f"Uploaded Directory To OneDrive: {file_path}")
            except Exception as e:
                log.error(e)
                self.__listener.onUploadError(str(e))
                return
            finally:
                self.updater.cancel()
            self.__listener.onUploadComplete(index_url_keyboard, None, total_files)
        elif os.path.isfile(file_path):
            try:
                index_url_keyboard, mime_type = self.upload_file(file_path, file_name)
                if index_url_keyboard is None:
                    raise Exception('Upload has been manually cancelled')
                log.info(f"Uploaded To OneDrive: {file_path}")
            except Exception as e:
                log.error(e)
                self.__listener.onUploadError(str(e))
                return
            finally:
                self.updater.cancel()
            self.__listener.onUploadComplete(index_url_keyboard, mime_type)
        
        log.info("Deleting downloaded file/folder..")
    
    
    def create_directory(self, directory_name):
        request_url = f"{DRIVE_URI}/root/children"
        body = {"name": directory_name, "folder": {}}
        response = requests.post(request_url, headers=HEADERS, json=body).json()
        folder_id = response["id"]
        return folder_id