import os
import subprocess
import sys
from time import strftime, gmtime, strptime
import yt_dlp
from internetarchive import get_item, upload
import argparse



def get_twitch_info(link: str, cookies: str) -> dict:
    ydl = yt_dlp.YoutubeDL({
        "extract_flat": "in_playlist", 
        "quiet": True, 
        "nocheckcertificate": True,
        "ignoreerrors": True,
        "no_warnings": True,
        "socket_timeout": 30,
        "retries": 10
    })
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
    
def get_metadata(identifier) -> dict:
    try:
        item = get_item(identifier)
        return item.metadata
    except Exception as e:
        print(f"Error: {e}")
        return None

def clear_dir(temp_dir: str) -> None:
    files = os.listdir(temp_dir)
    for file in files:
        os.remove(os.path.join(temp_dir, file))

def main(streamers: str, verify_metadata: bool) -> None:
    current_dir = os.getcwd()
    streamers = streamers.split(",")
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
            print("\t Getting vod info...")
            vod_info = get_twitch_info(vod["url"], cookies)
            if vod_info is None:
                print("Failed to get vod info")
                continue

            vod_id = vod["id"][1:]
            print(f"Checking if vods exists : {vod_id}")
            identifier = f"TwitchVod-{vod_id}"
            if check_identifier_exists(identifier):
                print("Skipping vod since it already exists in internet archive")
                if verify_metadata:
                    print("Verifying metadata...")
                    metadata = get_metadata(identifier)
                    metadata_should_be = {
                        "title": vod_info["fulltitle"],
                        "creator": vod_info["uploader_id"],
                        "date": strftime("%Y-%m-%d", strptime(vod_info["upload_date"], "%Y%m%d")),
                        "description": "\n".join([f"{strftime('%H:%M:%S', gmtime(chapter['start_time']))} - {chapter['title']}" for chapter in vod_info["chapters"]]),
                        "game": list(set(chapter["title"] for chapter in vod_info["chapters"])),
                        "language": "eng",
                        "mediatype": "movies",
                        "subject": ["Twitch", "Twitch Vod", "Twitch Chat"]
                    }
                    if any(metadata.get(key) != value for key, value in metadata_should_be.items()):
                        print("Metadata mismatch, updating...")
                        r = get_item(identifier).modify_metadata(metadata=metadata_should_be)
                        if r.status_code != 200:
                            print(f"Failed to update metadata: {r.status_code}")
                    print("Metadata verified")
                continue            

            if vod_info["is_live"] == True:
                print("Skipping vod since it is live")
                continue

            subprocess.run([twitch_downloader_cli, "cache", "--force-clear"])
            files = os.listdir(temp_dir)
            for file in files:
                os.remove(os.path.join(temp_dir, file))

            print("Downloading Chat...")
            chat_file = os.path.join(temp_dir, f"{vod_id}.json")
            compressed_chat_file = chat_file + ".gz"
            retries = 0
            while not os.path.exists(compressed_chat_file) and retries < 5:
                subprocess.run([
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
                        "1",
                ])
                retries += 1
            
            if not os.path.exists(compressed_chat_file) and retries >= 5:
                print(f"Failed to download chat for vod {vod_id}")
                continue

            print("Downloading Vod...")
            livestream_file = os.path.join(temp_dir, f"{vod_id}.mp4")
            video_retry = 0
            while not os.path.exists(livestream_file) and video_retry < 5:
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
                    break
                except Exception as e:
                    print(
                        f"Failed to download vod {vod['id']}. URL: https://www.twitch.tv/videos/{vod['id']}"
                    )
                    pass
            
            if not os.path.exists(livestream_file) and video_retry >= 5:
                print(f"Failed to download vod {vod_id}")
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
                "date": strftime("%Y-%m-%d", strptime(vod_info["upload_date"], "%Y%m%d")),
                "subject": ["Twitch", "Twitch Vod", "Twitch Chat"],
                "language": "eng",
                "game": list(set(chapter["title"] for chapter in vod_info["chapters"])),
            }
            files = [livestream_file, compressed_chat_file]
            print("Uploading...")
            r = upload(
                identifier, files=[livestream_file, compressed_chat_file], metadata=md, request_kwargs={"timeout": 600, "timeout": 9001},
                retries=9001,
            )
            if r[0].status_code == 200:
                print(
                    f"Successfully uploaded {vod_id}. URL: https://www.twitch.tv/videos/{vod_id}. Internet Archive URL: https://archive.org/details/{identifier}"
                )
            else:
                print(
                    f"Failed to upload {vod_id}. URL: https://www.twitch.tv/videos/{vod_id}"
                )
            for file in files:
                os.remove(file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Twitch Archiver')
    parser.add_argument('input_string', help='Streamers to archive, example: steamer1 or streamer1,streamer2', type=str)
    parser.add_argument('-vm', '--verify-metadata', action='store_true', help='Verifies metadata of the given identifier', required=False)
    args = parser.parse_args()
    main(args.input_string, args.verify_metadata)