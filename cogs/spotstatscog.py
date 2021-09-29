import discord
from cogs.databasecog import DatabaseCog
from discord.ext import commands, tasks
from discord.utils import get
from cogs import cogbase
from discord_slash import cog_ext


class SpotStatsCog(cogbase.BaseCog):
    def __init__(self, base):
        super().__init__(base)
        self.hex_to_int = "%02x%02x%02x"
        self.lege_total = 0
        self.rare_total = 0
        self.common_total = 0
        self.update_spot_stats_loop.start()

    @cog_ext.cog_slash(name="updatedbwitholdstats", guild_ids=cogbase.GUILD_IDS,
                       description=" ",
                       default_permission=True,
                       permissions=cogbase.PERMISSION_MODS
                       )
    async def get_old_stats(self, ctx):
        await ctx.send("Generating spots stats", delete_after=5)
        guild = self.bot.get_guild(self.bot.guild[0])
        channel = self.bot.get_channel(self.bot.ch_logs)
        async for message in channel.history(limit=None, oldest_first=True):
            for member in guild.members:
                if message.content.startswith("[PingLog]") and str(member.id) in message.content:
                    for monster in self.bot.config["commands"]:
                        if monster["name"] in message.content:
                            monster_type = "legendary" if monster["type"] == 1 else "rare"
                            DatabaseCog.db_count_monster_spot(member.id, monster_type, monster["name"])
                            break
        self.create_log_msg("Finished updating database")

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

    def get_monster_name(self, role, channel_type):
        monster_found = None
        for monster in self.bot.config["commands"]:
            if monster["name"].lower() == role.name.lower() or role.name.lower() in monster["triggers"]:
                monster_found = monster
                break
        if monster_found["type"] == channel_type:
            return role.name

    async def create_spots_list(self, channel_type: int):
        spots_df = await DatabaseCog.db_get_total_spots_df(self.bot.user.id, channel_type)
        spots_df = spots_df.to_dict(orient='records')
        spots_df = spots_df[0]
        del spots_df['member_id']
        top_print = []
        total = 0
        for key, value in spots_df.items():
            spotting_stats = [f"{key}:  **{value}**"]
            top_print.append(spotting_stats)
            total += value
        return top_print, total

    async def update_spot_stats(self, channel_id: int, channel_type: int):
        spot_stats_ch = self.bot.get_channel(self.bot.ch_spotting_stats)
        top_print, total = await self.create_spots_list(channel_type)
        top_print = ['\n'.join([elem for elem in sublist]) for sublist in top_print]
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

    @tasks.loop(hours=12)
    async def update_spot_stats_loop(self):
        spot_stats_ch = self.bot.get_channel(self.bot.ch_spotting_stats)
        await spot_stats_ch.purge()
        await self.update_spot_stats(self.bot.ch_legendary_spot, 1)
        await self.update_spot_stats(self.bot.ch_rare_spot, 0)
        self.create_log_msg(f"All spotting stats updated")

    @update_spot_stats_loop.before_loop
    async def before_update_spot_stats_loop(self):
        self.create_log_msg(f"Waiting until Bot is ready")
        await self.bot.wait_until_ready()

    # TODO: code refactoring
    # Member own stats
    @cog_ext.cog_slash(name="mySpottingStats", guild_ids=cogbase.GUILD_IDS,
                       description=" ",
                       default_permission=True,
                       permissions=cogbase.PERMISSION_MODS
                       )
    async def get_spotting_stats(self, ctx):
        await ctx.send("Generating spots stats", delete_after=5)

        # Legendary
        leges_list, leges_total = await self.create_spots_list(1)
        leges_print = ['\n'.join([elem for elem in sublist]) for sublist in leges_list]
        leges_print = "\n".join(leges_print)

        leges_color = int(self.hex_to_int % (163, 140, 21), 16)
        embed_command = discord.Embed(title=f"Legendary", description=leges_print, color=leges_color)
        embed_command.add_field(name="Total", value=f"**{leges_total}**", inline=False)
        if self.lege_total != 0:
            percentage_leges = round(leges_total / self.lege_total * 100, 2)
            embed_command.add_field(name="Server %", value=f"**{percentage_leges}%**", inline=False)
        dt_string = self.bot.get_current_time()
        embed_command.set_footer(text=f"{dt_string}")
        await ctx.author.send(embed=embed_command)

        # Rare
        rares_list, rares_total = await self.create_spots_list(0)
        rares_print = ['\n'.join([elem for elem in sublist]) for sublist in rares_list]
        rares_print = "\n".join(rares_print)

        rares_color = int(self.hex_to_int % (17, 93, 178), 16)
        embed_command = discord.Embed(title=f"Rare", description=rares_print, color=rares_color)
        embed_command.add_field(name="Total", value=f"**{rares_total}**", inline=False)
        if self.rare_total != 0:
            percentage_rares = round(rares_total / self.rare_total * 100, 2)
            embed_command.add_field(name="Server %", value=f"**{percentage_rares}%**", inline=False)
        dt_string = self.bot.get_current_time()
        embed_command.set_footer(text=f"{dt_string}")
        await ctx.author.send(embed=embed_command)

        # Common
        common_ch = self.bot.get_channel(self.bot.ch_common)
        common_total = 0
        async for message in common_ch.history(limit=None, oldest_first=True):
            self.common_total += 1
            if ctx.author == message.author:
                common_total += 1
        embed_command = discord.Embed(title=f"Common")
        embed_command.add_field(name="Total", value=f"**{common_total}**", inline=False)
        if self.common_total != 0:
            percentage_common = round(common_total / self.common_total * 100, 2)
            embed_command.add_field(name="Server %", value=f"**{percentage_common}%**", inline=False)
        dt_string = self.bot.get_current_time()
        embed_command.set_footer(text=f"{dt_string}")
        await ctx.author.send(embed=embed_command)
        self.create_log_msg(f"Spotting stats created for {ctx.author}")


def setup(bot: commands.Bot):
    bot.add_cog(SpotStatsCog(bot))
