# Twitch Vod Archiver
A simple program to archive twitch vods to archive.org with chat for preservation.

# Requirements
- [TwitchDownloader by lay295](https://github.com/lay295/TwitchDownloader)

# Install
```
git clone https://github.com/AksharDP/TwitchVodArchiver.git
cd TwitchVodArchiver
pip install -r requirements.txt
ia configure
```
#### TwitchDownloader
Download [TwitchDownloader](https://github.com/lay295/TwitchDownloader) and place in same directory as main.py

#### Start
```
python main.py "username"
```
#### Seperate usernames with commas to archive multiple streamers
```
python main.py "username,username2,username3"
```

# Third Party Credits

Chat is downloaded with [TwitchDownloader](https://github.com/lay295/TwitchDownloader/tree/master)

Twitch Vod is download with [yt-dlp](https://github.com/yt-dlp/yt-dlp)

# License

[MIT](./LICENSE.txt)

TwitchVodArchiver is in no way associated with Twitch Interactive, Inc. or its affiliates.