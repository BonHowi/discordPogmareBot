"""
Cog with general commands available in the Bot.
"""

import discord
from discord.ext import commands
from discord.utils import get
from discord_slash import cog_ext, SlashContext
from googletrans import Translator

import cogs.cogbase as cogbase
from cogs.databasecog import DatabaseCog
from modules.utils import get_dominant_color


class CommandsCog(cogbase.BaseCog):
    def __init__(self, base):
        super().__init__(base)

    # Get own spotting stats
    @cog_ext.cog_slash(name="myStats", guild_ids=cogbase.GUILD_IDS,
                       description="Get your spotting stats",
                       default_permission=True)
    async def get_stats_own(self, ctx: SlashContext) -> None:
        embed = await self.get_stats(ctx.author)
        await ctx.send(embed=embed, hidden=True)

    # Get and show own spotting stats
    @cog_ext.cog_slash(name="myStatsShow", guild_ids=cogbase.GUILD_IDS,
                       description="Get your spotting stats and show it to other members",
                       default_permission=True)
    async def show_stats_own(self, ctx: SlashContext) -> None:
        embed = await self.get_stats(ctx.author)
        await ctx.send(embed=embed)

    # Get member's spotting stats
    @cog_ext.cog_slash(name="memberStats", guild_ids=cogbase.GUILD_IDS,
                       description="Get member's spotting stats",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_MODS)
    async def get_stats_member(self, ctx: SlashContext, member: discord.Member) -> None:
        embed = await self.get_stats(member)
        await ctx.send(embed=embed, hidden=True)

    async def get_stats(self, member: discord.Member) -> discord.Embed:
        spot_roles = self.bot.config["total_milestones"][0]
        guild = self.bot.get_guild(self.bot.guild[0])
        spots_df = await DatabaseCog.db_get_member_stats(member.id)
        spots_df["total"] = spots_df["legendary"] * self.legend_multiplier + spots_df["rare"]

        role_next = ""
        spots_for_new = ""
        roles_list = [key for (key, value) in spot_roles.items() if spots_df.at[0, "total"] < value]
        values_list = [value for (key, value) in spot_roles.items() if spots_df.at[0, "total"] < value]
        if roles_list:
            role_next = get(guild.roles, name=roles_list[0])
            spots_for_new = values_list[0]

        message: str = f"**Legends**: {spots_df.at[0, 'legendary']}\n" \
                       f"**Rares**: {spots_df.at[0, 'rare']}\n" \
                       f"**Commons**: {spots_df.at[0, 'common']}\n\n" \
                       f"**Total points**: {spots_df.at[0, 'total']}\n" \
                       f"**Progress**: {spots_df.at[0, 'total']}/{spots_for_new}\n" \
                       f"**Next role**: {role_next.name}"

        member_color = get_dominant_color(member.avatar_url)
        embed = discord.Embed(title=f"{member} spotting stats", description=message,
                              color=member_color)
        embed.set_thumbnail(url=f'{member.avatar_url}')
        return embed

    # Pool
    @cog_ext.cog_slash(name="poll", guild_ids=cogbase.GUILD_IDS,
                       description="Create pool",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_MODS)
    async def poll(self, ctx: SlashContext, *, title: str, content: str = "") -> None:
        author_color = get_dominant_color(ctx.author.avatar_url)
        emb = (discord.Embed(title=f"{title}", description=content, color=author_color))
        try:
            poll_message = await ctx.send(embed=emb)
            await poll_message.add_reaction("\N{THUMBS UP SIGN}")
            await poll_message.add_reaction("\N{THUMBS DOWN SIGN}")
        except Exception as e:
            await ctx.send(f"Oops, I couldn't react to the poll. Check that I have permission to add reactions! "
                           f"```py\n{e}```", hidden=True)

    # Translate
    @cog_ext.cog_slash(name="translate", guild_ids=cogbase.GUILD_IDS,
                       description="Translate message",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_MODS)
    async def translate(self, ctx: SlashContext, message: str) -> None:
        # Translates the language and converts it to English
        translator = Translator()
        translated_message = translator.translate(message)
        await ctx.send(f"`{message}` -> `{translated_message.text}`", hidden=True)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(CommandsCog(bot))
