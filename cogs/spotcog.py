"""
Cog with role related commands available in the Bot.

Current commands:
/remove_spot

"""

from discord.ext import commands
from discord.utils import get
import cogs.cogbase as cogbase
from cogs.databasecog import DatabaseCog

monster_type_dict = {0: "rare", 1: "legendary", 2: "event1", 3: "event2", 4: "common"}


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
                await DatabaseCog.db_count_spot(ctx.author.id, monster_type_dict[4])
                await DatabaseCog.db_save_coords(ctx.content, monster_type_dict[4])
            else:
                await ctx.delete()

        elif ctx.channel.category and ctx.channel.category.id == self.bot.cat_spotting:
            if ctx.content.startswith(prefix):
                spotted_monster = await self.get_monster(ctx, ctx.content.replace(prefix, ""))
                if spotted_monster:
                    role = get(ctx.guild.roles, name=spotted_monster["name"])
                    await ctx.delete()
                    await ctx.channel.send(f"{role.mention}")
                    await DatabaseCog.db_count_spot(ctx.author.id,
                                                    monster_type_dict[spotted_monster["type"]])
                else:
                    await ctx.channel.send(
                        f"{ctx.author.mention} monster not found; are you sure that name is correct?", delete_after=5)
            elif ctx.content[0] in cords_beginning:
                await DatabaseCog.db_save_coords(ctx.content, ctx.channel.name)


def setup(bot: commands.Bot):
    bot.add_cog(SpotCog(bot))
