from __future__ import unicode_literals
import discord
from discord.ext import commands
import logging
import youtube_dl

sam_logger = logging.getLogger("SAM-Bot" + "." + __name__)


class Music(commands.Cog, name="Music"):
    def __init__(self, bot):
        self.bot = bot
        self.ydl_opts = {
            'format': "bestaudio/best",
            'quiet': True
        }

    @commands.command(name="play")
    async def play(self, ctx, url):
        video_embed = discord.embeds.Embed(title="video")
        with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
            sam_logger.debug("Getting audio url")
            song_info = ydl.extract_info(url, download=False)
            sam_logger.debug("Sending url")
            url = song_info['formats'][0]['url']
            video_embed.add_field(name=song_info['title'], value=url)
            await ctx.send(embed=video_embed)

def setup(bot):
    bot.add_cog(Music(bot))


def teardown(bot):
    bot.remove_cog("Music")
