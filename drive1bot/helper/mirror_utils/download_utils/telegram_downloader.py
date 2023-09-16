import time
import threading
from random import choice
from string import hexdigits
from drive1bot import OneDriveLog, download_dict, download_dict_lock, app
from drive1bot.helper.mirror_utils.download_utils.download_helper import DownloadHelper
from drive1bot.helper.mirror_utils.status_utils.telegram_download_status import TelegramDownloadStatus

global_lock = threading.Lock()
GLOBAL_GID = set()
log = OneDriveLog()


class TelegramDownloadHelper(DownloadHelper):
    def __init__(self, listener):
        super().__init__()
        self.__listener = listener
        self.__resource_lock = threading.RLock()
        self.__start_time = time.time()
        self.__is_cancelled = False
        self.__gid = ''.join(choice(hexdigits[:-6]) for _ in range(16))
        

    @property
    def gid(self):
        with self.__resource_lock:
            return self.__gid

    @property
    def download_speed(self):
        with self.__resource_lock:
            return self.downloaded_bytes / (time.time() - self.__start_time)

    def __onDownloadStart(self, name, size):
        with download_dict_lock:
            download_dict[self.__listener.uid] = TelegramDownloadStatus(self, self.__listener)
        with global_lock:
            GLOBAL_GID.add(self.__gid)
        with self.__resource_lock:
            self.name = name
            self.size = size
        self.__listener.onDownloadStarted()
        

    def __onDownloadProgress(self, current, total):
        if self.__is_cancelled:
            self.__onDownloadError('Cancelled by user!')
            app.stop_transmission()
            return
        with self.__resource_lock:
            self.downloaded_bytes = current
            try:
                self.progress = current / self.size * 100
            except ZeroDivisionError:
                self.progress = 0

    def __onDownloadError(self, error):
        with global_lock:
            try:
                GLOBAL_GID.remove(self.gid)
            except KeyError:
                pass
        self.__listener.onDownloadError(error)

    def __onDownloadComplete(self):
        with global_lock:
            GLOBAL_GID.remove(self.gid)
        self.__listener.onDownloadComplete()

    def __download(self, message, path):
        try:
            download = app.download_media(message, progress=self.__onDownloadProgress, file_name=path)
            if download is not None:
                self.__onDownloadComplete()
            else:
                if not self.__is_cancelled:
                    self.__onDownloadError('Internal error occurred')
        except:
            pass

    def add_download(self, message, path):
        _message = app.get_messages(message.chat.id, message.id)
        media = None
        media_array = [_message.document, _message.video, _message.audio]
        for i in media_array:
            if i is not None:
                media = i
                break
        if media is not None:
            with global_lock:
                # For avoiding locking the thread lock for long time unnecessarily
                download = media.file_id not in GLOBAL_GID

            if download:
                self.__onDownloadStart(media.file_name, media.file_size)
                log.info(f'Downloading telegram file with id: {media.file_id}')
                threading.Thread(target=self.__download, args=(_message, path)).start()
            else:
                self.__onDownloadError('File already being downloaded!')
        else:
            self.__onDownloadError('No document in the replied message')

    def cancel_download(self):
        log.info(f'Cancelling download on user request: {self.gid}')
        self.__is_cancelled = True