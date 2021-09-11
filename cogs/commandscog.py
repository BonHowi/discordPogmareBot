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
import discord
from discord.utils import get

import cogs.cogbase as cogbase
from discord.ext import commands
from discord_slash import cog_ext, SlashContext
from cogs.databasecog import DatabaseCog
from modules.pull_config.pull_config import get_config


class CommandsCog(cogbase.BaseCog):
    def __init__(self, base):
        super().__init__(base)

    # GENERAL FUNCTIONS
    # Check latency
    @cog_ext.cog_slash(name="ping", guild_ids=cogbase.GUILD_IDS,
                       description="Test function for checking latency",
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
        print(f"[{self.__class__.__name__}]: Exiting Bot")
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
        await ctx.send(f"{ctx.author.mention} mute is over", delete_after=10)

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
    async def update_commons_ch(self, ctx: SlashContext):
        with open('./server_files/commons.txt') as f:
            try:
                commons = f.read().splitlines()
            except ValueError:
                print(ValueError)

        new_name = f"common {commons[0]}"
        common_ch = self.bot.get_channel(self.bot.ch_common)
        await discord.TextChannel.edit(common_ch, name=new_name)
        print(f"[{self.__class__.__name__}]: Common channel name updated: {commons[0]}")

        admin_posting = self.bot.get_channel(self.bot.ch_admin_posting)
        await admin_posting.send(f"Common changed: {commons[0]}")
        await ctx.send(f"Common changed: {commons[0]}", hidden=True)

        commons.append(commons.pop(commons.index(commons[0])))
        with open('./server_files/commons.txt', 'w') as f:
            for item in commons:
                f.write("%s\n" % item)

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
            await discord.VoiceChannel.edit(channel, name=f"N-Word spotted: {new_status}")
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
            print(f"[{self.__class__.__name__}]: Finished data pull")
        await ctx.send(f"Config.json updated", hidden=True)

    # Create roles if pull_config gets non existent roles
    async def create_roles(self, ctx: SlashContext, common: bool):
        milestones = "common_milestones" if common else "total_milestones"
        for mon_type in self.bot.config[milestones][0]:
            if get(ctx.guild.roles, name=mon_type):
                continue
            else:
                await ctx.guild.create_role(name=mon_type)
                print(f"[{self.__class__.__name__}]: {mon_type} role created")

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
        try:
            self.bot.load_extension(f"{module}")
            await ctx.send(f'[{module}] loaded', hidden=True)
            print(f'[{self.__class__.__name__}]: {module} loaded')
        except commands.ExtensionAlreadyLoaded:
            self.bot.unload_extension(module)
            self.bot.load_extension(module)
            await ctx.send(f'[{module}] reloaded', hidden=True)
            print(f'[{self.__class__.__name__}]: {module} reloaded')
        except commands.ExtensionNotFound:
            await ctx.send(f'[{module}] not found', hidden=True)
            print(f'[{self.__class__.__name__}]: {module} not found')

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


def setup(bot: commands.Bot):
    bot.add_cog(CommandsCog(bot))
