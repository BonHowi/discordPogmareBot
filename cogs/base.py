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
        monster = []
        name = name.lower()

        for monsters in self.bot.config["commands"]:
            if monsters["name"].lower() == name:
                monster = monsters
                pass
            for monster_triggers in monsters["triggers"]:
                if monster_triggers == name:
                    monster = monsters

        if not monster:
            print("Monster not found")
            await ctx.send(f"Monster not found", hidden=True)
            return

        monster["role"] = discord.utils.get(ctx.guild.roles, name=monster["name"])
        if not monster["role"]:
            print(f"Failed to fetch roleID for monster {monster['name']}")
            await ctx.send(f"Role not found", hidden=True)
            return
        else:
            monster["role"] = monster["role"].id
        return monster

    # Count spot
    # TODO: move to spotcog.py
    async def count_spot(self, ctx: SlashContext, monster_type: int):
        with open("./json_files/monster_spots.json", encoding="utf-8") as f:
            try:
                spots = json.load(f)
            except ValueError:
                spots = {"users": []}
                await ctx.channel.send(f"monster_spots.json created", delete_after=1)

        if monster_type == 4:
            for current_user in spots["users"]:
                if current_user["id"] == ctx.author.id:
                    current_user["common_spots"] += 1
                    break
            else:
                spots["users"].append({
                    "id": ctx.author.id,
                    "name": ctx.author.name,
                    "lege_spots": 0,
                    "rare_spots": 0,
                    "total": 0,
                    "common_spots": 1
                })
        else:
            for current_user in spots["users"]:
                if current_user["id"] == ctx.author.id:
                    if monster_type == 0:
                        current_user["rare_spots"] += 1
                    elif monster_type == 1:
                        current_user["lege_spots"] += 1

                    current_user["total"] = current_user["lege_spots"] * 5 + current_user["rare_spots"]
                    break
            else:
                spots["users"].append({
                    "id": ctx.author.id,
                    "name": ctx.author.display_name,
                    "lege_spots": 0,
                    "rare_spots": 0,
                    "total": 0,
                    "common_spots": 0
                })

        with open("./json_files/monster_spots.json", "w+") as f:
            json.dump(spots, f, indent=4)
