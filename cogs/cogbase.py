import json

import discord
from discord.ext import commands
from discord_slash import SlashContext


class BaseCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print(f"[INFO]: Init {self.__class__.__name__}")

    # Find monster in config
    async def get_monster(self, ctx: SlashContext, name: str):
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
            for monster_triggers in monsters["triggers"]:
                if monster_triggers == name:
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
