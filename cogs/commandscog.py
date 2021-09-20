"""
Cog with general commands available in the Bot.

Current commands:
/ping -     check Bot latency
/clear -    clear x messages on the channel
/exit | !exit -     end Bot's runtime and disconnect from the server
/warn -     warn @user with reason
/warns -    send @user warns to author's DM
/nword -    Changes N-Word killed channel name  -   UNSTABLE
/updatetotmem - Update #TotalMembers channel
/updatecommon - Update common spotting channel with new monster name
/tba
"""
import discord
from discord.utils import get
from googletrans import Translator
import cogs.cogbase as cogbase
from discord.ext import commands
from discord_slash import cog_ext, SlashContext
from cogs.databasecog import DatabaseCog
from cogs.leaderboardcog import legend_multiplier


class CommandsCog(cogbase.BaseCog):
    def __init__(self, base):
        super().__init__(base)

    # Get own spotting stats
    @cog_ext.cog_slash(name="myStats", guild_ids=cogbase.GUILD_IDS,
                       description="Get your spot stats",
                       default_permission=True)
    async def get_stats(self, ctx):
        spot_roles = self.bot.config["total_milestones"][0]
        guild = self.bot.get_guild(self.bot.guild[0])
        spots_df = await DatabaseCog.db_get_member_stats(ctx.author.id)
        spots_df["total"] = spots_df["legendary"] * legend_multiplier + spots_df["rare"]

        role_new = ""
        spots_for_new = -1
        roles_list = [key for (key, value) in spot_roles.items() if spots_df.at[0, "total"] < value]
        values_list = [value for (key, value) in spot_roles.items() if spots_df.at[0, "total"] < value]
        if roles_list:
            role_new = get(guild.roles, name=roles_list[0])
            spots_for_new = values_list[0]

        message = f"**Legends**: {spots_df.at[0, 'legendary']}\n" \
                  f"**Rares**: {spots_df.at[0, 'rare']}\n" \
                  f"**Commons**: {spots_df.at[0, 'common']}\n\n" \
                  f"**Total points**: {spots_df.at[0, 'total']}\n" \
                  f"**Progress**: {spots_df.at[0, 'total']}/{spots_for_new}\n" \
                  f"**Next role**: _{role_new}_"

        await ctx.send(f"{ctx.author.mention} stats:\n{message}", hidden=True)

    # Pool
    @cog_ext.cog_slash(name="poll", guild_ids=cogbase.GUILD_IDS,
                       description="Create pool",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_MODS)
    async def poll(self, ctx, *, poll_info):
        emb = (discord.Embed(description=poll_info, colour=0x36393e))
        emb.set_author(name=f"Poll by {ctx.author.display_name}")
        try:
            poll_message = await ctx.send(embed=emb)
            await poll_message.add_reaction("\N{THUMBS UP SIGN}")
            await poll_message.add_reaction("\N{THUMBS DOWN SIGN}")
        except Exception as e:
            await ctx.send(f"Oops, I couldn't react to the poll. Check that I have permission to add reactions! "
                           f"```py\n{e}```")

    # Translate
    @cog_ext.cog_slash(name="translate", guild_ids=cogbase.GUILD_IDS,
                       description="Translate message",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_MODS)
    async def translate(self, ctx: SlashContext, message: str):
        # Translates the language and converts it to English
        translator = Translator()
        translated_message = translator.translate(message)
        await ctx.send(f"`{message}` -> `{translated_message.text}`", hidden=True)


def setup(bot: commands.Bot):
    bot.add_cog(CommandsCog(bot))
