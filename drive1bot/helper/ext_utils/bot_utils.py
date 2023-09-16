import re
import time
import threading
from drive1bot import download_dict, download_dict_lock

MAGNET_REGEX = r"magnet:\?xt=urn:btih:[a-zA-Z0-9]*"

URL_REGEX = r"(?i)\b(?:https?|ftp)://[-\w.]+(:\d+)?(/([~\w/_.]*)?)?"

class MirrorStatus:
    STATUS_UPLOADING = "Uploading"
    STATUS_DOWNLOADING = "Downloading"
    STATUS_WAITING = "Queued"
    STATUS_FAILED = "Failed. Cleaning download"
    STATUS_CANCELLED = "Cancelled"


PROGRESS_MAX_SIZE = 100 // 8
PROGRESS_INCOMPLETE = ['▤', '▥', '▦', '▧', '▨', '▩', '■']

SIZE_UNITS = ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB']


class setInterval:
    def __init__(self, interval, action):
        self.interval = interval
        self.action = action
        self.stopEvent = threading.Event()
        thread = threading.Thread(target=self.__setInterval)
        thread.start()

    def __setInterval(self):
        nextTime = time.time() + self.interval
        while not self.stopEvent.wait(nextTime - time.time()):
            nextTime += self.interval
            self.action()

    def cancel(self):
        self.stopEvent.set()


def get_readable_file_size(size_in_bytes) -> str:
    if size_in_bytes is None:
        return '0B'
    index = 0
    while size_in_bytes >= 1024:
        size_in_bytes /= 1024
        index += 1
    try:
        return f'{round(size_in_bytes, 2)} {SIZE_UNITS[index]}'
    except IndexError:
        return 'File too large'


def getDownloadByGid(gid):
    with download_dict_lock:
        for dl in download_dict.values():
            status = dl.status()
            if status != MirrorStatus.STATUS_UPLOADING:
                if dl.gid() == gid:
                    return dl
    return None


def get_progress_bar_string(status):
    completed = status.processed_bytes() / 8
    total = status.size_raw() / 8
    if total == 0:
        p = 0
    else:
        p = round(completed * 100 / total)
    p = min(max(p, 0), 100)
    cFull = p // 8
    cPart = p % 8 - 1
    blocks = ['▤', '▥', '▦', '▧', '▨', '▩', '■'][int(cPart / 8 * 7)] if cPart >= 0 else ''
    p_str = '■' * cFull + (blocks if cFull < 12 else '')
    p_str += '□' * (12 - cFull - 1)
    return f"[{p_str}]"


def get_download_str():
    result = ""
    with download_dict_lock:
        for status in list(download_dict.values()):
            result += (status.progress() + status.speed() + status.status())
        return result


def get_readable_message():
    with download_dict_lock:
        progress_message = ""
        for download in list(download_dict.values()):
            chat_id = str(download.message.chat.id).removeprefix("-100")
            message_link = f"https://t.me/{download.message.chat.username or f'c/{chat_id}'}/{download.message.id}"
            user = download.message.from_user
            new_line = "\n" if download.status() == MirrorStatus.STATUS_UPLOADING else ""
            username = f"@{user.username}" if user.username else f"[{user.first_name}]({f'tg://user?id={user.id}'})"
            progress_message += (
                f"**[{download.status()}]({message_link})**: `{download.name()}`\n"
                f"{get_progress_bar_string(download)} {download.progress()}\n"
                f"**Processed**: {get_readable_file_size(download.processed_bytes())} of {download.size()}\n"
                f"**Speed**: {download.speed()} | **ETA**: {download.eta()}\n"
                f"**User**: {username} | **ID**: `{user.id}`\n{new_line}"
            )
            if download.status() == MirrorStatus.STATUS_DOWNLOADING:
                if hasattr(download, 'is_torrent'):
                    progress_message += (
                        f"**Seeders**: {download.aria_download().num_seeders} | **Leechers**: {download.aria_download().connections}\n"
                    )
                progress_message += (
                    f"/cancel_{download.gid()}\n\n"
                )
        return progress_message
    

def get_readable_time(seconds: int) -> str:
    result = ''
    (days, remainder) = divmod(seconds, 86400)
    days = int(days)
    if days != 0:
        result += f'{days}d'
    (hours, remainder) = divmod(remainder, 3600)
    hours = int(hours)
    if hours != 0:
        result += f'{hours}h'
    (minutes, seconds) = divmod(remainder, 60)
    minutes = int(minutes)
    if minutes != 0:
        result += f'{minutes}m'
    seconds = int(seconds)
    result += f'{seconds}s'
    return result


def is_mega_link(url: str):
    return "mega.nz" in url


def is_url(url: str):
    url = re.findall(URL_REGEX,url)
    if url:
        return True
    return False    


def is_magnet(url: str):
    magnet = re.findall(MAGNET_REGEX,url)
    if magnet:
        return True
    return False


def new_thread(fn):
    """To use as decorator to make a function call threaded.
    Needs import
    from threading import Thread"""

    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread

    return wrapper