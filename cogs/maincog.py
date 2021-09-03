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
import discord
from discord_slash.utils.manage_commands import create_permission
from discord.ext import commands
from discord_slash import cog_ext, SlashContext
from discord_slash.model import SlashCommandPermissionType
import json
from cogs.cogbase import BaseCog
from modules.get_settings import get_settings
from modules.pull_config.pull_config import get_config

guild_ids = get_settings("guild")

MODERATION_IDS = get_settings("MOD_ROLES")
PERMISSIONS_MODS = {
    guild_ids[0]: [
        create_permission(MODERATION_IDS[0], SlashCommandPermissionType.ROLE, True),
        create_permission(MODERATION_IDS[1], SlashCommandPermissionType.ROLE, True)
    ]
}


class MainCog(BaseCog):
    def __init__(self, base):
        super().__init__(base)

    # GENERAL FUNCTIONS
    # Check latency
    @cog_ext.cog_slash(name="ping", guild_ids=guild_ids,
                       description="Test function for checking latency",
                       default_permission=False,
                       permissions=PERMISSIONS_MODS)
    async def _ping(self, ctx: SlashContext):
        await ctx.send(f"Pong! {round(self.bot.latency * 1000)}ms", delete_after=4.0)

    # Clear messages
    @cog_ext.cog_slash(name="clear", guild_ids=guild_ids,
                       description="Function for clearing messages on channel",
                       default_permission=False,
                       permissions=PERMISSIONS_MODS)
    async def _purge(self, ctx: SlashContext, number):
        num_messages = int(number)
        await ctx.channel.purge(limit=num_messages)
        await ctx.send(f"Cleared {num_messages} messages!", delete_after=4.0)

    # Disconnect Bot
    @cog_ext.cog_slash(name="exit", guild_ids=guild_ids,
                       description="Turn off the bot",
                       default_permission=False,
                       permissions=PERMISSIONS_MODS)
    async def _exit(self, ctx: SlashContext):
        await ctx.send(f"Closing Bot", delete_after=1.0)
        print("[INFO]: Exiting Bot")
        await asyncio.sleep(2)
        await self.bot.close()

    # WARN FUNCTIONS
    # Warn user
    @cog_ext.cog_slash(name="warn", guild_ids=guild_ids,
                       description="Function for warning users",
                       default_permission=False,
                       permissions=PERMISSIONS_MODS)
    async def _warn(self, ctx: SlashContext, user: discord.User, reason: str):
        with open('./json_files/warns.json', encoding='utf-8') as f:
            try:
                report = json.load(f)
            except ValueError:
                report = {'users': []}

        warned = False
        reason = ''.join(reason)
        for current_user in report['users']:
            if current_user['id'] == user.id:
                current_user['reasons'].append(reason)
                warned = True
                await ctx.send(f"{user.mention} was warned for:\n\"{reason}\"\n"
                               f"Number of warns: {len(current_user['reasons'])}")
                break
        if not warned:
            report['users'].append({
                'id': user.id,
                'name': user.display_name,
                'reasons': [reason, ]
            })
            # TODO: Improve 'reasons' format(or not?)
            await ctx.send(f"{user.mention} was warned for:\n\"{reason}\"\n")

        with open('./json_files/warns.json', 'w+') as f:
            json.dump(report, f, indent=4)

    # Get list of user's warns
    # Does not work if used too much
    @cog_ext.cog_slash(name="warns", guild_ids=guild_ids,
                       description="Function for warning users",
                       default_permission=False,
                       permissions=PERMISSIONS_MODS)
    async def _warns(self, ctx: SlashContext, user: discord.User):
        with open('./json_files/warns.json', encoding='utf-8') as f:
            try:
                report = json.load(f)
            except ValueError:
                report = {'users': []}

        for current_user in report['users']:
            if user.id == current_user['id']:
                message = f"{user.name} has been warned {len(current_user['reasons'])} times\nReasons:\n " \
                          f"{','.join(current_user['reasons'])}"
                # TODO: Improve 'reasons' message formatting
                await ctx.author.send(message)
                await ctx.send(f"{user.name} warns has been sent to DM", hidden=True)
                break
        else:
            await ctx.author.send(f"{user.name} has never been warned")
            await ctx.send(f"{user.name} warns has been sent to DM", hidden=True)

    @cog_ext.cog_slash(name="removeWarns", guild_ids=guild_ids,
                       description="Function for managing user's warns",
                       default_permission=False,
                       permissions=PERMISSIONS_MODS)
    async def remove_warns(self, ctx: SlashContext, user: discord.User, nr_to_delete: int):
        if nr_to_delete < 0:
            await ctx.send(f"Really? Negative nr?", hidden=True)
            return

        with open('./json_files/warns.json', encoding='utf-8') as f:
            try:
                report = json.load(f)
            except ValueError:
                report = {'users': []}

        warns_removed = False
        for current_user in report['users']:
            if current_user['id'] == user.id:
                current_user['reasons'] = current_user['reasons'][:-nr_to_delete or None]
                await ctx.send(f"{user.display_name}'s last {nr_to_delete} warns were deleted", delete_after=5.0)
                warns_removed = True
                break
        if not warns_removed:
            await ctx.send(f"{user.display_name} did not have any warns", delete_after=5.0)

        with open('./json_files/warns.json', 'w+') as f:
            json.dump(report, f, indent=4)

    @cog_ext.cog_slash(name="updateTotMem", guild_ids=guild_ids,
                       description="Update total number of members",
                       default_permission=False,
                       permissions=PERMISSIONS_MODS)
    async def update_member_count_command(self, ctx: SlashContext):
        await self.bot.update_member_count(ctx)
        await ctx.send(f"Total Members count updated", hidden=True)

    @cog_ext.cog_slash(name="updateCommons", guild_ids=guild_ids,
                       description="Update common channel name",
                       default_permission=False,
                       permissions=PERMISSIONS_MODS)
    async def update_commons_ch(self, ctx: SlashContext, common: str):
        new_name = f"common-{common}"
        channel = self.bot.get_channel(self.bot.CH_COMMON)
        await discord.TextChannel.edit(channel, name=new_name)
        await ctx.send(f"Common channel updated", hidden=True)

    # Pull config.json from Google Sheets
    @cog_ext.cog_slash(name="pullConfig", guild_ids=guild_ids,
                       description="Pull config from google sheets",
                       default_permission=False,
                       permissions={
                           guild_ids[0]: [
                               create_permission(get_settings("ADMIN"), SlashCommandPermissionType.USER, True)
                           ]
                       })
    async def pull_config(self, ctx: SlashContext):
        get_config()
        with open('json_files/config.json', 'r', encoding='utf-8-sig') as fp:
            self.bot.config = json.load(fp)
            self.bot.reload_extension("cogs.rolecog")
        await ctx.send(f"Config.json updated", hidden=True)

    # OTHER

    # Did BonJowi killed N-Word? (unstable)
    # Apparently you can not use this command more often than every x minutes
    @cog_ext.cog_slash(name="nword", guild_ids=guild_ids,
                       description="Change N-Word channel name",
                       permissions=PERMISSIONS_MODS)
    async def rename_nword_channel(self, ctx, status: str):
        new_status = status
        channel = self.bot.get_channel(self.bot.CH_NIGHTMARE_KILLED)
        if new_status in channel.name:
            await ctx.send(f"{channel.name} has been changed", hidden=True)
            return
        else:
            await discord.VoiceChannel.edit(channel, name=f"N-Word spotted: {new_status}")
            await ctx.send(f"{channel.name} channel name has been changed", hidden=True)

    # async def rename_nword_channel(self, ctx):
    #     channel = self.bot.get_channel(CH_NWORD_KILLED)
    #     if "YES" in channel.name:
    #         new_status = "NO"
    #     elif "NO" in channel.name:
    #         new_status = "YES"
    #     else:
    #         return
    #     # new_status = "YES" if "NO" in channel.name else "NO" if "YES" in channel.name else ""
    #     print(type(new_status))
    #     print(new_status)
    #     await discord.VoiceChannel.edit(channel, name=f"N-Word killed: {new_status}")
    #     await ctx.send(f"{channel.name} channel name has been changed", hidden=True)

    # Disconnect Bot using "!" prefix (For safety reasons in case Slash commands are not working
    @commands.command(name="ex", pass_context=True, aliases=["e", "exit"])
    async def exit_bot(self, ctx):
        print("[INFO]: Exiting Bot")
        await ctx.send(f"Closing Bot")
        await self.bot.close()


def setup(bot: commands.Bot):
    bot.add_cog(MainCog(bot))
