from __future__ import unicode_literals
import yt_dlp

import os.path
import re
import threading
import discord
from discord import FFmpegPCMAudio
from discord.ext import commands, tasks
import logging
import urllib.request

sam_logger = logging.getLogger("SAM-Bot" + "." + __name__)


class DownloadUrl(threading.Thread):
    def __init__(self, url, yt_id):
        threading.Thread.__init__(self, daemon=True, target=lambda: self.download(url, yt_id))
        self._stop_event = threading.Event()
        self.downloading = False

    def download(self, url, yt_id):
        try:
            sam_logger.debug("Started Thread")
            self.downloading = True
            # Download the file from `url` and save it locally under `file_name`:
            os.makedirs('cache', exist_ok=True)
            with urllib.request.urlopen(url) as response, open("cache/{yt_id}.m4a".format(yt_id=yt_id), 'wb') as out_file:
                data = response.read()  # a `bytes` object
                out_file.write(data)
        except Exception as e:
            sam_logger.debug(e)
        finally:
            sam_logger.debug("Finished Download")
            self.downloading = False
            self.stop()

    def stop(self):
        if not self.is_stopped():
            self._stop_event.set()
            sam_logger.debug("Stopped thread")
            if self.downloading:
                raise Exception("Canceled Downloading")
        else:
            sam_logger.debug("Already stopped thread")

    def is_stopped(self):
        return self._stop_event.is_set()


class YoutubeAudio(yt_dlp.YoutubeDL):
    def __init__(self, url):
        yt_dlp.YoutubeDL.__init__(self, {'format': 'bestaudio/best', 'prefer_ffmpeg': True, 'quiet': True})
        # video data
        self.video_info = None
        self.yt_id = None
        self.youtube_url = url

        self.thumbnail = None
        self.title = None
        self.author = None
        self.duration = {}
        self.download_thread = None
        self.audio_url = None

    def get_youtube_id(self):
        # get yt id
        regex = re.compile(
            r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?(?P<id>[A-Za-z0-9\-=_]{11})')
        match = regex.match(self.youtube_url)
        if match:
            self.yt_id = match.group('id')
            sam_logger.error("Got youtube video id")
        if not match:
            sam_logger.error("Could not find youtube id")
            self.yt_id = None

    def get_video_info(self):
        self.get_youtube_id()
        self.video_info = self.extract_info("https://youtu.be/{yt_id}".format(yt_id=self.yt_id), download=False)
        self.title = self.video_info['title']
        self.author = self.video_info['uploader']
        self.audio_url = self.video_info['formats'][1]['url']

        thumbnails = self.video_info['thumbnails'].reverse()
        self.thumbnail = thumbnails[1]['url']

        self.duration['total_seconds'] = self.video_info['duration']
        self.duration['length'] = seconds_to_minutes_display(self.video_info['duration'])

    def get_audio_url_or_path(self):
        if os.path.isfile("cache/{yt_id}.m4a".format(yt_id=self.yt_id)):
            sam_logger.debug("No need to cache video")
            return "cache/{yt_id}.m4a".format(yt_id=self.yt_id), False
        else:
            sam_logger.debug("Caching video")
            return self.video_info['formats'][1]['url'], True

    def cache_audio(self):
        self.download_thread = DownloadUrl(self.audio_url, yt_id=self.yt_id)
        self.download_thread.start()

    def stop_downloading(self):
        self.download_thread.stop()

    def is_finished_downloading(self):
        self.download_thread.is_stopped()


def seconds_to_minutes_display(seconds):
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


class Music(commands.Cog, name="Music"):
    def __init__(self, bot):
        self.bot = bot
        self.playing_index = 0
        self.queue = []
        self.music_seconds = None
        self.current_seconds = None
        self.video_message = None

    @commands.command(name="join")
    async def join(self, ctx):
        voice = ctx.author.voice
        if voice:
            sam_logger.debug("Joining voice chat")
            self.video_message = await ctx.send("Joined voice chat")
            await voice.channel.connect()
            return discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        await self.video_message.edit("You need to be in a voice channel idot")
        sam_logger.debug("User is not in voice chat")

    @commands.command(name="leave", aliases=("dc", "disconnect"))
    async def leave(self, ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice.is_connected():
            await voice.disconnect()

    @commands.command(name="play", aliases=("p",))
    async def play(self, ctx, url):
        # get and send video audio

        await ctx.message.delete()

        self.queue.append(YoutubeAudio(url))

        await self.play_next(ctx)

    async def play_next(self, ctx):
        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if not self.queue or self.current_seconds:
            return

        if not voice_client:
            voice_client = await self.join(ctx)
        if voice_client:
            voice_client.stop()
            self.music_player_loop.stop()
            sam_logger.debug("Getting audio url")
            await self.video_message.edit(content="Loading Music")

            youtube_video = self.queue[self.playing_index]
            youtube_video.get_video_info()

            video_embed = discord.Embed(title=f"Playing {youtube_video.title}")
            video_embed.url = youtube_video.youtube_url
            video_embed.set_image(url=youtube_video.thumbnail + "?size=640x385")
            video_embed.set_footer(text="Requested by {user}".format(user=ctx.author.name))

            video_embed.add_field(name="Duration", value=youtube_video.duration['length'])

            await self.video_message.edit(content=None, embed=video_embed)

            url_or_path, needs_caching = youtube_video.get_audio_url_or_path()
            if needs_caching:
                youtube_video.cache_audio()
            currently_playing_ffmpeg = FFmpegPCMAudio(source=url_or_path)
            voice_client.play(currently_playing_ffmpeg)
            sam_logger.debug("Playing audio")

            self.current_seconds = 0
            self.music_seconds = youtube_video.duration['total_seconds']

            self.music_player_loop.start(ctx)

    @commands.command(name="skip", aliases=['s'])
    async def skip(self, ctx):
        self.queue[self.playing_index].stop_downloading()
        self.current_seconds = 0
        self.queue.pop(0)
        await self.play_next(ctx)

    @tasks.loop(seconds=1.0)
    async def music_player_loop(self, ctx):
        self.current_seconds += 1
        if self.current_seconds >= self.music_seconds:
            await self.skip(ctx)

    @music_player_loop.after_loop
    async def after_music_player_loop(self):
        await self.video_message.edit(embed=discord.Embed(title="Finished Playing song"))

    @commands.command(name="queue", aliases=["q"])
    async def queue(self, ctx):
        emb = discord.Embed(title="Queue")
        if self.queue:
            for item in self.queue:
                emb.add_field(name=f"{self.queue.index(item) + 1}. {item.title}", value=item.duration['length'], inline=False)
        else:
            emb.add_field(name="Nothing playing", value="Use ,play to play something.")
        await ctx.send(embed=emb)

    @commands.command(name="stop")
    async def stop(self, ctx):
        sam_logger.debug("Stopping Song")
        # self.queue[self.playing_index].stop_downloading()
        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        voice_client.stop()
        self.music_player_loop.stop()

    @commands.command(name="playing", aliases=['np'])
    async def playing(self, ctx):
        playing_progress = seconds_to_minutes_display(self.current_seconds)
        song_length = seconds_to_minutes_display(self.music_seconds)
        await ctx.send(
            f"Playing song: **{self.queue[self.playing_index].title}**\nProgress: {playing_progress} of {song_length}")


def setup(bot):
    bot.add_cog(Music(bot))


def teardown(bot):
    bot.remove_cog("Music")
