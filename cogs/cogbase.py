import atexit

import discord
from discord.ext import commands
from discord_slash.model import SlashCommandPermissionType
from discord_slash.utils.manage_commands import create_permission
from modules.get_settings import get_settings

GUILD_IDS = get_settings("guild")
MODERATION_IDS = get_settings("MOD_ROLES")
PERMISSION_MODS = {
    GUILD_IDS[0]: [
        create_permission(MODERATION_IDS[0], SlashCommandPermissionType.ROLE, True),
        create_permission(MODERATION_IDS[1], SlashCommandPermissionType.ROLE, True)
    ]
}
PERMISSION_BONJOWI = {
    GUILD_IDS[0]: [
        create_permission(get_settings("ADMIN"), SlashCommandPermissionType.USER, True)
    ]
}


class BaseCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print(f"[INFO]: Init {self.__class__.__name__}")

    # Find monster in config
    async def get_monster(self, ctx, name: str):
        """

        :param ctx:
        :type ctx:
        :param name:
        :type name:
        :return:
        :rtype:
        """
        monster = []
        name = name.lower()

        for monsters in self.bot.config["commands"]:
            if monsters["name"].lower() == name:
                monster = monsters
                break
            if name in monsters["triggers"]:
                monster = monsters

        if not monster:
            print("Monster not found")
            await ctx.send("Monster not found", hidden=True)
            return

        monster["role"] = discord.utils.get(ctx.guild.roles, name=monster["name"])
        if not monster["role"]:
            print(f"Failed to fetch roleID for monster {monster['name']}")
            await ctx.send("Role not found", hidden=True)
            return

        else:
            monster["role"] = monster["role"].id
        return monster
