import discord
from discord.ext import commands
from discord.utils import get
from discord_slash.model import SlashCommandPermissionType
from discord_slash.utils.manage_commands import create_permission
from modules.get_settings import get_settings
from datetime import datetime

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
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        print(f"({dt_string})\t[{self.__class__.__name__}]: Init")

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
            dt_string = self.bot.get_current_time()
            print(f"({dt_string})\t[{self.__class__.__name__}]: Monster not found ({ctx.author}: {name})")
            return

        monster_found["role"] = discord.utils.get(ctx.guild.roles, name=monster_found["name"])
        if not monster_found["role"]:
            dt_string = self.bot.get_current_time()
            print(
                f"({dt_string})\t[{self.__class__.__name__}]: Failed to fetch roleID for monster {monster_found['name']}")
            return

        else:
            monster_found["role"] = monster_found["role"].id
        return monster_found

    # Create role if not on server
    async def create_role(self, guild, role):
        if get(guild.roles, name=role):
            return
        else:
            await guild.create_role(name=role)
            dt_string = self.get_current_time()
            print(f"({dt_string})\t[{self.__class__.__name__}]: {role} role created")
