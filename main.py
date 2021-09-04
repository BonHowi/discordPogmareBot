import os
import logging
import json
from discord_slash.model import SlashCommandPermissionType
from discord_slash.utils.manage_commands import create_permission
import discord
from discord.ext import commands
from discord_slash import SlashCommand
from modules.get_settings import get_settings

# Create logger
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# Set bot privileges
intents = discord.Intents.all()

# Load environment variables
# from dotenv import load_dotenv
# load_dotenv()
# TOKEN = os.getenv("DC_TOKEN")

# Must be converted to int as python recognizes as str otherwise
# GUILD = int(os.getenv("DC_MAIN_GUILD"))
# CH_MEMBER_COUNT = int(os.getenv("DC_CH_MEMBERS"))
# MODERATION_ROLES_IDS = os.getenv("DC_MODERATION_ROLES")
# CH_LOGS = int(os.getenv("DC_CH_LOGS"))
# added a test command


class MyBot(commands.Bot):

    # Init
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        print("[INFO]: Init Bot")
        self.GUILD = get_settings("guild")
        self.ADMIN = get_settings("ADMIN")
        self.MOD_ROLES = get_settings("MOD_ROLES")
        self.PERMISSIONS_MODS = {
            self.GUILD[0]: [
                create_permission(self.MOD_ROLES[0], SlashCommandPermissionType.ROLE, True),
                create_permission(self.MOD_ROLES[1], SlashCommandPermissionType.ROLE, True)
            ]
        }
        self.CH_ROLE_REQUEST = get_settings("CH_ROLE_REQUEST")
        self.CH_TOTAL_MEMBERS = get_settings("CH_TOTAL_MEMBERS")
        self.CH_NIGHTMARE_KILLED = get_settings("CH_NIGHTMARE_KILLED")
        self.CH_COMMON = get_settings("CH_COMMON")
        self.CH_LOGS = get_settings("CH_LOGS")
        self.CH_DISCUSSION_EN = get_settings("CH_DISCUSSION_EN")
        self.CAT_SPOTTING = get_settings("CAT_SPOTTING")

        with open('json_files/config.json', 'r', encoding='utf-8-sig') as fp:
            # fp.encoding = 'utf-8-sig'
            self.config = json.load(fp)

    # On Client Start
    async def on_ready(self):
        await MyBot.change_presence(self, activity=discord.Activity(type=discord.ActivityType.playing,
                                                                    name="The Witcher: Monster Slayer"))
        print("[INFO]: Bot now online")

    async def update_member_count(self, ctx):
        true_member_count = len([m for m in ctx.guild.members if not m.bot])
        new_name = f"Total members: {true_member_count}"
        channel = self.get_channel(self.CH_TOTAL_MEMBERS)
        await discord.VoiceChannel.edit(channel, name=new_name)

    # On member join
    async def on_member_join(self, ctx):
        await self.update_member_count(ctx)
        print(f"Someone joined")

    # Manage on message actions
    async def on_message(self, ctx):
        if ctx.author.id == self.user.id:
            return

        # If not on role-request channel
        if ctx.content.startswith("!") and ctx.channel.id != self.CH_ROLE_REQUEST:
            await ctx.channel.send(
                fr"{ctx.author.mention} Please use / instead of ! to use commands on the server!",
                delete_after=5.0)
            await ctx.delete()


def main():
    pogmare = MyBot()
    print(f"[INFO]: Rate limited: {pogmare.is_ws_ratelimited()}")

    # Allow slash commands
    slash = SlashCommand(pogmare, sync_commands=True, sync_on_cog_reload=True)

    # Load cogs
    for cog in os.listdir("./cogs"):
        if cog.endswith("cog.py"):
            try:
                cog = f"cogs.{cog.replace('.py', '')}"
                pogmare.load_extension(cog)
            except Exception as e:
                print(f"{cog} Could not be loaded")
                raise e

    pogmare.run(get_settings("token"))


if __name__ == "__main__":
    main()
