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
PERMISSION_ADMINS = {
    GUILD_IDS[0]: [
        create_permission(get_settings("ADMIN"), SlashCommandPermissionType.USER, True)
    ]
}


# noinspection PyTypeChecker
class BaseCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print(f"[{self.__class__.__name__}]: Init")

    def get_bot(self):
        return self.bot

    # Find monster in config
    def get_monster(self, ctx, name: str):
        name = name.lower()
        monster_found = []

        for monster in self.bot.config["commands"]:
            if monster["name"].lower() == name or name in monster["triggers"]:
                monster_found = monster

        if not monster_found:
            print(f"[{self.__class__.__name__}]: Monster not found ({ctx.author}: {name})")
            return

        monster_found["role"] = discord.utils.get(ctx.guild.roles, name=monster_found["name"])
        if not monster_found["role"]:
            print(f"[{self.__class__.__name__}]: Failed to fetch roleID for monster {monster_found['name']}")
            return

        else:
            monster_found["role"] = monster_found["role"].id
        return monster_found
