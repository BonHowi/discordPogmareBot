from discord.ext import commands


class BaseCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print(f"[INFO]: Init {self.__class__.__name__}")
