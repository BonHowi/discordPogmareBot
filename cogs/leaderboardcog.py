import discord
import pandas as pd
from discord.ext import commands, tasks
from discord.utils import get
from discord_slash import cog_ext, SlashContext
import cogs.cogbase as cogbase
from cogs.databasecog import DatabaseCog
from modules.utils import get_dominant_color


class LeaderboardsCog(cogbase.BaseCog):
    def __init__(self, base):
        super().__init__(base)

        self.common_total = 0
        self.update_leaderboards_loop.start()

    def cog_unload(self):
        self.update_leaderboards_loop.cancel()

    # Send leaderboards to specified channel
    async def update_leaderboard(self, channel: int, ch_type: str) -> None:
        top_ch = self.bot.get_channel(channel)
        spots_df = await DatabaseCog.db_get_spots_df()
        monsters_df = await DatabaseCog.db_get_monster_spots_df()
        # Hard coded because there is only one interesting monster
        event_monster_df = monsters_df.filter(["member_id", "Nightmare"], axis=1)
        spots_df = pd.merge(spots_df, event_monster_df, on=["member_id"])
        spots_df = spots_df.drop(spots_df[spots_df.member_id == self.bot.user.id].index)
        spots_df["total"] = spots_df["legendary"] * self.legend_multiplier + spots_df["rare"] + (spots_df["Nightmare"])
        spots_df_top = spots_df.sort_values(ch_type, ascending=False).head(15)
        spots_df_top = spots_df_top.reset_index(drop=True)
        try:
            await top_ch.purge()
        except discord.errors.NotFound:
            pass
        top_print = []
        top_user_id = int(spots_df_top.at[0, 'member_id'])
        for index, row in spots_df_top.iterrows():
            if row[ch_type] == 0:
                member_stats = ""
            elif row['member_id'] == top_user_id:
                member_stats = [f"**[{index + 1}]**  {row['display_name']} - **{row[ch_type]}**"]
            else:
                member_stats = [f"**[{index + 1}]**  {row['display_name']} - {row[ch_type]}"]
            top_print.append(member_stats)
        top_print = ['\n'.join([elem for elem in sublist]) for sublist in top_print]
        top_print = "\n".join(top_print)
        ch_type = ''.join([i for i in ch_type if not i.isdigit()])

        top_user = get(self.bot.get_all_members(), id=top_user_id)
        top_user_color = get_dominant_color(top_user.avatar_url)
        embed_command = discord.Embed(title=f"TOP 15 {ch_type.upper()}", description=top_print,
                                      color=top_user_color)
        member = self.bot.get_user(spots_df_top['member_id'].iloc[0])
        embed_command.set_thumbnail(url=f'{member.avatar_url}')
        dt_string = self.bot.get_current_time()
        embed_command.set_footer(text=f"{dt_string}")
        await top_ch.send(embed=embed_command)
        self.create_log_msg(f"Leaderboards updated - {ch_type}")

    # Update member spotting role(total/common)
    async def update_role(self, guild, guild_member, spot_roles: dict, common: bool) -> None:
        roles_type = "common" if common else "total"
        try:
            spots_df = await DatabaseCog.db_get_member_stats(guild_member.id)
            if not common:
                spots_df["total"] = spots_df["legendary"] * self.legend_multiplier + spots_df["rare"]
            roles_list = [key for (key, value) in spot_roles.items() if spots_df.loc[0, roles_type] >= value]
            if roles_list:
                await self.update_role_ext(guild, roles_list, guild_member)
        except KeyError as e:
            print(e)

    async def update_role_ext(self, guild, roles_list: list, guild_member) -> None:
        await self.create_new_role(guild, roles_list[-1])
        role_new = get(guild.roles, name=roles_list[-1])
        if role_new not in guild_member.roles:
            await guild_member.add_roles(role_new)
        if len(roles_list) > 1:
            await self.create_new_role(guild, roles_list[-2])
            role_old = get(guild.roles, name=roles_list[-2])
            if role_old in guild_member.roles:
                await guild_member.remove_roles(role_old)

    # Update members' spotting roles
    async def update_member_roles(self) -> None:
        guild = self.bot.get_guild(self.bot.guild[0])
        spot_roles_total = self.bot.config["total_milestones"][0]
        spot_roles_common = self.bot.config["common_milestones"][0]
        for guild_member in guild.members:
            await self.update_role(guild, guild_member, spot_roles_total, False)
            await self.update_role(guild, guild_member, spot_roles_common, True)

    async def update_event_leaderboards(self, channel: int, event_monster: str) -> None:
        top_ch = self.bot.get_channel(channel)
        spots_df = await DatabaseCog.db_get_monster_spots_df()
        event_monster_df = spots_df.filter(["member_id", event_monster], axis=1)
        member_names_df = await DatabaseCog.db_get_member_names()

        event_df = pd.merge(event_monster_df, member_names_df, on=["member_id"])
        event_df = event_df.drop(event_df[event_df.member_id == self.bot.user.id].index)
        event_df = event_df.sort_values(event_monster, ascending=False).head(15)
        event_df = event_df.reset_index(drop=True)
        try:
            await top_ch.purge()
        except discord.errors.NotFound:
            pass
        top_print = []
        top_user_id = int(event_df.at[0, 'member_id'])
        for index, row in event_df.iterrows():
            if row[event_monster] == 0:
                member_stats = ""
            elif row['member_id'] == top_user_id:
                member_stats = [f"**[{index + 1}]**  {row['display_name']} - **{row[event_monster]}**"]
            else:
                member_stats = [f"**[{index + 1}]**  {row['display_name']} - {row[event_monster]}"]
            top_print.append(member_stats)
        top_print = ['\n'.join([elem for elem in sublist]) for sublist in top_print]
        top_print = "\n".join(top_print)
        ch_type = ''.join([i for i in event_monster if not i.isdigit()])

        top_user = get(self.bot.get_all_members(), id=top_user_id)
        top_user_color = get_dominant_color(top_user.avatar_url)
        embed_command = discord.Embed(title=f"TOP 15 {ch_type.upper()}", description=top_print,
                                      color=top_user_color)
        member = self.bot.get_user(event_df['member_id'].iloc[0])
        embed_command.set_thumbnail(url=f'{member.avatar_url}')
        dt_string = self.bot.get_current_time()
        embed_command.set_footer(text=f"{dt_string}")
        await top_ch.send(embed=embed_command)
        self.create_log_msg(f"Leaderboards updated - event")

    async def update_leaderboards(self) -> None:
        await self.update_leaderboard(self.bot.ch_leaderboards, "total")
        await self.update_leaderboard(self.bot.ch_leaderboards_common, "common")
        await self.update_event_leaderboards(self.bot.ch_leaderboards_event, "Nightmare")
        self.create_log_msg(f"All leaderboards updated")
        await self.update_member_roles()
        self.create_log_msg(f"Members' roles updated")

    @tasks.loop(minutes=15)
    async def update_leaderboards_loop(self) -> None:
        await self.update_leaderboards()

    @tasks.loop(minutes=15)
    async def update_leaderboards_loop(self) -> None:
        await self.update_leaderboards()

    @update_leaderboards_loop.before_loop
    async def before_update_leaderboards_loop(self) -> None:
        self.create_log_msg(f"Waiting until Bot is ready")
        common_ch = self.bot.get_channel(self.bot.ch_common)
        try:
            async for _ in common_ch.history(limit=None, oldest_first=True):
                self.common_total += 1
        except AttributeError:
            pass
        await self.bot.wait_until_ready()

    @cog_ext.cog_slash(name="reloadLeaderboards", guild_ids=cogbase.GUILD_IDS,
                       description="Reload leaderboards",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_MODS)
    async def reload_leaderboards(self, ctx: SlashContext) -> None:
        await ctx.send(f"Leaderboards reloaded", hidden=True)
        await self.update_leaderboards()


def setup(bot: commands.Bot) -> None:
    bot.add_cog(LeaderboardsCog(bot))
