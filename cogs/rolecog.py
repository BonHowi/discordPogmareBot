"""
Cog with role related commands available in the Bot.

Current commands:
/

"""
import discord
from discord.utils import get
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
CH_ROLE_REQUEST = int(os.getenv("DC_CH_REQUEST"))
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
    async def _role(self, ctx: SlashContext, monster_name: str):
        if ctx.channel.id != CH_ROLE_REQUEST:
            await ctx.send(f"Use <#{CH_ROLE_REQUEST}> to request a role!", hidden=True)
            return
        else:
            monster = await self.bot.get_monster(ctx, monster_name)
            member = ctx.author
            if monster:
                role = get(member.guild.roles, name=monster["name"])
                if role in member.roles:
                    await member.remove_roles(role)
                    await self.bot.say(f"Role removed")
                else:
                    await member.add_roles(role)
                    await self.bot.say(f"Role added")
            else:
                await self.bot.say(f"No role found")

    # discord.errors.Forbidden: 403 Forbidden (error code: 50013): Missing Permissions


def setup(bot: commands.Bot):
    bot.add_cog(RoleCog(bot))
