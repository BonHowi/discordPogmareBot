from discord.ext.commands import bot
from dotenv import load_dotenv
import os
from discord.ext import commands
from dislash import slash_command, ActionRow, Button, ButtonStyle, check, SelectMenu, SelectOption

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DC_TOKEN')

# Must be converted to int as python recognizes as str otherwise
GUILD = int(os.getenv('DC_MAIN_GUILD'))
CH_MEMBER_COUNT = int(os.getenv('DC_CH_MEMBERS'))


class MainCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name="ping")
    async def ping(self, ctx: commands.Context):
        """Get the bot's current websocket latency."""
        await ctx.send(f"Pong! {round(self.bot.latency * 1000)}ms") # It's now self.bot.latency

    @slash_command(name='exit', pass_context=True, aliases=['e'])
    async def exit_bot(self, ctx):
        print('[INFO]: Exiting Bot')
        await ctx.send(f'Closing Bot')
        await self.bot.close()

    @commands.command(name='exit', pass_context=True, aliases=['e'])
    async def exit_bot(self, ctx):
        print('[INFO]: Exiting Bot')
        await ctx.send(f'Closing Bot')
        await self.bot.close()

    # # @commands.command(name='test', pass_context=True)
    # @slash_command(description="Says Hello")
    # async def test_command(self, ctx):
    #     await ctx.send(f'Test')

    async def on_message(self, message):
        # don't respond to ourselves
        if message.author == self.user:
            return

        if message.content == 'xxx xxx':
            print('xxx')


def setup(bot):
    bot.add_cog(MainCog(bot))
