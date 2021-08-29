from discord_slash.utils.manage_commands import create_permission
from dotenv import load_dotenv
import os
from discord.ext import commands
from discord_slash import cog_ext, SlashContext, ComponentContext
from discord_slash.utils.manage_components import create_button, create_actionrow, wait_for_component
from discord_slash.model import ButtonStyle, SlashCommandPermissionType

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DC_TOKEN")

# Must be converted to int as python recognizes as str otherwise
GUILD = int(os.getenv("DC_MAIN_GUILD"))
CH_MEMBER_COUNT = int(os.getenv("DC_CH_MEMBERS"))
MODERATION_IDS = list(os.getenv("DC_MODERATION_ROLES").split(","))
PERMISSIONS = {
    GUILD: [
        create_permission(MODERATION_IDS[0], SlashCommandPermissionType.ROLE, True),
        create_permission(MODERATION_IDS[1], SlashCommandPermissionType.ROLE, True)
    ]
}


class MainCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("[INFO]: Init MainCog")

    # Check latency
    @cog_ext.cog_slash(name="ping", guild_ids=[GUILD],
                       description="Test function for checking latency",
                       default_permission=False,
                       permissions=PERMISSIONS)
    async def _ping(self, ctx: SlashContext):
        await ctx.send(f"Pong! {round(self.bot.latency * 1000)}ms")

    # Clear messages
    @cog_ext.cog_slash(name="clear", guild_ids=[GUILD],
                       description="Function for clearing messages on channel",
                       default_permission=False,
                       permissions=PERMISSIONS)
    async def _clear(self, ctx: SlashContext, num_messages):
        num_messages = int(num_messages)
        await ctx.channel.purge(limit=num_messages)
        await ctx.send(f"Cleared {num_messages} messages!", delete_after=2.0)

    # Disconnect Bot
    @cog_ext.cog_slash(name="exit", guild_ids=[GUILD],
                       description="Turn off the bot")
    async def _exit(self, ctx: SlashContext):
        await ctx.send(f"Closing Bot")
        print("[INFO]: Exiting Bot")
        await self.bot.close()

    # Disconnect Bot using "!" prefix (For safety reasons in case Slash commands are not working
    @commands.command(name="ex", pass_context=True, aliases=["e"])
    async def exit_bot(self, ctx):
        print("[INFO]: Exiting Bot")
        await ctx.send(f"Closing Bot")
        await self.bot.close()

    @commands.Cog.listener()
    async def on_message(self, message):
        # Don't respond to ourselves
        if message.author.bot:
            return

        if message.content.lower() == "xD":
            print("lol")


def setup(bot: commands.Bot):
    bot.add_cog(MainCog(bot))
