"""
Cog with general commands available in the Bot.

Current commands:
/ping -     check Bot latency
/clear -    clear x messages on the channel
/exit -     end Bot's runtime and disconnect from the server
/warn -     warn @user with reason
/warns -    send @user warns to author's DM
/nword -    Changes N-Word killed channel name  -   UNSTABLE
"""
import discord
from discord_slash.utils.manage_commands import create_permission
from dotenv import load_dotenv
import os
from discord.ext import commands
from discord_slash import cog_ext, SlashContext, ComponentContext
from discord_slash.model import SlashCommandPermissionType
import json

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DC_TOKEN")

# Must be converted to int as python recognizes as str otherwise
GUILD = int(os.getenv("DC_MAIN_GUILD"))
CH_MEMBER_COUNT = int(os.getenv("DC_CH_MEMBERS"))
CH_NWORD_KILLED = int(os.getenv("DC_CH_NIGHTMARE_KILL"))
MODERATION_IDS = list(os.getenv("DC_MODERATION_ROLES").split(","))
PERMISSIONS_MODS = {
    GUILD: [
        create_permission(MODERATION_IDS[0], SlashCommandPermissionType.ROLE, True),
        create_permission(MODERATION_IDS[1], SlashCommandPermissionType.ROLE, True)
    ]
}


class MainCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("[INFO]: Init MainCog")

    # GENERAL FUNCTIONS
    # Check latency
    @cog_ext.cog_slash(name="ping", guild_ids=[GUILD],
                       description="Test function for checking latency",
                       default_permission=False,
                       permissions=PERMISSIONS_MODS)
    async def _ping(self, ctx: SlashContext):
        await ctx.send(f"Pong! {round(self.bot.latency * 1000)}ms")

    # Clear messages
    @cog_ext.cog_slash(name="clear", guild_ids=[GUILD],
                       description="Function for clearing messages on channel",
                       default_permission=False,
                       permissions=PERMISSIONS_MODS)
    async def _clear(self, ctx: SlashContext, number):
        num_messages = int(number)
        await ctx.channel.purge(limit=num_messages)
        await ctx.send(f"Cleared {num_messages} messages!", delete_after=2.0)

    # Disconnect Bot
    @cog_ext.cog_slash(name="exit", guild_ids=[GUILD],
                       description="Turn off the bot",
                       default_permission=False,
                       permissions=PERMISSIONS_MODS)
    async def _exit(self, ctx: SlashContext):
        await ctx.send(f"Closing Bot")
        print("[INFO]: Exiting Bot")
        await self.bot.close()

    # WARN FUNCTIONS
    # Warn user
    @cog_ext.cog_slash(name="warn", guild_ids=[GUILD],
                       description="Function for warning users",
                       default_permission=False,
                       permissions=PERMISSIONS_MODS)
    async def _warn(self, ctx, user: discord.User, reason: str):
        with open('./json_files/warns.json', encoding='utf-8') as f:
            try:
                report = json.load(f)
            except ValueError:
                report = {'users': []}

        reason = ' '.join(reason)
        for current_user in report['users']:
            if current_user['id'] == user.id:
                current_user['reasons'].append(reason)
                break
        else:
            report['users'].append({
                'id': user.id,
                'name': user.name,
                'reasons': [reason, ]
            })
            # TODO: Improve 'reasons' format
        with open('./json_files/warns.json', 'w+') as f:
            json.dump(report, f)

        await ctx.send(f"Warned {user.mention} for:\n\"{reason}\"\n"
                       f"Number of warns: {len(current_user['reasons'])}")

    @cog_ext.cog_slash(name="warns", guild_ids=[GUILD],
                       description="Function for getting user's warns",
                       default_permission=False,
                       permissions=PERMISSIONS_MODS)
    async def _warns(self, ctx, user: discord.User):
        with open('./json_files/warns.json', encoding='utf-8') as f:
            try:
                report = json.load(f)
            except ValueError:
                report = {'users': []}

        for current_user in report['users']:
            if user.name == current_user['name']:
                message = f"{user.name} has been warned {len(current_user['reasons'])} times\nReasons:\n " \
                          f"{','.join(current_user['reasons'])}"
                # TODO: Improve 'reasons' message formatting
                await ctx.author.send(message)
                await ctx.send(f"{user.name} warns has been sent to DM", hidden=True)
                break
        else:
            await ctx.author.send(f"{user.name} has never been warned")
            await ctx.send(f"{user.name} warns has been sent to DM", hidden=True)

    # OTHER

    # Did BonJowi killed N-Word? (unstable)
    @cog_ext.cog_slash(name="nword", guild_ids=[GUILD],
                       description="Change N-Word channel name",
                       permissions=PERMISSIONS_MODS)
    async def rename_nword_channel(self, ctx, status: str):
        new_status = status
        channel = self.bot.get_channel(CH_NWORD_KILLED)
        if new_status in channel.name:
            await ctx.send(f"{channel.name} has been changed", hidden=True)
            return
        else:
            await discord.VoiceChannel.edit(channel, name=f"N-Word killed: {new_status}")
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
