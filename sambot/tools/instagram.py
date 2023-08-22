from sambot.tools import botlogger

import instaloader
import re
import urllib.request
from urllib.parse import urlparse
import os

loggr = botlogger.getSubLogger("instadl")


class InstaDL(instaloader.Instaloader):
    def __init__(self):
        instaloader.Instaloader.__init__(self)
        self.dl_dir = "cache/instadl"
        self.load_session_from_file(username="fishing_lover74", filename="session-fishing_lover74")

    def dl_post(self, url):
        """Download a post's images and or videos"""

        shortcode = re.sub(r'(?:https?:\/\/)?(?:www.)?instagram.com\/?([a-zA-Z0-9\.\_\-]+)?\/([p]+)?([reel]+)?([tv]+)?([stories]+)?\/([a-zA-Z0-9\-\_\.]+)\/?([0-9]+)?',
                           r'\6', url)

        loggr.debug(f"Getting post from {shortcode}")

        try:
            post = instaloader.Post.from_shortcode(self.context, shortcode)
        except instaloader.BadResponseException:
            loggr.error(f"Failed to get post from {shortcode}")
            return shortcode

        loggr.debug(f"Acquired post from {shortcode}")

        media = self.get_media(post)
        media.insert(0, shortcode)

        if not media[1:]:
            url = post.url
            if post.is_video: url = post.video_url
            media.append({"url": url, "mediaindex": 0})

        media_paths = self.dl_media(media)

        media_paths.insert(0, {"caption": post.caption, "shortcode": shortcode})

        return media_paths

    def get_extension(self, url):
        parsed_url = urlparse(url)
        path = parsed_url.path
        filename = os.path.basename(path)
        filename_without_extension, file_extension = os.path.splitext(filename)
        return file_extension

    def get_media(self, post: instaloader.Post):
        media = []
        if post.mediacount == 1: return media
        mediaindex = 0
        for i in post.get_sidecar_nodes():
            url = i.display_url
            if i.is_video: url = i.video_url
            media.append({"url": url, "mediaindex": mediaindex})
            mediaindex += 1
        return media

    def dl_media(self, media: list):
        shortcode = media[0]
        media_paths = []
        for i in media[1:]:
            extension = self.get_extension(i["url"])
            path = f"{self.dl_dir}/{shortcode}-{i['mediaindex']}{extension}"
            loggr.debug(f"Download {path}")
            media_paths.append(path)
            urllib.request.urlretrieve(i["url"], path)
        return media_paths


if "__main__" == __name__:
    insta = InstaDL()

    insta.dl_dir = "../cache/instadl"

    print(insta.dl_post(url="https://www.instagram.com/p/CvfVPj7oryQ/"))
