from dotenv import load_dotenv
import os
import logging
import discord as dc
from discord.ext import commands
from dislash import slash_command, ActionRow, Button, ButtonStyle

# Create logger
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# Set bot privileges
intents = dc.Intents.all()


# Load environment variables
load_dotenv()
TOKEN = os.getenv('DC_TOKEN')

# Must be converted to int as python recognizes as str otherwise
GUILD = int(os.getenv('DC_MAIN_GUILD'))
CH_MEMBER_COUNT = int(os.getenv('DC_CH_MEMBERS'))


class MyBot(commands.Bot):

    # Init
    def __init__(self, command_prefix='/'):
        super().__init__(command_prefix='!', intents=intents)
        self.message_online = "[INFO]: Bot now online"

    # On Client Start
    async def on_ready(self):
        await MyBot.change_presence(self, activity=dc.Game('Fortnite'))
        print(self.message_online)

    # On member join
    async def on_member_join(self, ctx):
        true_member_count = len([m for m in ctx.guild.members if not m.bot])
        new_name = f'Total members: {true_member_count}'
        channel = self.get_channel(CH_MEMBER_COUNT)
        await dc.VoiceChannel.edit(channel, name=new_name)
        print("JOINED")


def main():
    pogmare = MyBot()
    pogmare.load_extension('cogs.maincog')
    pogmare.run(TOKEN)


if __name__ == '__main__':
    main()
