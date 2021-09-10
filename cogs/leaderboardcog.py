import discord
from discord.ext import commands, tasks
from discord.utils import get
from discord_slash import cog_ext
import cogs.cogbase as cogbase
from cogs.databasecog import DatabaseCog

legend_multiplier = 5


class LeaderboardsCog(cogbase.BaseCog):
    def __init__(self, base):
        super().__init__(base)
        self.update_leaderboards_loop.start()

    async def update_leaderboards(self, channel: int, ch_type: str):
        top_ch = self.bot.get_channel(channel)

        spots_df = await DatabaseCog.db_get_spots_df()
        spots_df["total"] = spots_df["legendary"] * legend_multiplier + spots_df["rare"]
        spots_df_top = spots_df.sort_values(ch_type, ascending=False, ignore_index=True).head(15)
        spots_df_top = spots_df_top[["display_name", ch_type]]

        await top_ch.purge(limit=10)

        top_print = []
        for index, row in spots_df_top.iterrows():
            member_stats = [f"**[{index + 1}]**  {row['display_name']} - {row[ch_type]}"]
            top_print.append(member_stats)
        top_print = ['\n'.join([elem for elem in sublist]) for sublist in top_print]
        top_print = "\n".join(top_print)
        embed_command = discord.Embed(title="TOP 15", description=top_print,
                                      color=0x00ff00)
        await top_ch.send(embed=embed_command)

    async def update_role(self, guild, guild_member, spot_roles, common: bool):
        roles_type = "common" if common else "total"
        try:
            spots_df = await DatabaseCog.db_get_member_stats(guild_member.id)
            spots_df["total"] = spots_df["legendary"] * legend_multiplier + spots_df["rare"]
            roles_list = [key for (key, value) in spot_roles.items() if spots_df.at[0, roles_type] >= value]
            if roles_list:
                await self.create_role(guild, roles_list)
                role_new = get(guild.roles, name=roles_list[-1])
                await guild_member.add_roles(role_new)
                if len(roles_list) > 1:
                    role_old = get(guild.roles, name=roles_list[-2])
                    await guild_member.remove_roles(role_old)
        except KeyError as e:
            print(e)

    async def create_role(self, guild, roles_list):
        if get(guild.roles, name=roles_list[-1]):
            pass
        else:
            await guild.create_role(name=roles_list[-1])
            print(f"[{self.__class__.__name__}]: {roles_list[-1]} role created")

    async def update_member_roles(self):
        guild = self.bot.get_guild(self.bot.guild[0])
        spot_roles_total = self.bot.config["total_milestones"][0]
        spot_roles_common = self.bot.config["common_milestones"][0]
        for guild_member in guild.members:
            await self.update_role(guild, guild_member, spot_roles_total, False)
            await self.update_role(guild, guild_member, spot_roles_common, True)

    @tasks.loop(minutes=15)
    async def update_leaderboards_loop(self):
        await self.update_leaderboards(self.bot.ch_leaderboards, "total")
        await self.update_leaderboards(self.bot.ch_leaderboards_common, "common")
        await self.update_member_roles()
        print(f'[{self.__class__.__name__}]: Leaderboards updated')

    @update_leaderboards_loop.before_loop
    async def before_update_leaderboards_loop(self):
        print(f'[{self.__class__.__name__}]: Waiting until Bot is ready')
        await self.bot.wait_until_ready()

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


def setup(bot: commands.Bot):
    bot.add_cog(LeaderboardsCog(bot))
