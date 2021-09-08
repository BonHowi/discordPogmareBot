import cogs.cogbase as cogbase
from discord.ext import commands


class LeaderboardsCog(cogbase.BaseCog):
    def __init__(self, base):
        super().__init__(base)

    async def update_leaderboards(self):
        pass

    async def print_leaderboards(self):
        pass


def setup(bot: commands.Bot):
    bot.add_cog(LeaderboardsCog(bot))
