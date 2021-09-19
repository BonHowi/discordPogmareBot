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

prefix = "/"
cords_beginning = ["-", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]


class SpotCog(cogbase.BaseCog):
    def __init__(self, base):
        super().__init__(base)

    # Ping monster role
    @commands.Cog.listener()
    async def on_message(self, ctx):
        if ctx.author.id == self.bot.user.id:
            return

        # If common spotted
        if ctx.channel.id == self.bot.ch_common:
            await self.handle_spotted_common(ctx)
        elif ctx.channel.category and ctx.channel.category.id == self.bot.cat_spotting:
            await self.handle_spotted_monster(ctx)

    @staticmethod
    async def handle_spotted_common(ctx):
        if ctx.content[0] in cords_beginning:
            await DatabaseCog.db_count_spot(ctx.author.id, monster_type_dict[4])
            await DatabaseCog.db_save_coords(ctx.content, monster_type_dict[4])
        else:
            await ctx.delete()

    # TODO: spaghetti code
    async def handle_spotted_monster(self, ctx):
        if ctx.content.startswith(prefix):
            spotted_monster = self.get_monster(ctx, ctx.content.replace(prefix, ""))
            if spotted_monster:
                role = get(ctx.guild.roles, name=spotted_monster["name"])
                await ctx.delete()
                await ctx.channel.send(f"{role.mention}")
                await DatabaseCog.db_count_spot(ctx.author.id,
                                                monster_type_dict[spotted_monster["type"]])
                logs_ch = self.bot.get_channel(self.bot.ch_logs)
                await logs_ch.send(f"[PingLog] {ctx.author} ({ctx.author.id}) "
                                   f"requested ping for **{spotted_monster['name']}** role")
            else:
                await ctx.delete()
                await ctx.channel.send(
                    f"{ctx.author.mention} monster not found - are you sure that the name is correct?", delete_after=5)
        elif len(ctx.content) > 0 and ctx.content[0] in cords_beginning:
            await DatabaseCog.db_save_coords(ctx.content, ctx.channel.name)
        elif ctx.channel.id != self.bot.ch_werewolf:
            await ctx.add_reaction("a:peepoban:872502800146382898")


def setup(bot: commands.Bot):
    bot.add_cog(SpotCog(bot))
