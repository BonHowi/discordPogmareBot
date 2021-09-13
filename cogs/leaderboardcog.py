import discord
import pandas as pd
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

    # Send leaderboards to specified channel
    async def update_leaderboards(self, channel: int, ch_type: str):
        top_ch = self.bot.get_channel(channel)
        spots_df = await DatabaseCog.db_get_spots_df()
        spots_df = pd.DataFrame(spots_df)
        spots_df["total"] = spots_df["legendary"] * legend_multiplier + spots_df["rare"]
        spots_df_top = spots_df.sort_values(ch_type, ascending=False).head(15)
        spots_df_top = spots_df_top.reset_index(drop=True)
        await top_ch.purge()

        top_print = []
        for index, row in spots_df_top.iterrows():
            member_stats = [f"**[{index + 1}]**  {row['display_name']} - {row[ch_type]}"]
            top_print.append(member_stats)
        top_print = ['\n'.join([elem for elem in sublist]) for sublist in top_print]
        top_print = "\n".join(top_print)
        embed_command = discord.Embed(title=f"TOP 15 {ch_type.upper()}", description=top_print,
                                      color=0xf1c232)
        member = self.bot.get_user(spots_df_top['member_id'].iloc[0])
        embed_command.set_thumbnail(url=f'{member.avatar_url}')
        await top_ch.send(embed=embed_command)

    # Update member spotting role(total/common)
    async def update_role(self, guild, guild_member, spot_roles, common: bool):
        roles_type = "common" if common else "total"
        try:
            spots_df = await DatabaseCog.db_get_member_stats(guild_member.id)
            spots_df["total"] = spots_df["legendary"] * legend_multiplier + spots_df["rare"]
            roles_list = [key for (key, value) in spot_roles.items() if spots_df.loc[0, roles_type] >= value]
            if roles_list:
                await self.create_role(guild, roles_list[-1])
                role_new = get(guild.roles, name=roles_list[-1])
                await guild_member.add_roles(role_new)
                if len(roles_list) > 1:
                    await self.create_role(guild, roles_list[-2])
                    role_old = get(guild.roles, name=roles_list[-2])
                    await self.create_role(guild, roles_list[-2])
                    await guild_member.remove_roles(role_old)
        except KeyError as e:
            print(e)

    # Update members' spotting roles
    async def update_member_roles(self):
        guild = self.bot.get_guild(self.bot.guild[0])
        spot_roles_total = self.bot.config["total_milestones"][0]
        spot_roles_common = self.bot.config["common_milestones"][0]
        for guild_member in guild.members:
            await self.update_role(guild, guild_member, spot_roles_total, False)
            await self.update_role(guild, guild_member, spot_roles_common, True)

    # @tasks.loop(seconds=15)
    @tasks.loop(minutes=15)
    async def update_leaderboards_loop(self):
        await self.update_leaderboards(self.bot.ch_leaderboards, "total")
        await self.update_leaderboards(self.bot.ch_leaderboards_common, "common")
        await self.update_member_roles()
        dt_string = self.bot.get_current_time()
        print(f'({dt_string})\t[{self.__class__.__name__}]: Leaderboards updated')

    @update_leaderboards_loop.before_loop
    async def before_update_leaderboards_loop(self):
        dt_string = self.bot.get_current_time()
        print(f'({dt_string})\t[{self.__class__.__name__}]: Waiting until Bot is ready')
        await self.bot.wait_until_ready()


def setup(bot: commands.Bot):
    bot.add_cog(LeaderboardsCog(bot))
