import discord
from cogs.databasecog import DatabaseCog
from discord.ext import commands, tasks
from discord.utils import get
from discord_slash import cog_ext, SlashContext

from cogs import cogbase
from cogs.databasecog import DatabaseCog


class SpotStatsCog(cogbase.BaseCog):
    def __init__(self, base):
        super().__init__(base)
        self.hex_to_int = "%02x%02x%02x"
        self.lege_total = 0
        self.rare_total = 0
        self.common_total = 0
        self.update_spot_stats_loop.start()

    async def get_channel_history(self, channel_id, channel_type) -> list:
        guild = self.bot.get_guild(self.bot.guild[0])
        channel = self.bot.get_channel(channel_id)
        roles_list = []
        async for message in channel.history(limit=None, oldest_first=True):
            if message.content.startswith("<@&8"):  # If message is a ping for a role
                seq_type = type(message.content)
                role_id = int(seq_type().join(filter(seq_type.isdigit, message.content)))
                role = get(guild.roles, id=role_id)
                if role:
                    roles_list.append(self.get_monster_name(role, channel_type))
        roles_list = list(filter(None, roles_list))
        return roles_list

    def get_monster_name(self, role, channel_type) -> str:
        monster_found = None
        for monster in self.bot.config["commands"]:
            if monster["name"].lower() == role.name.lower() or role.name.lower() in monster["triggers"]:
                monster_found = monster
                break
        if monster_found["type"] == channel_type:
            return role.name

    @staticmethod
    async def create_spots_list(member_id: int, channel_type: int) -> tuple:
        spots_df = await DatabaseCog.db_get_total_spots_df(member_id, channel_type)
        spots_df = spots_df.to_dict(orient='records')
        spots_df = spots_df[0]
        del spots_df['member_id']
        top_print = []
        total = 0
        for key, value in spots_df.items():
            if key == min(spots_df, key=spots_df.get):
                spotting_stats = [f"*{key}*:  **{value}**"]
            elif key == max(spots_df, key=spots_df.get):
                spotting_stats = [f"**{key}**:  **{value}**"]
            else:
                spotting_stats = [f"{key}:  **{value}**"]
            top_print.append(spotting_stats)
            total += value
        return top_print, total

    async def update_spot_stats(self, channel_id: int, channel_type: int) -> None:
        spot_stats_ch = self.bot.get_channel(self.bot.ch_spotting_stats)
        top_print, total = await self.create_spots_list(self.bot.user.id, channel_type)
        top_print = ['\n'.join(sublist) for sublist in top_print]
        top_print = "\n".join(top_print)

        if channel_type == 1:
            embed_title = "LEGENDARY"
            embed_color = int(self.hex_to_int % (163, 140, 21), 16)
            self.lege_total = total
        elif channel_type == 0:
            embed_title = "RARE"
            embed_color = int(self.hex_to_int % (17, 93, 178), 16)
            self.rare_total = total
        else:
            embed_title = "OTHER"
            embed_color = int(self.hex_to_int % (1, 1, 1), 16)

        embed_command = discord.Embed(title=f"{embed_title}", description=top_print, color=embed_color)
        embed_command.add_field(name="Total", value=f"**{total}**", inline=False)
        dt_string = self.bot.get_current_time()
        embed_command.set_footer(text=f"{dt_string}")
        await spot_stats_ch.send(embed=embed_command)

        channel = self.bot.get_channel(channel_id)
        self.create_log_msg(f"Spotting stats updated - {channel.name}")

    @tasks.loop(hours=1)
    async def update_spot_stats_loop(self) -> None:
        spot_stats_ch = self.bot.get_channel(self.bot.ch_spotting_stats)
        await spot_stats_ch.purge()
        await self.update_spot_stats(self.bot.ch_legendary_spot, 1)
        await self.update_spot_stats(self.bot.ch_rare_spot, 0)

        common_sum = await DatabaseCog.db_get_common_sum()
        embed_color = int(self.hex_to_int % (1, 1, 1), 16)
        spot_stats_ch = self.bot.get_channel(self.bot.ch_spotting_stats)
        embed_command = discord.Embed(title="COMMON", color=embed_color)
        embed_command.add_field(name="Total", value=f"**{common_sum}**", inline=False)
        dt_string = self.bot.get_current_time()
        embed_command.set_footer(text=f"{dt_string}")
        await spot_stats_ch.send(embed=embed_command)
        self.create_log_msg("Spotting stats updated - common")

        self.create_log_msg("All spotting stats updated")

    @update_spot_stats_loop.before_loop
    async def before_update_spot_stats_loop(self) -> None:
        self.create_log_msg("Waiting until Bot is ready")
        await self.bot.wait_until_ready()

    async def get_stats_type(self, ctx: SlashContext, monster_type: int):
        monsters_list, monsters_total = await self.create_spots_list(ctx.author.id, monster_type)
        monsters_print = ['\n'.join(sublist) for sublist in monsters_list]
        monsters_print = "\n".join(monsters_print)

        if monster_type == 1:
            leges_color = int(self.hex_to_int % (163, 140, 21), 16)
            embed_command = discord.Embed(
                title='Legendary', description=monsters_print, color=leges_color
            )

        elif monster_type == 0:
            rares_color = int(self.hex_to_int % (17, 93, 178), 16)
            embed_command = discord.Embed(
                title='Rare', description=monsters_print, color=rares_color
            )

        else:
            embed_command = discord.Embed(title='Other', description=monsters_print)

        embed_command.add_field(name="Total", value=f"**{monsters_total}**", inline=False)
        if self.lege_total != 0:
            percentage_leges = round(monsters_total / self.lege_total * 100, 2)
            embed_command.add_field(name="Server %", value=f"**{percentage_leges}%**", inline=False)
        dt_string = self.bot.get_current_time()
        embed_command.set_footer(text=f"{dt_string}")
        await ctx.author.send(embed=embed_command)

    # Member own stats
    @cog_ext.cog_slash(name="mySpottingStats", guild_ids=cogbase.GUILD_IDS,
                       description="Get detailed spotting stats to your dm",
                       default_permission=True,
                       permissions=cogbase.PERMISSION_MODS
                       )
    async def get_spotting_stats(self, ctx: SlashContext) -> None:
        await ctx.send("Generating spots stats", delete_after=5)
        # Legendary
        await self.get_stats_type(ctx, 1)

        # Rare
        await self.get_stats_type(ctx, 0)

        # Common
        common_ch = self.bot.get_channel(self.bot.ch_common)
        common_total = 0
        # TODO: count common spots in leaderboard
        async for message in common_ch.history(limit=None, oldest_first=True):
            self.common_total += 1
            if ctx.author == message.author:
                common_total += 1
        embed_command = discord.Embed(title="Common")
        embed_command.add_field(name="Total", value=f"**{common_total}**", inline=False)
        if self.common_total != 0:
            percentage_common = round(common_total / self.common_total * 100, 2)
            embed_command.add_field(name="Server %", value=f"**{percentage_common}%**", inline=False)
        dt_string = self.bot.get_current_time()
        embed_command.set_footer(text=f"{dt_string}")
        await ctx.author.send(embed=embed_command)
        self.create_log_msg(f"Spotting stats created for {ctx.author}")


def setup(bot: commands.Bot) -> None:
    bot.add_cog(SpotStatsCog(bot))
