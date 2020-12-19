import os
import shutil
import sys
from pathlib import Path
from typing import List
import time

import telegram
import telegraph

from settings import TELEGRAPH_ACCESS_TOKEN, TELEGRAM_ACCESS_TOKEN, TELEGRAM_GROUP_ID

bot = telegram.Bot(token=TELEGRAM_ACCESS_TOKEN)
telegraph_client = telegraph.Telegraph(access_token=TELEGRAPH_ACCESS_TOKEN)
tg_sleep_sec = 25


def post_image_to_tg(image_url, caption=''):
    # telegram restricts max characters of `caption` to be 200
    bot.send_photo(chat_id=TELEGRAM_GROUP_ID, photo=image_url,
                   caption=caption[:200])
    time.sleep(tg_sleep_sec)


def post_video_to_tg(video_url, caption=''):
    # telegram restricts max characters of `caption` to be 200
    bot.send_video(chat_id=TELEGRAM_GROUP_ID, video=video_url,
                   caption=caption[:200])
    time.sleep(tg_sleep_sec)


def post_telegraph_url_to_tg(username: str, telegraph_url):
    text = F"\nTelegraph URL #{username} \n({username}): {telegraph_url}\n"  # noqa
    bot.send_message(
        chat_id=TELEGRAM_GROUP_ID, text=text, disable_web_page_preview=True,
        disable_notification=True)
    time.sleep(tg_sleep_sec)


# given a list of media urls, this method posts them to the TG group
def post_to_tg(username, album_name, media_urls: List[str]):
    caption = F"#{username} {username}: {album_name}"
    for _url in media_urls:
        if _url.endswith(('.png', '.gif', '.jpg', '.jpeg')):
            post_image_to_tg(image_url=_url, caption=caption)
        else:
            post_video_to_tg(video_url=_url, caption=caption)


# uploads all the contents of a album to telegraph and returns the post URL
def upload_to_telegraph(username, album_path: Path) -> (str, List[str]):
    # children will be the path to the files within this album directory
    # they could be jpeg, gif, png or mp4
    children = [p.absolute().as_posix() for p in album_path.iterdir() if p.is_file()]
    if not children:
        return None, None
    media_urls: List[str] = telegraph.upload.upload_file(children)
    content = get_html_content_for_telegraph(media_urls)
    post_title = F"{album_path.name} by {username}"
    response = telegraph_client.create_page(post_title, html_content=content)
    return response['url'], media_urls


def get_html_content_for_telegraph(media_urls: List[str]):
    if not media_urls:
        return
    content = ''
    for _url in media_urls:
        if _url.endswith('jpeg') or _url.endswith('jpg') or _url.endswith('png') or _url.endswith('gif'):  ## noqa
            content = content + F"<img src='{_url}'>" + ' <br />'
        elif _url.endswith('mp4'):
            content = content + F"<video src='{_url}' controls></video>" + ' <br />'  ## noqa
        else:
            content = content + F'<p>found new kind of content {_url}</p>' + ' <br />'  ## noqa
    return content


def clean_up(path: Path):
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def process_album(username: str, album: Path):
    album_name = album.name
    # we need to upload all the images, videos to telegraph
    post_url, media_urls = upload_to_telegraph(username, album_path=album)
    if not post_url:
        # there were no files in this directory to be uploaded, so just return
        return
    # once we have post_url, we can now post to TG
    # telegraph urls dont have host, so we add them manually here. They are usually like
    # `/file/someId`, so we just append `https://telegra.ph`
    post_to_tg(username=username, album_name=album_name,
               media_urls=[F"https://telegra.ph{u}" for u in media_urls])
    # once all images have been posted, we can post the telegraph url
    post_telegraph_url_to_tg(username=username, telegraph_url=post_url)


def process_user(path: Path):
    username = path.name
    for album in Path(path).iterdir():
        if album.is_dir():
            process_album(username, album)
            # the album has been processed. then it can be deleted
            clean_up(album)


def run(root: str):
    for child in Path(root).iterdir():
        if child.is_dir():
            process_user(child)
            # the user has been processed. then it can be deleted
            clean_up(child)


if __name__ == '__main__':
    run(sys.argv[1])
