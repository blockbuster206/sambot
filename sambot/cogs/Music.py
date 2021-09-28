import discord
import pafy
from discord import FFmpegPCMAudio, PCMVolumeTransformer
from discord.ext import commands, tasks
import logging

sam_logger = logging.getLogger("SAM-Bot" + "." + __name__)


class Music(commands.Cog, name="Music"):
    def __init__(self, bot):
        self.bot = bot
        self.playing_index = 0
        self.queue = []
        self.music_seconds = None
        self.current_seconds = None
        self.video_message = None

    def seconds_to_minutes_display(self, seconds):
        return f"{seconds // 60:02d}:{seconds % 60:02d}"
        
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

        self.queue.append(pafy.new(url))

        sam_logger.debug("Getting voice client")

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

            video = self.queue[self.playing_index]
            audio = video.getbestaudio()

            video_embed = discord.Embed(title=f"Playing {video.title} : Made by {video.author}")
            video_embed.set_image(url=video.getbestthumb() + "?size=640x385")
            video_embed.set_footer(text="Requested by {user}".format(user=ctx.author.name))

            video_embed.add_field(name="Duration", value=video.duration)

            await self.video_message.edit(content=None, embed=video_embed)
            currently_playing_ffmpeg = FFmpegPCMAudio(source=audio.url)
            voice_client.play(currently_playing_ffmpeg)
            sam_logger.debug("Playing audio")

            self.current_seconds = 0
            self.music_seconds = video.length

            self.music_player_loop.start(ctx)


    @commands.command(name="skip", aliases=("s",))
    async def skip(self, ctx):
        self.music_player_loop.stop()
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

    @commands.command(name="queue", aliases=("q",))
    async def queue(self, ctx):
        emb = discord.Embed(title="Queue")
        if self.queue:
            for i in range(len(self.queue)):
                item = self.queue[i]
                emb.add_field(name=f"{i+1}. {item.title}", value=item.duration, inline=False)
        else:
            emb.add_field(name="Nothing playing", value="Use ,play to play something.")
        await ctx.send(embed=emb)

    @commands.command(name="stop")
    async def stop(self, ctx):
        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        voice_client.stop()
        self.music_player_loop.stop()

    @commands.command(name="playing", aliases=['np'])
    async def playing(self, ctx):
        playing_progress = self.seconds_to_minutes_display(self.current_seconds)
        song_length = self.seconds_to_minutes_display(self.music_seconds)
        await ctx.send(f"Playing song: {self.queue[self.playing_index].title}\nProgress: {playing_progress} of {song_length}")




def setup(bot):
    bot.add_cog(Music(bot))


def teardown(bot):
    bot.remove_cog("Music")
