import os
import time
import requests
from urllib.parse import quote
from dotenv import load_dotenv
from drive1bot import OneDriveLog, DOWNLOAD_DIR
from drive1bot.helper.ext_utils.bot_utils import *
from drive1bot.msgraphauth import MicrosoftGraphAuth



load_dotenv()
log = OneDriveLog()

auth_manager = MicrosoftGraphAuth()
HEADERS = auth_manager.headers()


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
        
        index_url = f"{os.environ.get('INDEX_DOMAIN')}/api/raw/?path=/{quote(file_name)}"
        return index_url
        

    def upload(self, file_name: str):
        self.__listener.onUploadStarted()
        file_dir = f"{DOWNLOAD_DIR}{self.__listener.message.id}"
        file_path = f"{file_dir}/{file_name}"
        log.info("Uploading File: " + file_path)
        self.start_time = time.time()
        self.updater = setInterval(self.update_interval, self._on_upload_progress)
        if os.path.isfile(file_path):
            try:
                link = self.upload_file(file_path, file_name)
                if link is None:
                    raise Exception('Upload has been manually cancelled')
                log.info("Uploaded To OneDrive: " + file_path)
            except Exception as e:
                log.error(e)
                self.__listener.onUploadError(str(e))
                return
            finally:
                self.updater.cancel()
        log.info(download_dict)
        self.__listener.onUploadComplete(link)
        log.info("Deleting downloaded file/folder..")
        return link