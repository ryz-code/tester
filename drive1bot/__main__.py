import shutil
import asyncio
# import importlib
import os
import subprocess
from uvloop import install
from dotenv import load_dotenv
from pyrogram import idle, filters
from pyrogram.enums import ParseMode
from contextlib import closing, suppress
from drive1bot import app, OneDriveLog, BOT_NAME, DOWNLOAD_DIR, USERBOT_NAME
import glob

log = OneDriveLog()
loop = asyncio.get_event_loop()


async def start_bot():
    
    module_directory = 'drive1bot/modules'
    
    module_files = [
        file for file in glob.glob(os.path.join(module_directory, '*.py'))
        if not os.path.basename(file).startswith('__')
    ]

    for module_file in module_files:
        module_name = os.path.splitext(os.path.basename(module_file))[0]
        __import__(f'drive1bot.modules.{module_name}')
    
    
    log.info(f"{BOT_NAME} as Bot Started")
    log.info(f"{USERBOT_NAME} as Userbot Started")
    
    await idle()

    log.info("Stopping app")
    await app.stop()
    
    subprocess.run('pkill -9 -f aria2c', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run('pkill -9 -f megasdkrest', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run('pkill -9 -f drive1bot', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        shutil.rmtree(DOWNLOAD_DIR)
    except FileNotFoundError:
        pass
    
    # command = "docker ps --filter ancestor=drive1bot --format {{.ID}}"
    # container_id = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True).stdout.strip()
    # subprocess.run(f"docker exec -it {container_id} kill -9 {getpid()}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    log.info("Terminating all asyncio tasks")
    for task in asyncio.all_tasks():
        task.cancel()
    log.info("Bot Stopped!")
    


@app.on_message(filters.command("start"))
async def start(_, message):
    await message.reply_text("Hello from Bot")
    

if __name__ == "__main__":
    install()
    with closing(loop):
        with suppress(asyncio.exceptions.CancelledError):
            loop.run_until_complete(start_bot())