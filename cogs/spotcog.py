"""
Cog with role related commands available in the Bot.

Current commands:
/

"""
import discord
from discord.utils import get
from discord.ext import commands
from discord_slash import cog_ext, SlashContext
from cogs.base import BaseCog
from modules.get_settings import get_settings

guild_ids = get_settings("guild")


class SpotCog(BaseCog):
    def __init__(self, base):
        super().__init__(base)

    # Ping monster role
    @commands.Cog.listener()
    async def on_message(self, ctx):
        if ctx.author.id == self.bot.user.id:
            return

        prefix = "/"
        cords_beginning = ['-', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
        if ctx.channel.id == self.bot.CH_COMMON:
            if ctx.content[0] in cords_beginning:
                pass
            else:
                await ctx.delete()

        elif ctx.channel.category.id == self.bot.CAT_SPOTTING:
            if ctx.content.startswith(prefix):
                spotted_monster = await self.get_monster(ctx, ctx.content.replace(prefix, ""))
                if spotted_monster:
                    role = get(ctx.guild.roles, name=spotted_monster["name"])
                    await ctx.channel.send(f"{role.mention}")
            elif ctx.content[0] in cords_beginning:
                return
            else:
                await ctx.channel.send(
                    f"{ctx.author.mention} Use {self.bot.get_channel(self.bot.CH_DISCUSSION_EN).mention}",
                    delete_after=5.0)


def setup(bot: commands.Bot):
    bot.add_cog(SpotCog(bot))
