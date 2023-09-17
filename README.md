<img src='https://gcdnb.pbrd.co/images/5SOosCKUJuL0.png?o=1' alt='drive1bot'>

## Join Our Channel and Group for Support
[Drive1bot ( support group )](https://t.me/drive1botgroup) | [Drive1bot Channel](https://t.me/drive1botchannel)


# What is this repo about?

This is a telegram bot writen in python for mirroring files on the internet to our beloved OneDrive.

## Base Repo
I'm using this repo [python-aria-mirror-bot](https://github.com/lzzy12/python-aria-mirror-bot) as base

---
### Repo Features

- Mirroring direct download links to OneDrive
- Mega.nz Support
- Leeching Support
- Torrent Support
- Docker Support
- Index Support
- YouTube Support

---
### Bot Usage

- /mirror    # aria2c|mega|pyrogram will upload files/folders on OneDrive
- /leech     # aria2c|mega will leeched files on Telegram Dump's Channel
- /yt        # YouTube videos will upload files/folders on OneDrive
- /ytl       # YouTube videos will leeched files on Telegram Dump's Channel
- /status    # for checking message status
- /search query    # Search file/folder in Onedrive
- /list or /list ID    # List root folder or Specific folder by folder ID
- /delete ITEM_ID   # Delete file/folder by ID 

---
## How to run

#### Fill .env file

### Docker
```
docker build -t drive1bot .; docker run -it drive1bot
```

### VPS/Pc
```
curl -Ls https://github.com/Oxhellfire/pymegasdkrest/releases/download/v6.9/megasdkrest -o /usr/local/bin/megasdkrest
chmod +x /usr/local/bin/megasdkrest
pip3 install -r requirements.txt
python3 -m drive1bot
```

---
### How to get mongodb URI 
[mongodb](https://telegra.ph/How-to-get-mongodb-URI-08-28)

### How to get 5tb onedrive storage
[OneDrive 5tb](https://www.youtube.com/watch?v=gcOsnkf1hfc)

### How to get OneGraph Secret Creadentials
[Secret Credetials](https://telegra.ph/How-to-get-OneDrive-Secret-Credentials-08-28)

### how to generate OneDrive Index
[OneDrive Index](https://ovi.swo.moe/docs/getting-started)