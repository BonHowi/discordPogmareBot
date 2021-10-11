"""
Cog with role related commands available in the Bot.

Current commands:
/remove_spot

"""
from datetime import datetime
import discord
from discord.ext import commands, tasks
from discord.utils import get
import cogs.cogbase as cogbase
from cogs.databasecog import DatabaseCog

monster_type_dict = {0: "rare", 1: "legendary", 2: "event1", 3: "event2", 4: "common"}

prefix = "/"
cords_beginning = ["-", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]


class SpotCog(cogbase.BaseCog):
    def __init__(self, base):
        super().__init__(base)
        self.peepo_ban_emote: str = ":peepoban:872502800146382898"
        self.spotting_channels: list = [self.bot.ch_legendary_spot, self.bot.ch_rare_spot,
                                        self.bot.ch_legendary_nemeton, self.bot.ch_rare_nemeton]

        self.clear_nemeton_channels_loop.start()

    # Ping monster role
    @commands.Cog.listener()
    async def on_message(self, ctx) -> None:
        if ctx.author.id == self.bot.user.id or isinstance(ctx.channel, discord.channel.DMChannel):
            return
        # If common spotted
        try:
            if ctx.channel.id == self.bot.ch_common:
                await self.handle_spotted_common(ctx)
                return
            elif ctx.channel.category and ctx.channel.category.id == self.bot.cat_spotting:
                await self.handle_spotted_monster(ctx)
                return
            # elif ctx.channel.id != self.bot.ch_role_request:
            #     await self.handle_wrong_ping(ctx)
        except AttributeError:
            pass

        # If monster pinged by member without using bot
        channels_dont_check = [self.bot.ch_role_request, self.bot.ch_leaderboards, self.bot.ch_leaderboards_common,
                               self.bot.ch_leaderboards_event, self.bot.ch_logs, self.bot.ch_spotting_stats]
        if ctx.channel.id not in channels_dont_check:
            await self.handle_wrong_ping(ctx)

    async def handle_wrong_ping(self, ctx):
        guild = self.bot.get_guild(self.bot.guild[0])
        guild_roles: list = [role.id for role in ctx.guild.roles]
        tagged_roles: list = ([role for role in guild_roles if (str(role) in ctx.content)])
        tagged_roles_names = [get(guild.roles, id=role).name for role in tagged_roles]
        for monster in self.bot.config["commands"]:
            if monster["name"] in tagged_roles_names:
                await ctx.channel.send(f"{ctx.author.mention} you have tagged monster without using a bot! "
                                       f"Please read <#876116496651280424> and consider it a warning! "
                                       f"<{self.peepo_ban_emote}>\n"
                                       f"*If you think this message was sent incorrectly please let "
                                       f"<@&872189602281193522> know*")

    @staticmethod
    async def handle_spotted_common(ctx) -> None:
        if ctx.content[0] in cords_beginning:
            await DatabaseCog.db_count_spot(ctx.author.id, "common", "")
            await DatabaseCog.db_save_coords(ctx.content, "common")
        else:
            await ctx.delete()

    async def handle_spotted_monster(self, ctx) -> None:
        if ctx.content.startswith(prefix):
            spotted_monster = self.get_monster(ctx, ctx.content.replace(prefix, ""))
            if spotted_monster:
                monster_type_str = monster_type_dict[spotted_monster["type"]]
                if await self.wrong_channel(ctx, spotted_monster, monster_type_str):
                    return
                role = get(ctx.guild.roles, name=spotted_monster["name"])
                try:
                    await ctx.delete()
                except discord.errors.NotFound:
                    pass
                await ctx.channel.send(f"{role.mention}")
                await DatabaseCog.db_count_spot(ctx.author.id,
                                                monster_type_str, spotted_monster["name"])
                logs_ch = self.bot.get_channel(self.bot.ch_logs)
                await logs_ch.send(f"[PingLog] {ctx.author} ({ctx.author.id})"
                                   f" ping for **{spotted_monster['name']}** on {ctx.channel}")
            else:
                await ctx.delete()
                await ctx.channel.send(
                    f"{ctx.author.mention} monster not found - are you sure that the name is correct?", delete_after=5)
        elif len(ctx.content) > 0 and ctx.content[0] in cords_beginning:
            await DatabaseCog.db_save_coords(ctx.content, ctx.channel.name)
        elif ctx.channel.id in self.spotting_channels:
            try:
                await ctx.add_reaction(f"a{self.peepo_ban_emote}")
            except discord.errors.NotFound:
                pass

    async def wrong_channel(self, ctx, spotted_monster, monster_type_str: str) -> bool:
        if ctx.channel.id in self.spotting_channels:
            if monster_type_str not in ctx.channel.name:
                channel_wild = discord.utils.get(ctx.guild.channels, name=monster_type_str)
                correct_channel_wild = channel_wild.id
                channel_nemeton = discord.utils.get(ctx.guild.channels, name=f"{monster_type_str}-nemeton")
                correct_channel_nemeton = channel_nemeton.id
                await ctx.delete()
                await ctx.channel.send(
                    f"{ctx.author.mention} you posted {spotted_monster['name']} on wrong channel! "
                    f"Use <#{correct_channel_wild}> or <#{correct_channel_nemeton}> instead! <{self.peepo_ban_emote}>",
                    delete_after=8)
                return True
            return False

    async def clear_channel_messages(self, channel) -> None:
        messages = []
        # Can't use datetime.utcnow().date() beacuse discord
        today = datetime.utcnow()
        today = today.replace(hour=0, minute=0, second=0, microsecond=0)
        async for message in channel.history(before=today):
            messages.append(message)
        await channel.delete_messages(messages)
        self.create_log_msg(f"Wiped - {channel.name} history")

    @tasks.loop(hours=3)
    async def clear_nemeton_channels_loop(self) -> None:
        lege_nemeton = self.bot.get_channel(self.bot.ch_legendary_nemeton)
        rare_nemeton = self.bot.get_channel(self.bot.ch_rare_nemeton)
        await self.clear_channel_messages(lege_nemeton)
        await self.clear_channel_messages(rare_nemeton)

    @clear_nemeton_channels_loop.before_loop
    async def before_update_leaderboards_loop(self) -> None:
        self.create_log_msg("Waiting until Bot is ready")
        await self.bot.wait_until_ready()


def setup(bot: commands.Bot) -> None:
    bot.add_cog(SpotCog(bot))
