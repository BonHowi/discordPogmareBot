"""
Cog with role related commands available in the Bot.

Current commands:
/

"""
import discord
from discord_slash.utils.manage_commands import create_permission
from dotenv import load_dotenv
import os
from discord.ext import commands
from discord_slash import cog_ext, SlashContext
from discord_slash.model import SlashCommandPermissionType
import json
from cogs.base import BaseCog

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


class RoleCog(BaseCog):
    def __init__(self, base):
        super().__init__(base)

    # Clear messages
    @cog_ext.cog_slash(name="role", guild_ids=[GUILD],
                       description="Function for adding monster role to user",
                       default_permission=True)
    async def _role(self, ctx: SlashContext, number):
        pass


def setup(bot: commands.Bot):
    bot.add_cog(RoleCog(bot))
