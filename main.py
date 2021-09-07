import os
import logging
import json
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


class MyBot(commands.Bot):

    # Init
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        print("[INFO]: Init Bot")
        self.guild = get_settings("guild")
        self.ch_role_request = get_settings("CH_ROLE_REQUEST")
        self.ch_total_members = get_settings("CH_TOTAL_MEMBERS")
        self.ch_nightmare_killed = get_settings("CH_NIGHTMARE_KILLED")
        self.ch_common = get_settings("CH_COMMON")
        self.ch_logs = get_settings("CH_LOGS")
        self.ch_discussion_en = get_settings("CH_DISCUSSION_EN")
        self.cat_spotting = get_settings("CAT_SPOTTING")

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
        channel = self.get_channel(self.ch_total_members)
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
        if ctx.content.startswith("!") and ctx.channel.id != self.ch_role_request:
            await ctx.channel.send(
                fr"{ctx.author.mention} Please use / instead of ! to use commands on the server!",
                delete_after=5.0)
            await ctx.delete()


def main():
    pogmare = MyBot()
    print(f"[INFO]: Rate limited: {pogmare.is_ws_ratelimited()}")

    # Allow slash commands
    slash = SlashCommand(pogmare, sync_commands=True, sync_on_cog_reload=False)

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
