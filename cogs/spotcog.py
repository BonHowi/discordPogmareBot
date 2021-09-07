"""
Cog with role related commands available in the Bot.

Current commands:
/remove_spot

"""
import json
import discord
import cogs.cogbase as cogbase
from discord.utils import get
from discord.ext import commands
from discord_slash import SlashContext, cog_ext


class SpotCog(cogbase.BaseCog):
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
        if ctx.channel.id == self.bot.ch_common:
            if ctx.content[0] in cords_beginning:
                await self.count_spot(ctx, 4)
            else:
                await ctx.delete()

        elif ctx.channel.category.id == self.bot.cat_spotting:
            if ctx.content.startswith(prefix):
                spotted_monster = await self.get_monster(ctx, ctx.content.replace(prefix, ""))
                if spotted_monster:
                    role = get(ctx.guild.roles, name=spotted_monster["name"])
                    await ctx.delete()
                    await ctx.channel.send(f"{role.mention}")
                    await self.count_spot(ctx, spotted_monster["type"])
            elif ctx.content[0] in cords_beginning:  # I think this should be 1st in checking if
                return

    @staticmethod
    async def count_spot(ctx: SlashContext, monster_type: int):
        """

        :param ctx:
        :type ctx:
        :param monster_type:
        :type monster_type:
        :return:
        :rtype:
        """
        with open("./server_files/monster_spots.json", encoding="utf-8") as f:
            try:
                spots = json.load(f)
            except ValueError:
                spots = {"users": []}
                await ctx.channel.send("monster_spots.json created", delete_after=1)

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

        with open("./server_files/monster_spots.json", "w+") as f:
            json.dump(spots, f, indent=4)

    @cog_ext.cog_slash(name="setMemberSpotsCounter", guild_ids=cogbase.GUILD_IDS,
                       description="Function for managing user's warns",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_MODS)
    async def set_spot_count(self, ctx: SlashContext, user: discord.User, monster_type: int, number: int):
        """

        :param ctx:
        :type ctx:
        :param user:
        :type user:
        :param monster_type:
        :type monster_type:
        :param number:
        :type number:
        :return:
        :rtype:
        """
        if number < 0:
            await ctx.channel.send("Nr of spots can't be lower than 0", delete_after=2)
            return
        with open("./server_files/monster_spots.json", encoding="utf-8") as f:
            try:
                spots = json.load(f)
            except ValueError:
                spots = {"users": []}
                await ctx.channel.send("monster_spots.json created", delete_after=1)

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

        with open("./server_files/monster_spots.json", "w+") as f:
            json.dump(spots, f, indent=4)
        await ctx.channel.send(f"Nr of spots changed for {user.display_name}", delete_after=4)


def setup(bot: commands.Bot):
    bot.add_cog(SpotCog(bot))
