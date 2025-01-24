import os
import subprocess
import sys
from time import localtime, strftime, gmtime
import yt_dlp
from internetarchive import get_item, upload


def get_twitch_info(link: str, cookies: str) -> dict:
    ydl = yt_dlp.YoutubeDL({"extract_flat": "in_playlist", "quiet": True})
    if cookies is not None:
        ydl.params["cookiefile"] = cookies
    result = ydl.extract_info(link, download=False)
    return result

def get_vods(username: str, cookies: str) -> list:
    link = f"https://www.twitch.tv/{username}/videos"
    result = get_twitch_info(link, cookies)
    all_videos = []
    for entry in result["entries"]:
        all_videos.append(entry)
    return all_videos

def check_identifier_exists(identifier):
    try:
        item = get_item(identifier)
        return item.exists
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    current_dir = os.getcwd()
    streamers = sys.argv[1].split(",")
    cookies = None
    twitch_downloader_cli = None

    files = os.listdir(current_dir)
    if not any("TwitchDownloaderCLI" in file for file in files):
        print("TwitchDownloaderCLI not found")
        sys.exit(1)
    
    for file in files:
        if "TwitchDownloaderCLI" in file:
            twitch_downloader_cli = os.path.abspath(os.path.join(current_dir, file))
            break
    if not "ffmpeg" in os.environ:
        subprocess.run([twitch_downloader_cli, "ffmpeg", "-d"])

    if any("cookies" in file for file in files):
        for file in files:
            if "cookies" in file:
                cookies = file
                break

    temp_dir = os.path.join(current_dir, "data")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    for streamer in streamers:
        print("Getting vods of " + streamer)
        vods = get_vods(streamer, cookies)
        for vod in vods:
            vod_id = vod["id"][1:]
            print(f"Checking if vods exists : {vod_id}")
            identifier = f"TwitchVod-{vod_id}"
            if check_identifier_exists(identifier):
                print("Skipping vod since it already exists in internet archive")
                continue

            print("\t Getting vod info...")
            vod_info = get_twitch_info(vod["url"], cookies)
            if vod is None:
                print("Failed to get vod info")
                continue

            if vod_info["is_live"] == True:
                print("Skipping vod since it is live")
                continue

            subprocess.run(
                [twitch_downloader_cli, "cache", "--force-clear"]
            )
            files = os.listdir(temp_dir)
            for file in files:
                os.remove(os.path.join(temp_dir, file))

            print("Downloading Chat...")
            chat_file = os.path.join(temp_dir, f"{vod_id}.json")
            subprocess.run(
                [
                    f"{twitch_downloader_cli}",
                    "chatdownload",
                    "--id",
                    vod_id,
                    "--embed-images",
                    "--bttv=true",
                    "--ffz=True",
                    "--stv=true",
                    "-o",
                    chat_file,
                    "--compression",
                    "Gzip",
                    "--banner",
                    "false",
                    "-t",
                    "2",
                ]
            )
            chat_file = chat_file + ".gz"

            print("Downloading Vod...")
            livestream_file = os.path.join(temp_dir, f"{vod_id}.mp4")
            yt_opts = {
                "format": "best",
                "outtmpl": livestream_file,
                "tmpdir": temp_dir,
                "noplaylist": True,
                "retries": 10,
            }
            if cookies is not None:
                yt_opts["cookiefile"] = cookies

            try:
                with yt_dlp.YoutubeDL(yt_opts) as ydl:
                    ydl.download([vod_info["url"]])
            except Exception as e:
                files = os.listdir(temp_dir)
                for file in files:
                    os.remove(file)
                print(
                    f"Failed to download vod {vod['id']}. URL: https://www.twitch.tv/videos/{vod['id']}"
                )
                continue

            md = {
                "title": vod_info["fulltitle"],
                "mediatype": "movies",
                "creator": vod_info["uploader_id"],
                "description": "\n".join(
                    [
                        f"{strftime('%H:%M:%S', gmtime(chapter['start_time']))} - {chapter['title']}"
                        for chapter in vod_info["chapters"]
                    ]
                ),
                "date": strftime("%Y-%m-%d", localtime(vod_info["epoch"])),
                "subject": ["Twitch", "Twitch Vod", "Twitch Chat"],
                "language": "eng",
                "game": list(set(chapter["title"] for chapter in vod_info["chapters"])),
            }
            files = [livestream_file, chat_file]
            print("Uploading...")
            r = upload(identifier, files=files, metadata=md, request_kwargs={"timeout": 600})
            if r[0].status_code == 200:
                print(
                    f"Successfully uploaded {vod['id']}. URL: https://www.twitch.tv/videos/{vod['id']}. Internet Archive URL: https://archive.org/details/{identifier}"
                )
            else:
                print(
                    f"Failed to upload {vod['id']}. URL: https://www.twitch.tv/videos/{vod['id']}"
                )
            for file in files:
                os.remove(file)


if __name__ == "__main__":
    main()
