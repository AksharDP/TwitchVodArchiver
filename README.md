# Twitch Vod Archiver

A simple program to archive Twitch VODs with chat to archive.org for preservation.

## 🚀 Features

- Downloads Twitch VODs with chat history
- Preserves BTTV, FFZ, and 7TV emotes in chat file
- Uploads to Internet Archive automatically
- Supports archiving multiple streamers
- Includes chapter information in metadata

## 📋 Requirements

- Python 3.6+
- [TwitchDownloader](https://github.com/lay295/TwitchDownloader)
- Internet Archive account

## 🔧 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/AksharDP/TwitchVodArchiver.git
   cd TwitchVodArchiver
2. Install dependencies:
    ```
    pip install -r requirements.txt
    ```
3. Configure Internet Archive credentials:
    ```
    ia configure
    ```
4. Download [TwitchDownloader](https://github.com/lay295/TwitchDownloader) (CLI version) and place the executable in the same directory as main.py.

## 🚀 Usage
***Archive a single streamer:***
```
python main.py "username"
```

***Archive multiple streamers:***
```
python main.py "username1,username2,username3"
```

## 🛠️ Dependencies
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - For VOD downloads
- [TwitchDownloader](https://github.com/lay295/TwitchDownloader) - For chat downloads
- [internetarchive](https://pypi.org/project/internetarchive/) - For uploading to archive.org

## 📝 License
This project is licensed under the MIT License.

TwitchVodArchiver is not affiliated with Twitch Interactive, Inc. or its affiliates.