import shutil
import asyncio
import subprocess
from uvloop import install
from pyrogram import idle, filters
from pyrogram.enums import ParseMode
from contextlib import closing, suppress
from drive1bot import app, OneDriveLog, BOT_NAME, DOWNLOAD_DIR


log = OneDriveLog()
loop = asyncio.get_event_loop()


async def start_bot():
    log.info(f"{BOT_NAME}! Started")

    await idle()

    log.info("Stopping app")
    await app.stop()
    
    subprocess.run('pkill -9 -f aria2', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        shutil.rmtree(DOWNLOAD_DIR)
    except FileNotFoundError:
        pass
    subprocess.run("ps aux | grep [d]rive1bot | awk '{print $2}' | xargs -I drive1bot kill -9 drive1bot", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    log.info("Terminating all asyncio tasks")
    for task in asyncio.all_tasks():
        task.cancel()
    log.info("Bot Stopped!")
    

@app.on_message(filters.command("start"))
async def start(_, message):
    await message.reply_text("Hello from Bot")
    
    
@app.on_message(filters.command("id"))
async def getid(_, message):
    chat = message.chat
    text = f"**[Chat ID:](https://t.me/{chat.username})** `{chat.id}`\n\n"

    await message.reply_text(
        text=text,
        disable_web_page_preview=True,
        parse_mode=ParseMode.MARKDOWN,
    )


if __name__ == "__main__":
    install()
    with closing(loop):
        with suppress(asyncio.exceptions.CancelledError):
            loop.run_until_complete(start_bot())