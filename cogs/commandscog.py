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
"""
import asyncio
import json
import os
from datetime import datetime

import discord
from discord.utils import get
from modules.get_settings import get_settings

import cogs.cogbase as cogbase
from discord.ext import commands
from discord_slash import cog_ext, SlashContext
from cogs.databasecog import DatabaseCog
from cogs.leaderboardcog import legend_multiplier
from modules.pull_config.pull_config import get_config


class CommandsCog(cogbase.BaseCog):
    def __init__(self, base):
        super().__init__(base)

    # GENERAL FUNCTIONS
    # Check latency
    @cog_ext.cog_slash(name="ping", guild_ids=cogbase.GUILD_IDS,
                       description="Function for checking latency",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_MODS)
    async def _ping(self, ctx: SlashContext):
        await ctx.send(f"Pong! {round(self.bot.latency * 1000)}ms", delete_after=4.0)

    # Clear messages
    @cog_ext.cog_slash(name="clear", guild_ids=cogbase.GUILD_IDS,
                       description="Function for clearing messages on channel",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_MODS)
    async def _purge(self, ctx: SlashContext, number):
        num_messages = int(number)
        await ctx.channel.purge(limit=num_messages)
        await ctx.send(f"Cleared {num_messages} messages!", delete_after=4.0)

    # Disconnect Bot
    @cog_ext.cog_slash(name="exit", guild_ids=cogbase.GUILD_IDS,
                       description="Turn off the bot",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_ADMINS)
    async def _exit(self, ctx: SlashContext):
        await ctx.send(f"Closing Bot", delete_after=1.0)
        dt_string = self.bot.get_current_time()
        print(f"({dt_string})\t[{self.__class__.__name__}]: Exiting Bot")
        await asyncio.sleep(3)
        await self.bot.close()

    # WARN FUNCTIONS

    # Warn user
    @cog_ext.cog_slash(name="warn", guild_ids=cogbase.GUILD_IDS,
                       description="Function for warning users",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_MODS)
    async def _warn(self, ctx: SlashContext, user: discord.User, reason: str):

        await DatabaseCog.db_add_warn(user.id, reason)
        await ctx.send(
            f"{user.mention} was warned for:\n*\"{reason}\"*\n")  # f"Number of warns: {len(current_user['reasons'])}")

    # Get list of user's warns
    @cog_ext.cog_slash(name="warns", guild_ids=cogbase.GUILD_IDS,
                       description="Function for warning users",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_MODS)
    async def _warns(self, ctx: SlashContext, user: discord.User):
        warns, nr_of_warns = await DatabaseCog.db_get_warns(user.id)
        nl = "\n"
        message = f"**{user.name}** has been warned **{nr_of_warns}** times\n\n_Reasons_:\n" \
                  f"{nl.join(warns)}\n"
        await ctx.author.send(message)
        await ctx.send(f"{user.name} warns has been sent to DM", hidden=True)

    # Remove all member's warns
    @cog_ext.cog_slash(name="removeWarns", guild_ids=cogbase.GUILD_IDS,
                       description="Function for removing user's all warns",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_ADMINS)
    async def remove_warns(self, ctx: SlashContext, user: discord.User):
        await DatabaseCog.db_remove_warns(user.id)
        await ctx.send(f"{user.display_name}'s warns were deleted", hidden=True)

    # Mute member
    @cog_ext.cog_slash(name="mute", guild_ids=cogbase.GUILD_IDS,
                       description="Mute member for x minutes",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_MODS)
    async def _mute(self, ctx: SlashContext, user: discord.User, time: int, reason: str):
        duration = time * 60
        guild = ctx.guild
        muted = discord.utils.get(guild.roles, name="Muted")

        if not muted:
            muted = await guild.create_role(name="Muted")
            for channel in guild.channels:
                await channel.set_permissions(muted, speak=False, send_messages=False, read_message_history=True,
                                              read_messages=False)
        await user.add_roles(muted, reason=reason)
        await ctx.send(f"{user.mention} Was muted by {ctx.author.name} for {time} min\n"
                       f"Reason: {reason}", delete_after=10)
        await asyncio.sleep(duration)
        await user.remove_roles(muted)
        await ctx.send(f"{user.mention}'s mute is over", delete_after=10)

    # KICK FUNCTIONS

    # Kick
    @cog_ext.cog_slash(name="kick", guild_ids=cogbase.GUILD_IDS,
                       description="Kicks member from the server",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_MODS)
    async def kick(self, ctx, user: discord.Member, *, reason=None):
        if user == ctx.author:
            return await ctx.send(
                f"{user.mention} You can't kick yourself", delete_after=5.0)
        await user.kick(reason=reason)
        if not reason:
            await ctx.send(f"{user} was kicked", delete_after=10.0)
            await user.send(f"You were kicked from {ctx.guild.name}")
        else:
            await ctx.send(f"{user} was kicked\nReason: {reason}", delete_after=10.0)
            await user.send(f"You were kicked from {ctx.guild.name}\nReason: {reason}")

    # TODO: Remove code repetition?
    # Ban
    @cog_ext.cog_slash(name="ban", guild_ids=cogbase.GUILD_IDS,
                       description="Bans member from the server",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_ADMINS)
    async def kick(self, ctx, user: discord.Member, *, reason=None):
        if user == ctx.author:
            return await ctx.send(
                f"{user.mention} You can't ban yourself", delete_after=5.0)
        await user.ban(reason=reason)
        if not reason:
            await ctx.send(f"{user} was banned", delete_after=10.0)
            await user.send(f"You were banned from {ctx.guild.name}")
        else:
            await ctx.send(f"{user} was banned \nReason: {reason}", delete_after=10.0)
            await user.send(f"You were banned from {ctx.guild.name}\nReason: {reason}")

    # Softban
    @cog_ext.cog_slash(name="softban", guild_ids=cogbase.GUILD_IDS,
                       description="Bans and unbans the user, so their messages are deleted",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_MODS)
    async def kick(self, ctx, user: discord.Member, *, reason=None):
        if user == ctx.author:
            return await ctx.send(
                f"{user.mention} You can't softban yourself", delete_after=5.0)
        await user.ban(reason=reason)
        await user.unban(reason=reason)
        if not reason:
            await ctx.send(f"{user} was softbanned", delete_after=10.0)
            await user.send(f"You were softbanned from {ctx.guild.name}")
        else:
            await ctx.send(f"{user} was softbanned \nReason: {reason}", delete_after=10.0)
            await user.send(f"You were softbanned from {ctx.guild.name}\nReason: {reason}")

    # CHANNEL NAMES UPDATES
    # Total member channel name
    @cog_ext.cog_slash(name="updateTotalMembers", guild_ids=cogbase.GUILD_IDS,
                       description="Update total number of members",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_MODS)
    async def update_member_count_command(self, ctx: SlashContext):
        await self.bot.update_member_count(ctx)
        await ctx.send(f"Total Members count updated", hidden=True)

    # Commons channel name
    @cog_ext.cog_slash(name="updateCommons", guild_ids=cogbase.GUILD_IDS,
                       description="Update common channel name",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_MODS)
    async def update_commons_ch_command(self, ctx: SlashContext):
        with open('./server_files/commons.txt') as f:
            try:
                commons = f.read().splitlines()
            except ValueError:
                print(ValueError)

        await self.update_commons_ch(ctx, commons)

        commons.append(commons.pop(commons.index(commons[0])))
        with open('./server_files/commons.txt', 'w') as f:
            for item in commons:
                f.write("%s\n" % item)

    async def update_commons_ch(self, ctx: SlashContext, commons):
        new_name = f"common {commons[0]}"
        common_ch = self.bot.get_channel(self.bot.ch_common)
        await discord.TextChannel.edit(common_ch, name=new_name)
        dt_string = self.bot.get_current_time()
        print(f"({dt_string})\t[{self.__class__.__name__}]: Common channel name updated: {commons[0]}")

        await common_ch.send(f"Common changed: {commons[0]}")
        await ctx.send(f"Common changed: {commons[0]}", hidden=True)

    # N-Word spotted channel name
    # Doesn't work if used too many times in a short period of time
    @cog_ext.cog_slash(name="nword", guild_ids=cogbase.GUILD_IDS,
                       description="Change N-Word channel name",
                       permissions=cogbase.PERMISSION_ADMINS)
    async def rename_nword_channel(self, ctx, status: str):
        new_status = status
        channel = self.bot.get_channel(self.bot.ch_nightmare_killed)
        if new_status in channel.name:
            await ctx.send(f"{channel.name} has been changed", hidden=True)
        else:
            await discord.VoiceChannel.edit(channel, name=f"N-Word fixed: {new_status}")
            await ctx.send(f"{channel.name} channel name has been changed", hidden=True)

    # OTHER

    # Pull config.json from Google Sheets
    @cog_ext.cog_slash(name="pullConfig", guild_ids=cogbase.GUILD_IDS,
                       description="Pull config from google sheets",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_ADMINS)
    async def pull_config(self, ctx: SlashContext):
        get_config()
        with open('server_files/config.json', 'r', encoding='utf-8-sig') as fp:
            self.bot.config = json.load(fp)
            await self.create_roles(ctx, True)
            await self.create_roles(ctx, False)
            dt_string = self.bot.get_current_time()
            print(f"({dt_string})\t[{self.__class__.__name__}]: Finished data pull")
        await ctx.send(f"Config.json updated", hidden=True)

    # Create roles if pull_config gets non existent roles
    async def create_roles(self, ctx: SlashContext, common: bool):
        milestones = "common_milestones" if common else "total_milestones"
        for mon_type in self.bot.config[milestones][0]:
            if get(ctx.guild.roles, name=mon_type):
                continue
            else:
                await ctx.guild.create_role(name=mon_type)
                dt_string = self.bot.get_current_time()
                print(f"({dt_string})\t[{self.__class__.__name__}]: {mon_type} role created")

    # Clear temp spots table in database
    @cog_ext.cog_slash(name="clearTempSpots", guild_ids=cogbase.GUILD_IDS,
                       description="Clear temp spots table in database",
                       permissions=cogbase.PERMISSION_ADMINS)
    async def clear_temp_spots_table(self, ctx):
        await DatabaseCog.db_clear_spots_temp_table()
        await ctx.send(f"Temp spots table was cleared", hidden=True)
        await self.reload_cog(ctx, "cogs.databasecog")

    # Reloads cog, very useful because there is no need to exit the bot after updating cog
    async def reload_cog(self, ctx: SlashContext, module: str):
        """Reloads a module."""
        dt_string = self.bot.get_current_time()
        try:
            self.bot.load_extension(f"{module}")
            await ctx.send(f'[{module}] loaded', hidden=True)
            print(f'({dt_string})\t[{self.__class__.__name__}]: {module} loaded')
        except commands.ExtensionAlreadyLoaded:
            self.bot.unload_extension(module)
            self.bot.load_extension(module)
            await ctx.send(f'[{module}] reloaded', hidden=True)
            print(f'({dt_string})\t[{self.__class__.__name__}]: {module} reloaded')
        except commands.ExtensionNotFound:
            await ctx.send(f'[{module}] not found', hidden=True)
            print(f'({dt_string})\t[{self.__class__.__name__}]: {module} not found')

    # Command for reloading specific cog
    @cog_ext.cog_slash(name="reloadCog", guild_ids=cogbase.GUILD_IDS,
                       description="Reload cog",
                       permissions=cogbase.PERMISSION_ADMINS)
    async def reload_cog_command(self, ctx: SlashContext, module: str):
        await self.reload_cog(ctx, module)

    # Command for reloading all cogs
    @cog_ext.cog_slash(name="reloadAllCogs", guild_ids=cogbase.GUILD_IDS,
                       description="Reload cog",
                       permissions=cogbase.PERMISSION_ADMINS)
    async def reload_all_cogs(self, ctx: SlashContext = None):
        for cog in list(self.bot.extensions.keys()):
            await self.reload_cog(ctx, cog)
        await ctx.send(f'All cogs reloaded', hidden=True)

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

    @cog_ext.cog_slash(name="saveCoordinates", guild_ids=cogbase.GUILD_IDS,
                       description="Get your spot stats",
                       permissions=cogbase.PERMISSION_ADMINS)
    async def save_coordinates(self, ctx: SlashContext):
        coords_df = await DatabaseCog.db_get_coords()
        coords_df[['latitude', 'longitude']] = coords_df['coords'].str.split(',', expand=True)
        coords_df.to_excel(r'server_files/coords.xlsx', index=False)
        await ctx.send(f"Coords saved", hidden=True)
        dt_string = self.bot.get_current_time()
        print(f'({dt_string})\t[{self.__class__.__name__}]: Coords saved to server_files/coords.xlsx')

    # Get member info
    @cog_ext.cog_slash(name="memberinfo", guild_ids=cogbase.GUILD_IDS,
                       description="Get member info",
                       permissions=cogbase.PERMISSION_ADMINS)
    async def memberinfo(self, ctx: SlashContext, *, user: discord.Member = None):
        if user is None:
            user = ctx.author
        date_format = "%a, %d %b %Y %I:%M %p"
        embed = discord.Embed(color=0xFF0000, description=user.mention)
        embed.set_author(name=str(user), icon_url=user.avatar_url)
        embed.set_thumbnail(url=user.avatar_url)
        embed.add_field(name="Joined Server", value=user.joined_at.strftime(date_format), inline=False)
        members = sorted(ctx.guild.members, key=lambda m: m.joined_at)
        embed.add_field(name="Join Position", value=str(members.index(user) + 1), inline=False)
        embed.add_field(name="Joined Discord", value=user.created_at.strftime(date_format), inline=False)
        if len(user.roles) > 1:
            role_string = ' '.join([r.mention for r in user.roles][1:])
            embed.add_field(name="Roles [{}]".format(len(user.roles) - 1), value=role_string, inline=False)
        embed.set_footer(text='ID: ' + str(user.id))
        return await ctx.send(embed=embed)

    # Backup database to a file
    @cog_ext.cog_slash(name="backupDatabase", guild_ids=cogbase.GUILD_IDS,
                       description="Backup database to a file",
                       permissions=cogbase.PERMISSION_MODS)
    async def backup_database(self, ctx: SlashContext):
        now = datetime.now()
        cmd = f"mysqldump -u {get_settings('DB_U')} " \
              f"--result-file=database_backup/backup-{now.strftime('%m-%d-%Y')}.sql " \
              f"-p{get_settings('DB_P')} server_database"
        os.system(cmd)
        await ctx.send(f"Database backed up", hidden=True)

    # Slow mode
    @cog_ext.cog_slash(name="slowmode", guild_ids=cogbase.GUILD_IDS,
                       description="Enable slowmode on current channel",
                       permissions=cogbase.PERMISSION_MODS)
    async def slowmode(self, ctx, seconds: int = 0):
        if seconds > 120:
            return await ctx.send(":no_entry: Amount can't be over 120 seconds")
        if seconds is 0:
            await ctx.channel.edit(slowmode_delay=seconds)
            a = await ctx.send("Slowmode is off for this channel")
            await a.add_reaction("a:redcard:871861842639716472")
        else:
            if seconds is 1:
                numofsecs = "second"
            else:
                numofsecs = "seconds"
            await ctx.channel.edit(slowmode_delay=seconds)
            confirm = await ctx.send(
                f"{ctx.author.display_name} set the channel slow mode delay to `{seconds}` {numofsecs}\n"
                f"To turn this off use /slowmode")
            await confirm.add_reaction("a:ResidentWitcher:871872130021736519")


def setup(bot: commands.Bot):
    bot.add_cog(CommandsCog(bot))
