import os
import sys
import shutil
import mimetypes
from drive1bot import aria2, OneDriveLog, DOWNLOAD_DIR


log = OneDriveLog()

def clean_download(path: str):
    if os.path.exists(path):
        log.info(f"Cleaning download: {path}")
        shutil.rmtree(path)


def start_cleanup():
    try:
        shutil.rmtree(DOWNLOAD_DIR)
    except FileNotFoundError:
        pass


def clean_all():
    aria2.remove_all(True)
    try:
        shutil.rmtree(DOWNLOAD_DIR)
    except FileNotFoundError:
        pass


def exit_clean_up(signal, frame):
    try:
        log.info("Please wait, while we clean up the downloads and stop running downloads")
        clean_all()
        sys.exit(0)
    except KeyboardInterrupt:
        log.warning("Force Exiting before the cleanup finishes!")
        sys.exit(1)


def get_path_size(path):
    if os.path.isfile(path):
        return os.path.getsize(path)
    total_size = 0
    for root, dirs, files in os.walk(path):
        for f in files:
            abs_path = os.path.join(root, f)
            total_size += os.path.getsize(abs_path)
    return total_size


def get_mime_type(file_path):
    mime_type, _ = mimetypes.guess_type(file_path)
    mime_type = mime_type if mime_type else "text/plain"
    return mime_type