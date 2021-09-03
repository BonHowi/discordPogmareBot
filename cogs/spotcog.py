"""
Cog with role related commands available in the Bot.

Current commands:
/remove_spot

"""
import json
import discord
from discord.utils import get
from discord.ext import commands
from discord_slash import SlashContext, cog_ext
from discord_slash.model import SlashCommandPermissionType
from discord_slash.utils.manage_commands import create_permission

from cogs.base import BaseCog
from modules.get_settings import get_settings

guild_ids = get_settings("guild")
MODERATION_IDS = get_settings("MOD_ROLES")
PERMISSIONS_MODS = {
    guild_ids[0]: [
        create_permission(MODERATION_IDS[0], SlashCommandPermissionType.ROLE, True),
        create_permission(MODERATION_IDS[1], SlashCommandPermissionType.ROLE, True)
    ]
}


class SpotCog(BaseCog):
    def __init__(self, base):
        super().__init__(base)

    # Ping monster role
    @commands.Cog.listener()
    async def on_message(self, ctx):
        if ctx.author.id == self.bot.user.id:
            return

        prefix = "/"
        cords_beginning = ["-", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]

        # If common spotted
        if ctx.channel.id == self.bot.CH_COMMON:
            if ctx.content[0] in cords_beginning:
                await self.count_spot(ctx, 4)
            else:
                await ctx.delete()

        elif ctx.channel.category.id == self.bot.CAT_SPOTTING:
            if ctx.content.startswith(prefix):
                spotted_monster = await self.get_monster(ctx, ctx.content.replace(prefix, ""))
                if spotted_monster:
                    role = get(ctx.guild.roles, name=spotted_monster["name"])
                    await ctx.delete()
                    await ctx.channel.send(f"{role.mention}")
                    await self.count_spot(ctx, spotted_monster["type"])
            elif ctx.content[0] in cords_beginning:  # I think this should be 1st in checking if
                return

            # # If member sends normal message
            # else:
            #     return
            #     await ctx.channel.send(
            #         f"{ctx.author.mention} Use {self.bot.get_channel(self.bot.CH_DISCUSSION_EN).mention}",
            #         delete_after=5.0)

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
                    else:
                        print("Wrong monster type(?)")

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

    @cog_ext.cog_slash(name="setMemberSpotsCounter", guild_ids=guild_ids,
                       description="Function for managing user's warns",
                       default_permission=False,
                       permissions=PERMISSIONS_MODS)
    async def set_spot_count(self, ctx: SlashContext, user: discord.User, monster_type: int, number: int):
        if number < 0:
            await ctx.channel.send(f"Nr of spots can't be lower than 0", delete_after=2)
            return
        with open("./json_files/monster_spots.json", encoding="utf-8") as f:
            try:
                spots = json.load(f)
            except ValueError:
                spots = {"users": []}
                await ctx.channel.send(f"monster_spots.json created", delete_after=1)

        # TODO: Too many ifs? actually this whole function is written in bad way
        for current_user in spots["users"]:
            if current_user["id"] == user.id:
                if monster_type == 0:
                    current_user["rare_spots"] = number
                elif monster_type == 1:
                    current_user["lege_spots"] = number
                elif monster_type == 2:
                    pass
                elif monster_type == 3:
                    pass
                elif monster_type == 4:
                    current_user["common_spots"] = number
                else:
                    print("Wrong monster type(?)")

                current_user["total"] = current_user["lege_spots"] * 5 + current_user["rare_spots"]
                break

        with open("./json_files/monster_spots.json", "w+") as f:
            json.dump(spots, f, indent=4)
        await ctx.channel.send(f"Nr of spots changed for {user.display_name}", delete_after=4)


def setup(bot: commands.Bot):
    bot.add_cog(SpotCog(bot))