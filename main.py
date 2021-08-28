import discord
from dotenv import load_dotenv
import os
import discord
import logging
from discord.ext import commands

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

load_dotenv()
TOKEN = os.getenv('DC_TOKEN')
GUILD = os.getenv('DC_MAIN_GUILD')
CH_MEMBER_COUNT = os.getenv('DC_CH_MEMBERS')


class MyClient(discord.Client):

    async def on_ready(self):
        print('Logged on as', self.user)
        await MyClient.change_presence(self, activity=discord.Game('Fortnite'))

    async def on_message(self, message):
        word_list = ['cheat', 'cheats', 'hack', 'hacks', 'internal', 'external', 'ddos', 'denial of service']

        # don't respond to ourselves
        if message.author == self.user:
            return

        if message.content in ['/stop', '/close', '/exit', '/e']:
            await message.channel.send('Closing...')
            await MyClient.close(self)

        message_content = message.content
        if len(message_content) > 0:
            for word in word_list:
                if word in message_content:
                    await message.delete()
                    await message.channel.send('Do not say that!')

        message_attachments = message.attachments
        if len(message_attachments) > 0:
            for attachment in message_attachments:
                if attachment.filename.endswith(".dll"):
                    await message.delete()
                    await message.channel.send("No DLL's allowed!")
                elif attachment.filename.endswith('.exe'):
                    await message.delete()
                    await message.channel.send("No EXE's allowed!")
                else:
                    break

    async def emoivb(self, ctx):
        channel = self.get_channel(CH_MEMBER_COUNT)
        true_member_count = len([m for m in ctx.guild.members if not m.bot])
        new_name = f'Total members: {true_member_count}'
        await channel.edit(name=new_name)


def main():
    client = MyClient()
    client.run(TOKEN)


if __name__ == '__main__':
    main()
