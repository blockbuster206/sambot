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
import ctypes
import time

sam_logger = logging.getLogger("SAM-Bot" + "." + __name__)
thread_counts = 0


def ctype_async_raise(target_tid, exception):
    ret = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(target_tid), ctypes.py_object(exception))
    # ref: http://docs.python.org/c-api/init.html#PyThreadState_SetAsyncExc
    if ret == 0:
        raise ValueError("Invalid thread ID")
    elif ret > 1:
        # Huh? Why would we notify more than one threads?
        # Because we punch a hole into C level interpreter.
        # So it is better to clean up the mess.
        ctypes.pythonapi.PyThreadState_SetAsyncExc(target_tid, 0)
        raise SystemError("PyThreadState_SetAsyncExc failed")


def seconds_to_minutes_display(seconds):
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


class DownloadUrl(threading.Thread):
    def __init__(self, url, yt_id):
        threading.Thread.__init__(self, daemon=True, target=lambda: self.download(url, yt_id))
        self.yt_id = yt_id
        self._stop_event = threading.Event()
        self.downloading = False

    def download(self, url, yt_id):
        global thread_counts
        thread_counts += 1
        out_file = open(f"cache/{yt_id}.m4a", 'wb+')
        try:
            sam_logger.debug(f"Started download thread ({yt_id})")
            self.downloading = True
            os.makedirs('cache', exist_ok=True)
            with urllib.request.urlopen(url) as response:
                data = response.read()  # a `bytes` object
                out_file.write(data)
            self._stop_event.set()
        except StopIteration:
            sam_logger.debug(f"Download thread cancelled ({self.yt_id})")
            out_file.truncate(0)
            os.remove(f"cache/{yt_id}.m4a")
        finally:
            sam_logger.debug(f"Stopped download thread ({self.yt_id})")
            self.downloading = False
            thread_counts -= 1

    def stop(self):
        if not self.is_stopped():
            self._stop_event.set()
            ctype_async_raise(self.ident, StopIteration)
        else:
            sam_logger.debug(f"Already stopped download thread ({self.yt_id})")

    def is_stopped(self):
        return self._stop_event.is_set()


class GetSongData(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self, target=self.iterate_added_songs, daemon=True)
        self.list = []

    def add_song(self, song, after=None):
        self.list.append([song, after])

    def iterate_added_songs(self):
        global thread_counts
        thread_counts += 1
        while True:
            try:
                song = self.list[0]
                song[0].get_video_info()
                if song[1]:
                    threading.Thread(target=song[1], daemon=True).start()
                self.list.pop(0)
            except IndexError:
                pass


class SongTimer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self, target=self.run, daemon=True)
        self.seconds = 0

    def run(self):
        global thread_counts
        thread_counts += 1
        try:
            while True:
                self.seconds += 0.1
                time.sleep(0.1)
        except StopIteration:
            thread_counts -= 1


class Song(yt_dlp.YoutubeDL):
    def __init__(self, url_or_search_term):
        yt_dlp.YoutubeDL.__init__(self, {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'webm',
            }],
            'prefer_ffmpeg': True,
            'quiet': True})

        # video data
        self.video_info = None
        self.yt_id = None
        self.youtube_url_or_search_term = url_or_search_term

        self.youtube = None
        self.thumbnail = None
        self.title = None
        self.author = None
        self.duration = {}
        self.download_thread = None
        self.audio_url = None

    def get_video_id(self, url):
        regex = re.compile(
            r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?(?P<id>['
            r'A-Za-z0-9\-=_]{11})')
        match = regex.match(url)
        if match:
            self.yt_id = match.group('id')
            self.youtube = True
        else:
            self.youtube = False

    def get_video_info(self):
        if validators.url(self.youtube_url_or_search_term[0]):
            self.get_video_id(self.youtube_url_or_search_term[0])
            if self.youtube:
                self.video_info = self.extract_info("https://youtu.be/{0}".format(self.yt_id), download=False)
            else:
                self.audio_url = self.youtube_url_or_search_term[0]
                return
        else:
            sam_logger.debug(f"Searching for {' '.join(self.youtube_url_or_search_term)}")
            self.video_info = \
                self.extract_info(
                    f"ytsearch1:{' '.join(self.youtube_url_or_search_term)}", download=False)['entries'][0]
            if self.video_info:
                sam_logger.debug(f"Found {' '.join(self.youtube_url_or_search_term)}")
                self.get_video_id(self.video_info['webpage_url'])
            else:
                sam_logger.debug(f"Couldn't find {' '.join(self.youtube_url_or_search_term)}")
                self.yt_id = None
        sam_logger.debug(f"Getting youtube video metadata ({self.yt_id})")
        self.title = self.video_info['title']
        self.author = self.video_info['uploader']
        formats = self.video_info['formats']
        specified_format = None
        for i in formats:
            if not i["height"] and not i["width"] and i["ext"] == "m4a" and i["format_note"] == "low":
                specified_format = i
        self.audio_url = specified_format["url"]
        thumbnails = self.video_info['thumbnails']
        thumbnails.reverse()
        self.thumbnail = thumbnails[0]['url']
        self.duration['total_seconds'] = self.video_info['duration']
        self.duration['length'] = seconds_to_minutes_display(self.video_info['duration'])
        sam_logger.debug(f"Got youtube video metadata ({self.yt_id})")

    def get_audio_url_or_path(self):
        if os.path.isfile("cache/{yt_id}.m4a".format(yt_id=self.yt_id)):
            sam_logger.debug("No need to cache video")
            return f"cache/{self.yt_id}.m4a", False, f"cache/{self.yt_id}.m4a"
        else:
            sam_logger.debug(f"Caching video ({self.yt_id})")
            self.download_thread = DownloadUrl(self.audio_url, self.yt_id)
            self.download_thread.start()
            return self.audio_url, True, f"cache/{self.yt_id}.m4a"

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
        self.video_getter = GetSongData()
        self.video_getter.start()

    def ensure_guild_in_list(self, guild_id):
        if not guild_id in self.servers:
            self.servers[guild_id] = {
                'current_song': None,
                'queue': [],
                'loop': False,
                'timer': None,
                'skipping': False
            }

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

        self.ensure_guild_in_list(ctx.guild.id)

        await ctx.send("qued")
        song = Song(url_or_search_term)
        self.video_getter.add_song(song, lambda: self.play_song(ctx, song))

    def play_song(self, ctx, song):
        self.servers[ctx.guild.id]['skipping'] = False
        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if not voice_client.is_playing():
            self.servers[ctx.guild.id]['timer'] = SongTimer()
            self.servers[ctx.guild.id]['current_song'] = song
            if song.youtube:
                asyncio.run_coroutine_threadsafe(
                    ctx.send(f"Currently playing **{song.title}**"), self.bot.loop)
                audio_path, requires_caching, real_audio_path = song.get_audio_url_or_path()
                if requires_caching:
                    voice_client.play(source=FFmpegPCMAudio(audio_path), after=lambda e: self.play_next(ctx))
                    self.servers[ctx.guild.id]['timer'].start()
                    song.download_thread.join()
                    if self.servers[ctx.guild.id]['skipping']:
                        self.servers[ctx.guild.id]['current_song'] = None
                        ctype_async_raise(self.servers[ctx.guild.id]['timer'].ident, StopIteration)
                        self.servers[ctx.guild.id]['skipping'] = False
                    else:
                        voice_client.stop()
                        voice_client.play(source=FFmpegPCMAudio(
                            real_audio_path, before_options=f"-vn -ss {self.servers[ctx.guild.id]['timer'].seconds}"),
                            after=lambda e: self.play_next(ctx))
                else:
                    voice_client.play(source=FFmpegPCMAudio(real_audio_path), after=lambda e: self.play_next(ctx))
                    self.servers[ctx.guild.id]['timer'].start()
            else:
                voice_client.play(source=FFmpegPCMAudio(song.audio_url), after=lambda e: self.play_next(ctx))
                self.servers[ctx.guild.id]['timer'].start()
        else:
            self.servers[ctx.guild.id]['queue'].append(song)

    def play_next(self, ctx):
        ctype_async_raise(self.servers[ctx.guild.id]['timer'].ident, StopIteration)
        self.servers[ctx.guild.id]['current_song'] = None
        if len(self.servers[ctx.guild.id]['queue']) >= 1:
            song = self.servers[ctx.guild.id]['queue'][0]
            self.servers[ctx.guild.id]['queue'].pop(0)
            self.play_song(ctx, song)

    @commands.command(name="skip", aliases=['s'])
    async def skip(self, ctx):
        if self.servers[ctx.guild.id]['current_song']:
            self.servers[ctx.guild.id]['current_song'].download_thread.stop()
            self.servers[ctx.guild.id]['skipping'] = True
        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        voice_client.stop()

    @commands.command(name="queue", aliases=["q"])
    async def queue(self, ctx):
        self.ensure_guild_in_list(ctx.guild.id)

        emb = discord.Embed(title="Queue")
        if self.servers[ctx.guild.id]['current_song']:
            if self.servers[ctx.guild.id]['current_song'].youtube:
                emb.add_field(name=f"Currently playing. {self.servers[ctx.guild.id]['current_song'].title}",
                              value=self.servers[ctx.guild.id]['current_song'].duration['length'],
                              inline=False)
            else:
                emb.add_field(name=f"Currently playing. {self.servers[ctx.guild.id]['current_song'].audio_url}",
                              value="MP3 URL",
                              inline=False)
        if self.servers[ctx.guild.id]['queue']:
            for song in self.servers[ctx.guild.id]['queue']:
                if self.servers[ctx.guild.id]['current_song'].youtube:
                    emb.add_field(name=f"{self.servers[ctx.guild.id]['queue'].index(song) + 1}. {song.title}",
                                  value=song.duration['length'],
                                  inline=False)
                else:
                    emb.add_field(name=f"Currently playing. {self.servers[ctx.guild.id]['current_song'].audio_url}",
                                  value="MP3 Url",
                                  inline=False)
        else:
            emb.add_field(name="Nothing is queued", value="Use ,play to add something.")
        await ctx.send(embed=emb)

    @commands.command(name="loop")
    async def loop(self, ctx):
        self.servers[ctx.guild.id]['loop'] = True

    # @commands.command(name="stop")
    # async def stop(self, ctx):
    #     sam_logger.debug("Stopping Song")
    #     voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
    #     voice_client.stop()
    #     pass

    @commands.command(name="playing", aliases=['np'])
    async def playing(self, ctx):
        if self.servers[ctx.guild.id]['current_song'].youtube:
            await ctx.send(f"Playing song: **{self.servers[ctx.guild.id]['current_song'].title}**\n"
                           f"{seconds_to_minutes_display(round(self.servers[ctx.guild.id]['timer'].seconds))}/"
                           f"{self.servers[ctx.guild.id]['current_song'].duration['length']}")
        else:
            await ctx.send(f"Playing song: **{self.servers[ctx.guild.id]['current_song'].audio_url}** MP3 Url\n"
                           f"{seconds_to_minutes_display(round(self.servers[ctx.guild.id]['timer'].seconds))}")



def setup(bot):
    bot.add_cog(Music(bot))


def teardown(bot):
    bot.remove_cog("Music")