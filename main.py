import json
import logging
import os
from datetime import datetime
import discord
from discord.ext import commands, tasks
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

    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

        dt_string = self.get_current_time()
        print(f"({dt_string})\t[{self.__class__.__name__}]: Init")
        print(f"({dt_string})\t[{self.__class__.__name__}]: Rate limited: {self.is_ws_ratelimited()}")

        self.guild = get_settings("guild")
        self.ch_admin_posting = get_settings("CH_ADMIN_POSTING")
        self.ch_role_request = get_settings("CH_ROLE_REQUEST")
        self.ch_total_members = get_settings("CH_TOTAL_MEMBERS")
        self.ch_nightmare_killed = get_settings("CH_NIGHTMARE_KILLED")
        self.ch_leaderboards = get_settings("CH_LEADERBOARDS")
        self.ch_leaderboards_common = get_settings("CH_LEADERBOARDS_COMMON")
        self.ch_common = get_settings("CH_COMMON")
        self.ch_logs = get_settings("CH_LOGS")
        self.ch_discussion_en = get_settings("CH_DISCUSSION_EN")
        self.cat_spotting = get_settings("CAT_SPOTTING")
        self.update_ch_commons_loop.start()

        with open('server_files/config.json', 'r', encoding='utf-8-sig') as fp:
            self.config = json.load(fp)

    # On bot ready
    async def on_ready(self):
        await MyBot.change_presence(self, activity=discord.Activity(type=discord.ActivityType.playing,
                                                                    name="The Witcher: Monster Slayer"))
        dt_string = self.get_current_time()
        print(f"({dt_string})\t[{self.__class__.__name__}]: Bot ready")

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
        # If bot is the message author
        if ctx.author.id == self.user.id:
            return

        # If there is a message with "!" prefix
        if ctx.content.startswith("!") and ctx.channel.id != self.ch_role_request:
            await ctx.channel.send(
                fr"{ctx.author.mention} Please use / instead of ! to use commands on the server!",
                delete_after=5.0)
            await ctx.delete()

    # Loop tasks
    # Update common spotting channel name
    async def update_ch_commons(self):
        with open('./server_files/commons.txt') as f:
            try:
                commons = f.read().splitlines()
            except ValueError:
                print(ValueError)

        new_name = f"common {commons[0]}"
        common_ch = self.get_channel(self.ch_common)
        await discord.TextChannel.edit(common_ch, name=new_name)
        dt_string = self.get_current_time()
        print(f"({dt_string})\t[{self.__class__.__name__}]: Common channel name updated: {commons[0]}")

        admin_posting = self.get_channel(self.ch_admin_posting)
        await admin_posting.send(f"Common changed: {commons[0]}")

        commons.append(commons.pop(commons.index(commons[0])))
        with open('./server_files/commons.txt', 'w') as f:
            for item in commons:
                f.write("%s\n" % item)

    # Update commons channel name every day at 12:00
    @tasks.loop(minutes=60.0)
    async def update_ch_commons_loop(self):
        if datetime.now().hour == 12:
            await self.update_ch_commons()

    @update_ch_commons_loop.before_loop
    async def before_update_ch_commons(self):
        await self.wait_until_ready()

    # Disconnect Bot using "!" prefix (For safety reasons in case Slash commands are not working
    @commands.command(name="ex", pass_context=True, aliases=["e", "exit"])
    async def exit_bot(self, ctx):
        await ctx.send(f"Closing Bot", delete_after=1.0)
        dt_string = self.get_current_time()
        print(f"({dt_string})\t[{self.__class__.__name__}]: Exiting Bot")
        await self.close()

    @staticmethod
    def get_current_time():
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        return dt_string


def main():
    pogmare = MyBot()

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
