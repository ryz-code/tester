from drive1bot import app
from pyrogram import filters
from pyrogram.enums import ParseMode
from drive1bot.helper.telegram_helper.message_utils import *
from drive1bot.helper.mirror_utils.upload_utils.onedrivetool import OneDriveHelper


@app.on_message(filters.command("search"))
def searching(_, message):
    split_text = message.text.split(" ")
    query = ' '.join(split_text[1:]) if len(split_text) > 1 else None
    if query is None:
        return message.reply("`/search <query>`", parse_mode=ParseMode.MARKDOWN)
    msg = message.reply(f"Searching for {query}...")
    result = OneDriveHelper().searching(query)
    msg.edit(result)
    
    
@app.on_message(filters.command("list"))
def listing(_, message):
    split_text = message.text.split(" ")
    _id = split_text[1] if len(split_text) > 1 else None
    msg = message.reply(f"Listing all items from this {_id} ID..." if _id else f"Listing all items from root folder")
    result = OneDriveHelper().list_directory(_id)
    msg.edit(result)
    

@app.on_message(filters.command("delete"))
def deleting(_, message):
    split_text = message.text.split(" ")
    _id = split_text[1] if len(split_text) > 1 else None
    if _id is None:
        return message.reply("Item ID Required\nGet from:\n`/search <query>`\n`/list`", parse_mode=ParseMode.MARKDOWN)
    msg = message.reply(f"Deleting Item {_id}.")
    result = OneDriveHelper().delete_items(_id)
    msg.edit(result)