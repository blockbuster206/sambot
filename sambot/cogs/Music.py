from __future__ import unicode_literals

import asyncio

import yt_dlp

import os.path
import re
import threading
import discord
from discord import FFmpegPCMAudio
from discord.ext import commands, tasks
import logging
import urllib.request
import validators

sam_logger = logging.getLogger("SAM-Bot" + "." + __name__)


def seconds_to_minutes_display(seconds):
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


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
            with urllib.request.urlopen(url) as response, open("cache/{yt_id}.m4a".format(yt_id=yt_id),
                                                               'wb') as out_file:
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


class Song(yt_dlp.YoutubeDL):
    def __init__(self, url_or_search_term):
        yt_dlp.YoutubeDL.__init__(self, {'format': 'bestaudio/best', 'prefer_ffmpeg': True, 'quiet': True})
        # video data
        self.video_info = None
        self.yt_id = None
        self.youtube_url_or_search_term = url_or_search_term

        self.thumbnail = None
        self.title = None
        self.author = None
        self.duration = {}
        self.download_thread = None
        self.audio_url = None

    def get_video_id(self, url):
        regex = re.compile(
            r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?(?P<id>[A-Za-z0-9\-=_]{11})')
        match = regex.match(url)
        if match:
            self.yt_id = match.group('id')

    def get_video_info(self):
        sam_logger.debug("Getting youtube video metadata")
        if validators.url(self.youtube_url_or_search_term[0]):
            self.get_video_id(self.youtube_url_or_search_term[0])
            self.video_info = self.extract_info("https://youtu.be/{0}".format(self.yt_id), download=False)
        else:
            sam_logger.debug(f"Searching for {' '.join(self.youtube_url_or_search_term)}")
            self.video_info = \
            self.extract_info(f"ytsearch1:{' '.join(self.youtube_url_or_search_term)}", download=False)['entries'][0]
            if self.video_info:
                sam_logger.debug(f"Found {' '.join(self.youtube_url_or_search_term)}")
                self.get_video_id(self.video_info['webpage_url'])
            else:
                sam_logger.debug(f"Couldn't find {' '.join(self.youtube_url_or_search_term)}")
                self.yt_id = None
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
        return self.download_thread.is_stopped()


class Music(commands.Cog, name="Music"):
    def __init__(self, bot):
        self.bot = bot
        self.playing_index = 0
        self.servers = {}
        self.music_seconds = None
        self.current_seconds = None

    @commands.command(name="connect", aliases=['join', 'john'])
    async def connect(self, ctx):
        voice = ctx.author.voice
        if voice:
            if discord.utils.get(self.bot.voice_clients, guild=ctx.guild):
                await ctx.send("Already connected to voice chat!")
            else:
                await ctx.send("Joined voice chat!")
                await voice.channel.connect()
        else:
            await ctx.send("You need to be in a voice channel idot")

    @commands.command(name="disconnect", aliases=("dc", "leave"))
    async def leave(self, ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice.is_connected():
            await voice.disconnect()

    @commands.command(name="play", aliases=("p",))
    async def play(self, ctx, *url_or_search_term):
        # init list if it doesnt exist
        voice = ctx.author.voice
        if voice:
            if not discord.utils.get(self.bot.voice_clients, guild=ctx.guild):
                await ctx.send("Joined voice chat!")
                await voice.channel.connect()
        else:
            await ctx.send("You need to be in a voice channel idot")
            return

        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if not ctx.guild.id in self.servers:
            self.servers[ctx.guild.id] = []

        video = Song(url_or_search_term)
        await ctx.send(f"Searching for `{' '.join(url_or_search_term)}`")
        video.get_video_info()
        await ctx.send(f"Found `{' '.join(url_or_search_term)}`")
        if not voice_client.is_playing():
            await ctx.send(f"Currently playing **{video.title}**")
            voice_client.play(source=FFmpegPCMAudio(video.audio_url), after=lambda e: self.play_next(ctx))
        else:
            await ctx.send(f"Added **{video.title}** to the queue")
            self.servers[ctx.guild.id].append(video)

    def play_next(self, ctx):
        if len(self.servers[ctx.guild.id]) >= 1:
            voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            voice_client.play(source=FFmpegPCMAudio(self.servers[ctx.guild.id][0].audio_url), after=lambda e: self.play_next(ctx))
            asyncio.run_coroutine_threadsafe(ctx.send(f"Currently playing **{self.servers[ctx.guild.id][0].title}**"), self.bot.loop)
            self.servers[ctx.guild.id].pop(0)

    @commands.command(name="skip", aliases=['s'])
    async def skip(self, ctx):
        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        voice_client.stop()

    @commands.command(name="queue", aliases=["q"])
    async def queue(self, ctx):
        if not ctx.guild.id in self.servers:
            self.servers[ctx.guild.id] = []

        emb = discord.Embed(title="Queue")
        if self.servers[ctx.guild.id]:
            for song in self.servers[ctx.guild.id]:
                emb.add_field(name=f"{self.servers[ctx.guild.id].index(song) + 1}. {song.title}",
                              value=song.duration['length'],
                              inline=False)
        else:
            emb.add_field(name="Nothing is queued", value="Use ,play to add something.")
        await ctx.send(embed=emb)

    @commands.command(name="stop")
    async def stop(self, ctx):
        # sam_logger.debug("Stopping Song")
        # voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        # voice_client.stop()
        pass

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
