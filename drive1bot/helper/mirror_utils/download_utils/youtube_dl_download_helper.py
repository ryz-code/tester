import re
import threading
from random import choice
from string import hexdigits
from yt_dlp import YoutubeDL, DownloadError
from drive1bot import download_dict_lock, download_dict, OneDriveLog
from drive1bot.helper.mirror_utils.download_utils.download_helper import DownloadHelper
from drive1bot.helper.mirror_utils.status_utils.youtube_dl_download_status import YoutubeDLDownloadStatus

log = OneDriveLog()


class MyLogger:
    def __init__(self, obj):
        self.obj = obj

    def debug(self, msg):
        # Hack to fix changing changing extension
        if match := re.search(r'.ffmpeg..Merging formats into..(.*?).$', msg):
            self.obj.name = match.group(1)

    @staticmethod
    def warning(msg):
        log.error(msg)

    @staticmethod
    def error(msg):
        log.error(msg)


class YoutubeDLHelper(DownloadHelper):
    def __init__(self, listener):
        super().__init__()
        self.__name = ""
        self.__listener = listener
        self.opts = {
            'progress_hooks': [self.__onDownloadProgress],
            'logger': MyLogger(self),
            'noprogress': True,
            'overwrites': True,
            'format': 'bestvideo+bestaudio/best',
        }
        self.__download_speed = 0
        self.download_speed_readable = ''
        self.downloaded_bytes = 0
        self.size = 0
        self.last_downloaded = 0
        self.is_cancelled = False
        self.__resource_lock = threading.RLock()
        self.__gid = ''.join(choice(hexdigits[:-6]) for _ in range(16))

    @property
    def name(self):
        with self.__resource_lock:
            return self.__name

    @property
    def download_speed(self):
        with self.__resource_lock:
            return self.__download_speed

    @property
    def gid(self):
        with self.__resource_lock:
            return self.__gid

    def __onDownloadProgress(self, d):
        if self.is_cancelled:
            raise ValueError("Cancelling Download..")
        elif d['status'] == "downloading":
            with self.__resource_lock:
                self.__download_speed = d['speed']
                self.download_speed_readable = d['_speed_str']
                self.downloaded_bytes = d['downloaded_bytes']
                try:
                    self.progress = (self.downloaded_bytes / self.size) * 100
                except ZeroDivisionError:
                    pass

    def __onDownloadStart(self):
        with download_dict_lock:
            download_dict[self.__listener.uid] = YoutubeDLDownloadStatus(self, self.__listener)

    def __onDownloadComplete(self):
        self.__listener.onDownloadComplete()

    def onDownloadError(self, error):
        self.__listener.onDownloadError(error)

    def extractMetaData(self, link):
        with YoutubeDL(self.opts) as ydl:
            try:
                result = ydl.extract_info(link, download=False)
                name = ydl.prepare_filename(result, outtmpl=f"%(title)s.%(ext)s")
            except DownloadError as e:
                self.onDownloadError(str(e))

        if result.get('filesize'):
            self.size = result.get('filesize')
        elif result.get('filesize_approx'):
            self.size = result.get('filesize_approx')
        self.__name = name

    def __download(self, link):
        try:
            with YoutubeDL(self.opts) as ydl:
                try:
                    ydl.download([link])
                except DownloadError as e:
                    self.onDownloadError(str(e))
                    return
            if self.is_cancelled:
                raise ValueError("Cancelling Download..")
            self.__onDownloadComplete()
        except ValueError:
            log.info("Download Cancelled by User!")
            self.onDownloadError("Download Cancelled by User!")
        
    def add_download(self, link, path):
        self.opts['outtmpl'] = f"{path}/%(title)s.%(ext)s"
        self.opts['ignoreerrors'] = True
        self.__onDownloadStart()
        self.extractMetaData(link)
        log.info(f"Downloading with YT-DL: {link}")
        self.__download(link)

    def cancel_download(self):
        self.is_cancelled = True